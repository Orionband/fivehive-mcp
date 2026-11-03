import pytest
from types import SimpleNamespace
from mcp.server.mcpserver.exceptions import ToolError
from fivehive_mcp.artifacts import create_artifact, read_artifact
from fivehive_mcp.source_documents import snapshot_from_document


def test_image_refresh_rejects_changed_text_and_invalidates_old_review(tmp_path, monkeypatch):
    from fivehive_mcp import server
    config = SimpleNamespace(data_dir=tmp_path)
    monkeypatch.setattr(server, "config", config)
    doc = {"documentId": "doc", "tabs": [{"tabId": "t1", "body": {"content": [{"paragraph": {"elements": [{"textRun": {"content": "Original source"}}]}}]}}]}
    snapshot = snapshot_from_document(doc, tab_ids=["t1"])
    artifact = create_artifact(config, snapshot, "chapter", {"subjectSlug": "biology", "unitId": "u1"}, {"title": "Title"})
    root, _, _ = read_artifact(config, artifact["artifactId"])
    (root / "review.json").write_text('{}')
    server.ingest_source_document(doc, tab_ids=["t1"], refresh_artifact_id=artifact["artifactId"])
    assert not (root / "review.json").exists()
    doc["tabs"][0]["body"]["content"][0]["paragraph"]["elements"][0]["textRun"]["content"] = "Changed source"
    with pytest.raises(ToolError, match="Source content changed"):
        server.ingest_source_document(doc, tab_ids=["t1"], refresh_artifact_id=artifact["artifactId"])
