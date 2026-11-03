import json
import hashlib
import secrets
import httpx
import logging
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from .config import load_config
from .source_documents import snapshot_from_document
from .artifacts import artifact_hash, create_artifact, read_artifact, update_artifact
from .validation import validate, validate_artifact
from .website_client import WebsiteClient
from .credentials import delete_secret, load_secret, save_secret
from .resource_files import resource_text
from .assets import MAX_SOURCE_BYTES, prepare_image_upload

config = load_config()
# Temporary image URLs contain access keys and must never enter HTTP logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
mcp = MCPServer("FiveHive Document Porting", instructions="Use the Codex Google Drive plugin for source retrieval, then resolve source coverage, validate JSON, submit a private draft, and publish only after explicit review.")


def artifact_diagnostics(root, content, manifest):
    snapshot = json.loads((root / "source.json").read_text(encoding="utf-8"))
    return validate_artifact(manifest["contentType"], content, manifest, snapshot)


@mcp.resource("fivehive://instructions")
def instructions_resource() -> str:
    return resource_text("workflow.md") + "\n\n" + resource_text("editorial-standards.md")


@mcp.resource("fivehive://editorial-standards")
def editorial_standards_resource() -> str:
    return resource_text("editorial-standards.md")

@mcp.resource("fivehive://porting-reference")
def reference_resource() -> str:
    return resource_text("porting-reference.md")


@mcp.resource("fivehive://schemas/{content_type}")
def schema_resource(content_type: str) -> str:
    if content_type not in {"chapter", "test", "frq", "import-manifest", "diagnostics"}:
        return "Unknown schema."
    return resource_text(f"schemas/{content_type}.schema.json")

@mcp.prompt()
def import_workflow(content_type: str = "chapter") -> str:
    return f"Import a Google Docs document as a FiveHive {content_type}. Retrieve the full instructions, editorial standards and porting reference. Resolve source questions, validate the JSON, compare the saved content with the source, submit a private draft, inspect the website preview, and publish when explicitly authorized. Apply formatting rules through the content; do not change website renderers."

@mcp.tool()
def instructions(content_type: str | None = None) -> dict:
    return {"contentType": content_type, "workflow": instructions_resource(), "editorialProfile": {"headings": "levels 1-3", "math": "validated KaTeX or authoritative reviewed image", "tables": "native where representable; math tables may use KaTeX arrays", "images": "preserve source IDs and upload private derived assets", "unknownSourceData": "blocking diagnostic"}, "requiredFields": {"chapter": ["time", "version", "blocks"], "test": ["time", "questions"], "frq": ["questions", "timeLimitMinutes"]}, "referenceUri": "fivehive://porting-reference", "schemaUris": {"chapter": "fivehive://schemas/chapter", "test": "fivehive://schemas/test", "frq": "fivehive://schemas/frq", "manifest": "fivehive://schemas/import-manifest"}, "schemaVersion": "fivehive-import/1"}

@mcp.tool()
def auth_status() -> dict:
    return {"googleDrive": "external_codex_plugin", "websiteConnected": bool(load_secret(config.profile, "website-token")), "websiteConnectionId": load_secret(config.profile, "website-connection-id")}

@mcp.tool()
def connect_website(label: str = "FiveHive MCP") -> dict:
    verifier = secrets.token_urlsafe(32)
    challenge = hashlib.sha256(verifier.encode()).digest()
    import base64
    code_challenge = base64.urlsafe_b64encode(challenge).rstrip(b"=").decode()
    response = httpx.post(config.website_base_url.rstrip("/") + "/api/mcp/v1/pairings", json={"codeChallenge": code_challenge, "label": label}, timeout=30)
    response.raise_for_status()
    result = response.json()
    (config.data_dir / "pairing.json").write_text(json.dumps({"verifier": verifier, **result}), encoding="utf-8")
    return {"verificationUrl": result["verificationUrl"], "userCode": result["userCode"], "pairingId": result["pairingId"], "next": "After approving the browser page, call exchange_website with the pairingId. The pairing secret stays local."}

@mcp.tool()
def exchange_website(pairing_id: str, pairing_secret: str | None = None) -> dict:
    pairing_path = config.data_dir / "pairing.json"
    stored = json.loads(pairing_path.read_text(encoding="utf-8")) if pairing_path.exists() else {}
    if stored.get("pairingId") != pairing_id: raise ValueError("Unknown local pairing")
    pairing_secret = pairing_secret or stored.get("pairingSecret")
    if not pairing_secret: raise ValueError("The local pairing secret is unavailable")
    response = httpx.post(config.website_base_url.rstrip("/") + "/api/mcp/v1/pairings/exchange", json={"pairingId": pairing_id, "pairingSecret": pairing_secret, "codeVerifier": stored["verifier"]}, timeout=30)
    response.raise_for_status()
    result = response.json()
    save_secret(config.profile, "website-token", result["connectionSecret"])
    save_secret(config.profile, "website-connection-id", result["connectionId"])
    pairing_path.unlink(missing_ok=True)
    return {"connected": True, "connectionId": result["connectionId"], "expiresInSeconds": result["expiresInSeconds"]}

@mcp.tool()
def disconnect(provider: str) -> dict:
    if provider == "website":
        connection_id = load_secret(config.profile, "website-connection-id")
        if connection_id and load_secret(config.profile, "website-token"):
            try: WebsiteClient(config).delete(f"/api/mcp/v1/connections/{connection_id}")
            except httpx.HTTPError: pass
        delete_secret(config.profile, "website-token")
        delete_secret(config.profile, "website-connection-id")
    else: raise ValueError("provider must be website")
    return {"disconnected": provider}

@mcp.tool()
def ingest_source_document(source: dict, source_url: str | None = None, tab_ids: list[str] | None = None, suggestions_view_mode: str = "DEFAULT_FOR_CURRENT_ACCESS", refresh_artifact_id: str | None = None) -> dict:
    """Store a document resource retrieved by an authorized external connector."""
    snapshot = snapshot_from_document(source, source_url, tab_ids, suggestions_view_mode)
    root = config.data_dir / "snapshots"; root.mkdir(parents=True, exist_ok=True)
    (root / f"{snapshot['snapshotId']}.json").write_text(json.dumps(snapshot), encoding="utf-8")
    if refresh_artifact_id:
        job, content, manifest = read_artifact(config, refresh_artifact_id)
        previous = json.loads((job / "source.json").read_text(encoding="utf-8"))
        if previous.get("documentId") != snapshot.get("documentId") or previous.get("normalized") != snapshot.get("normalized") or [a["assetId"] for a in previous.get("assets", [])] != [a["assetId"] for a in snapshot.get("assets", [])]:
            raise ToolError("Source content changed. Create a new artifact and review those changes; image refresh cannot silently replace source content.")
        manifest["source"] = {"snapshotId": snapshot["snapshotId"], "documentId": snapshot["documentId"], "tabIds": [t["tabId"] for t in snapshot["tabs"]], "snapshotHash": snapshot["snapshotHash"]}
        update_artifact(config, refresh_artifact_id, artifact_hash(content, json.loads((job / "manifest.json").read_text(encoding="utf-8"))), manifest=manifest)
        (job / "source.json").write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    return {k: v for k, v in snapshot.items() if k != "raw"}

@mcp.tool()
def list_destinations(subject_slug: str | None = None, unit_id: str | None = None) -> dict:
    result = WebsiteClient(config).get("/api/mcp/v1/destinations")
    if subject_slug:
        result["destinations"] = [item for item in result.get("destinations", []) if item.get("id") == subject_slug]
    if unit_id:
        for item in result.get("destinations", []):
            item["units"] = [unit for unit in item.get("units", []) if unit.get("id") == unit_id]
    return result

@mcp.tool()
def create_json(snapshot_id: str, content_type: str, destination: dict, metadata: dict) -> dict:
    snapshot_path = config.data_dir / "snapshots" / f"{snapshot_id}.json"
    if not snapshot_path.exists(): raise ValueError("Unknown snapshot")
    return create_artifact(config, json.loads(snapshot_path.read_text()), content_type, destination, metadata)

@mcp.tool()
def read_json(artifact_id: str) -> dict:
    _, content, manifest = read_artifact(config, artifact_id)
    return {"artifactId": artifact_id, "hash": artifact_hash(content, manifest), "content": content, "manifest": manifest}


@mcp.tool()
def update_json(artifact_id: str, expected_artifact_hash: str, content: dict | None = None, manifest: dict | None = None) -> dict:
    return update_artifact(config, artifact_id, expected_artifact_hash, content, manifest)

@mcp.tool()
def validate_json(artifact_id: str) -> dict:
    root, content, manifest = read_artifact(config, artifact_id)
    diagnostics = artifact_diagnostics(root, content, manifest)
    (root / "diagnostics.json").write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"artifactId": artifact_id, "diagnostics": diagnostics, "valid": not any(d["severity"] == "blocking" for d in diagnostics)}


@mcp.tool()
def review_json(artifact_id: str, reviewed_hash: str, coverage_resolutions: list[dict] | None = None) -> dict:
    root, content, manifest = read_artifact(config, artifact_id)
    current_hash = artifact_hash(content, manifest)
    if reviewed_hash != current_hash:
        raise ValueError("Review hash does not match the current artifact")
    diagnostics = artifact_diagnostics(root, content, manifest)
    blockers = [d for d in diagnostics if d["severity"] == "blocking"]
    if blockers:
        raise ValueError("Blocking diagnostics must be resolved before review")
    review = {"artifactId": artifact_id, "reviewedArtifactHash": reviewed_hash, "coverageResolutions": coverage_resolutions or [], "reviewedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()}
    (root / "review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    return review

@mcp.tool()
def submit_draft(artifact_id: str, reviewed_hash: str, idempotency_key: str) -> dict:
    root, content, manifest = read_artifact(config, artifact_id)
    current_hash = artifact_hash(content, manifest)
    if reviewed_hash != current_hash:
        raise ValueError("The supplied review hash does not match the current artifact")
    review_path = root / "review.json"
    if not review_path.exists() or json.loads(review_path.read_text(encoding="utf-8")).get("reviewedArtifactHash") != reviewed_hash:
        raise ValueError("Call review_json for this exact artifact before submitting")
    diagnostics = artifact_diagnostics(root, content, manifest)
    if any(d["severity"] == "blocking" for d in diagnostics): raise ValueError("Blocking diagnostics must be resolved")
    if any(not binding.get("websiteAsset", {}).get("url") for binding in manifest.get("assetBindings", [])):
        raise ToolError("Upload every bound source asset before submission, then revalidate and review the changed artifact hash.")
    staging = json.loads((root / "server.json").read_text(encoding="utf-8")) if (root / "server.json").exists() else {}
    return WebsiteClient(config).post("/api/mcp/v1/imports", {"preparedImportId": staging.get("importId"), "artifactId": artifact_id, "contentType": manifest["contentType"], "content": content, "metadata": manifest["metadata"], "destination": manifest["destination"], "assetBindings": manifest.get("assetBindings", []), "sourceMap": manifest.get("sourceMap", []), "resolutions": manifest.get("resolutions", []), "diagnostics": diagnostics, "reviewedArtifactHash": reviewed_hash}, idempotency_key)

@mcp.tool()
def publish_revision(revision_id: str, expected_revision_hash: str) -> dict:
    return WebsiteClient(config).post(f"/api/mcp/v1/revisions/{revision_id}/publish", {"expectedRevisionHash": expected_revision_hash}, f"publish-{revision_id}-{expected_revision_hash}")


@mcp.tool()
def get_document_nodes(snapshot_id: str, cursor: int = 0, limit: int = 100) -> dict:
    snapshot_path = config.data_dir / "snapshots" / f"{snapshot_id}.json"
    if not snapshot_path.exists(): raise ValueError("Unknown snapshot")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    nodes = snapshot.get("normalized", [])
    page = nodes[cursor:cursor + max(1, min(limit, 500))]
    return {"snapshotId": snapshot_id, "nodes": page, "nextCursor": cursor + len(page) if cursor + len(page) < len(nodes) else None, "total": len(nodes)}


@mcp.tool()
def get_source_image(snapshot_id: str, asset_id: str) -> dict:
    snapshot_path = config.data_dir / "snapshots" / f"{snapshot_id}.json"
    if not snapshot_path.exists(): raise ValueError("Unknown snapshot")
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    for asset in snapshot.get("assets", []):
        if asset.get("assetId") == asset_id:
            return asset
    for tab in snapshot.get("tabs", []):
        for index, node in enumerate(tab.get("documentTab", {}).get("body", {}).get("content", [])):
            inline = node.get("paragraph", {}).get("elements", [])
            for element in inline:
                obj = element.get("inlineObjectElement", {})
                object_id = obj.get("inlineObjectId")
                if object_id == asset_id:
                    props = snapshot.get("raw", {}).get("inlineObjects", {}).get(object_id, {}).get("inlineObjectProperties", {})
                    embedded = props.get("embeddedObject", {})
                    return {"assetId": asset_id, "mimeType": embedded.get("mimeType"), "contentUri": embedded.get("imageProperties", {}).get("contentUri"), "tabId": tab.get("tabId"), "nodeId": f"{tab.get('tabId')}:{index}", "description": embedded.get("description")}
    raise ValueError("Image asset not found in snapshot")


@mcp.tool()
def upload_asset(artifact_id: str, asset_id: str, content_uri: str, content_type: str) -> dict:
    if not content_uri.startswith("https://"):
        raise ValueError("Only HTTPS image content URIs returned by Google Docs are accepted")
    root, content, manifest = read_artifact(config, artifact_id)
    snapshot = json.loads((root / "source.json").read_text(encoding="utf-8"))
    if not any(a.get("assetId") == asset_id and a.get("contentUri") == content_uri for a in snapshot.get("assets", [])):
        raise ValueError("Image URI must match this saved source asset")
    binding = next((b for b in manifest.get("assetBindings", []) if b.get("assetId") == asset_id), None)
    if not binding or not binding.get("targetPointer"):
        raise ValueError("Record the image targetPointer in assetBindings before upload")
    staging_path = root / "server.json"
    if staging_path.exists():
        staging = json.loads(staging_path.read_text(encoding="utf-8"))
    else:
        staging = WebsiteClient(config).post("/api/mcp/v1/imports/prepare", {"artifactId": artifact_id, "destination": manifest["destination"]}, f"prepare-{artifact_id}")
        staging_path.write_text(json.dumps(staging), encoding="utf-8")
    from urllib.parse import urlsplit, urljoin
    uri = content_uri
    # Retained source originals allow safe retries after temporary Google URLs
    # expire. This cache is job-owned and only used for this saved source ID.
    local_path = root / "assets" / asset_id
    if local_path.resolve().parent != (root / "assets").resolve():
        raise ValueError("Invalid source asset ID")
    image_bytes = local_path.read_bytes() if local_path.exists() else None
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        for _ in range(4):
            if image_bytes is not None:
                break
            parsed = urlsplit(uri)
            if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443) or not (parsed.hostname == "docs.google.com" or (parsed.hostname or "").endswith(".googleusercontent.com")):
                raise ValueError("Image redirect must stay on approved Google HTTPS image hosts")
            with client.stream("GET", uri) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    uri = urljoin(uri, response.headers.get("location", ""))
                    continue
                if response.status_code != 200:
                    raise ToolError(f"Source image download returned HTTP {response.status_code}. Refresh this source through Google Drive and call ingest_source_document with the same tab_ids and refresh_artifact_id, then retry upload_asset.")
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_SOURCE_BYTES:
                        raise ValueError("Source image exceeds the 50 MiB download bound; ask the user for a smaller original")
                    chunks.append(chunk)
                image_bytes = b"".join(chunks)
                break
    if image_bytes is None:
        raise ValueError("Image exceeded the redirect limit")
    local_path.write_bytes(image_bytes)
    try:
        upload_bytes, upload_type, dimensions, transformation = prepare_image_upload(image_bytes, content_type)
    except ValueError as error:
        raise ToolError(str(error)) from None
    if transformation:
        (root / "assets" / f"{asset_id}.webp").write_bytes(upload_bytes)
    upload = WebsiteClient(config).put_bytes(f"/api/mcp/v1/imports/{staging['importId']}/assets/{asset_id}", upload_bytes, upload_type)
    upload["dimensions"] = list(dimensions)
    if transformation:
        upload["transformation"] = transformation
    url = f"/api/mcp/v1/assets/{asset_id}?revisionId={staging['importId']}"
    parts = binding["targetPointer"].strip("/").split("/")
    target = content
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    target[parts[-1]] = url
    bindings = [binding for binding in manifest.get("assetBindings", []) if binding.get("assetId") != asset_id]
    bindings.append({**binding, "assetId": asset_id, "websiteAsset": {**upload, "url": url}})
    manifest["assetBindings"] = bindings
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "content.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    (root / "diagnostics.json").unlink(missing_ok=True)
    (root / "review.json").unlink(missing_ok=True)
    return {"asset": upload, "artifactId": artifact_id, "hash": artifact_hash(content, manifest)}

if __name__ == "__main__":
    mcp.run()
