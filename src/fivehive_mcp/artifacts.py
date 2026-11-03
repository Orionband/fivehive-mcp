import hashlib
import json
import uuid
from pathlib import Path
from .config import Config


def _hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()


def create_artifact(config: Config, snapshot: dict, content_type: str,
                    destination: dict, metadata: dict) -> dict:
    if content_type not in {"chapter", "test", "frq"}:
        raise ValueError("content_type must be chapter, test, or frq")
    artifact_id = str(uuid.uuid4())
    root = config.data_dir / "jobs" / artifact_id
    (root / "assets").mkdir(parents=True)
    content = {"time": int(__import__("time").time() * 1000), "version": "2.30.2", "blocks": []} if content_type == "chapter" else {}
    manifest = {
        "schemaVersion": "fivehive-import/1", "contentType": content_type,
        "destination": destination, "metadata": metadata,
        "source": {"snapshotId": snapshot["snapshotId"], "documentId": snapshot["documentId"],
                    "tabIds": [t["tabId"] for t in snapshot["tabs"]], "snapshotHash": snapshot.get("snapshotHash", snapshot["snapshotId"])},
        "assetBindings": [], "sourceMap": [], "resolutions": []
    }
    (root / "source.json").write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    (root / "content.json").write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return {"artifactId": artifact_id, "hash": _hash({"content": content, "manifest": manifest}), "content": content, "manifest": manifest}


def read_artifact(config: Config, artifact_id: str) -> tuple[Path, dict, dict]:
    root = config.data_dir / "jobs" / artifact_id
    if not root.is_dir():
        raise FileNotFoundError("Unknown artifact")
    return root, json.loads((root / "content.json").read_text(encoding="utf-8")), json.loads((root / "manifest.json").read_text(encoding="utf-8"))


def artifact_hash(content: dict, manifest: dict) -> str:
    return _hash({"content": content, "manifest": manifest})


def update_artifact(config: Config, artifact_id: str, expected_hash: str,
                    content: dict | None = None, manifest: dict | None = None) -> dict:
    root, current_content, current_manifest = read_artifact(config, artifact_id)
    current_hash = artifact_hash(current_content, current_manifest)
    if current_hash != expected_hash:
        raise ValueError("Artifact hash mismatch; reread the artifact before editing")
    next_content = content if content is not None else current_content
    next_manifest = manifest if manifest is not None else current_manifest
    (root / "content.json").write_text(json.dumps(next_content, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps(next_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for stale in ("diagnostics.json", "review.json"):
        (root / stale).unlink(missing_ok=True)
    return {"artifactId": artifact_id, "hash": artifact_hash(next_content, next_manifest), "content": next_content, "manifest": next_manifest}
