from io import BytesIO
from PIL import Image
from fivehive_mcp.assets import prepare_image_upload, MAX_UPLOAD_BYTES


def test_oversize_original_gets_lossless_derivative_without_resizing():
    image = Image.new("RGB", (1600, 1200), "white")
    original = BytesIO()
    image.save(original, format="PNG", compress_level=0)
    assert len(original.getvalue()) > MAX_UPLOAD_BYTES
    derived, mime, dimensions, record = prepare_image_upload(original.getvalue(), "image/png")
    assert len(derived) <= MAX_UPLOAD_BYTES
    assert mime == "image/webp"
    assert dimensions == image.size
    assert record["pixelsPreserved"]
    with Image.open(BytesIO(derived)) as result:
        assert result.convert("RGB").tobytes() == image.tobytes()


def test_small_source_is_uploaded_unchanged():
    original = BytesIO()
    Image.new("RGB", (20, 30)).save(original, format="PNG")
    data, mime, dimensions, record = prepare_image_upload(original.getvalue(), "image/png")
    assert data == original.getvalue()
    assert record is None
