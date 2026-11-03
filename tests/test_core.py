from fivehive_mcp.artifacts import artifact_hash
from fivehive_mcp.source_documents import document_id_from_url, snapshot_from_document
from fivehive_mcp.validation import validate


def test_google_document_url_parser():
    assert document_id_from_url("https://docs.google.com/document/d/abc_123/edit") == "abc_123"


def test_external_source_snapshot_preserves_tabs():
    snapshot = snapshot_from_document({
        "documentId": "doc-1",
        "title": "Example",
        "tabs": [{
            "tabProperties": {"tabId": "tab-1", "title": "Article"},
            "documentTab": {"body": {"content": []}},
        }],
    })
    assert snapshot["documentId"] == "doc-1"
    assert snapshot["tabs"][0]["title"] == "Article"


def test_artifact_hash_is_content_and_manifest_bound():
    first = artifact_hash({"blocks": []}, {"contentType": "chapter"})
    second = artifact_hash({"blocks": [{"type": "paragraph"}]}, {"contentType": "chapter"})
    assert first.startswith("sha256:")
    assert first != second


def test_validation_catches_missing_chapter_fields():
    diagnostics = validate("chapter", {})
    assert {item["code"] for item in diagnostics} >= {"INVALID_TIME", "INVALID_VERSION", "INVALID_BLOCKS"}


def test_validation_accepts_starter_chapter():
    assert validate("chapter", {"time": 1, "version": "2.30.2", "blocks": []}) == []
