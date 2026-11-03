from io import BytesIO
from types import SimpleNamespace

import httpx
from PIL import Image

from fivehive_mcp.artifacts import create_artifact, read_artifact


def test_source_image_redirect_stages_upload_and_resolves_pointer(tmp_path, monkeypatch, respx_mock):
    from fivehive_mcp import server
    config = SimpleNamespace(data_dir=tmp_path)
    monkeypatch.setattr(server, "config", config)
    uri = "https://docs.google.com/docs-images-rt/source"
    snapshot = {"snapshotId": "snap", "documentId": "doc", "tabs": [], "assets": [{"assetId": "img1", "contentUri": uri}]}
    artifact = create_artifact(config, snapshot, "chapter", {"subjectSlug": "biology", "unitId": "u1"}, {"title": "Title"})
    server.update_json(artifact["artifactId"], artifact["hash"], content={"time": 1, "version": "2.30.2", "blocks": [{"id": "image", "type": "image", "data": {"file": {"url": "local:image"}}}]}, manifest={**artifact["manifest"], "assetBindings": [{"assetId": "img1", "targetPointer": "/blocks/0/data/file/url"}]})
    buffer = BytesIO()
    Image.new("RGB", (2, 3)).save(buffer, format="PNG")
    respx_mock.get(uri).mock(return_value=httpx.Response(302, headers={"location": "https://lh3.googleusercontent.com/image"}))
    respx_mock.get("https://lh3.googleusercontent.com/image").mock(return_value=httpx.Response(200, content=buffer.getvalue()))
    calls = []

    class Website:
        def __init__(self, config): pass
        def post(self, path, payload, key):
            calls.append(path)
            return {"importId": "server-id"}
        def put_bytes(self, path, data, mime):
            calls.append(path)
            assert data == buffer.getvalue()
            assert mime == "image/png"
            return {"assetId": "img1", "size": len(data)}

    monkeypatch.setattr(server, "WebsiteClient", Website)
    result = server.upload_asset(artifact["artifactId"], "img1", uri, "image/png")
    assert calls == ["/api/mcp/v1/imports/prepare", "/api/mcp/v1/imports/server-id/assets/img1"]
    _, content, manifest = read_artifact(config, artifact["artifactId"])
    assert content["blocks"][0]["data"]["file"]["url"] == "/api/mcp/v1/assets/img1?revisionId=server-id"
    assert manifest["assetBindings"][0]["targetPointer"] == "/blocks/0/data/file/url"
    assert result["asset"]["dimensions"] == [2, 3]
