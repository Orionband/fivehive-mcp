"""Bounded, lossless upload derivatives; source originals remain in the job."""
from io import BytesIO
import hashlib
from PIL import Image

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SOURCE_BYTES = 50 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


def prepare_image_upload(original: bytes, declared_type: str):
    if len(original) > MAX_SOURCE_BYTES:
        raise ValueError("Source image exceeds the 50 MiB download bound. Ask the user for a smaller original.")
    with Image.open(BytesIO(original)) as image:
        actual_type = Image.MIME.get(image.format)
        dimensions = image.size
        if dimensions[0] * dimensions[1] > MAX_IMAGE_PIXELS:
            raise ValueError("Image exceeds the decoded pixel bound. Ask the user how to resize it.")
        image.verify()
    if actual_type != declared_type:
        raise ValueError(f"Declared image MIME does not match decoded image: {actual_type}")
    if len(original) <= MAX_UPLOAD_BYTES:
        return original, actual_type, dimensions, None
    with Image.open(BytesIO(original)) as image:
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("Animated source exceeds 5 MiB. Ask the user for an approved smaller animation; do not discard frames.")
        rgba = image.convert("RGBA")
        output = BytesIO()
        rgba.save(output, format="WEBP", lossless=True, exact=True, method=6)
        derived = output.getvalue()
        with Image.open(BytesIO(derived)) as verified:
            if verified.convert("RGBA").tobytes() != rgba.tobytes():
                raise ValueError("Lossless image conversion did not preserve pixels")
    if len(derived) > MAX_UPLOAD_BYTES:
        raise ValueError("Lossless image still exceeds 5 MiB. Ask the user to approve resizing/compression or provide a smaller image; do not omit it.")
    transformation = {"operation": "lossless-webp", "pixelsPreserved": True,
                      "originalBytes": len(original), "derivedBytes": len(derived),
                      "originalSha256": hashlib.sha256(original).hexdigest(),
                      "derivedSha256": hashlib.sha256(derived).hexdigest()}
    return derived, "image/webp", dimensions, transformation
