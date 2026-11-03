import asyncio
from pathlib import Path

from fivehive_mcp.resource_files import resource_text
from fivehive_mcp.source_documents import snapshot_from_document
from fivehive_mcp.validation import validate, validate_artifact


def chapter(text="It’s DNA → RNA, with <b>emphasis</b>."):
    return {"time": 1, "version": "2.30.2", "blocks": [{"id": "p1", "type": "paragraph", "data": {"text": text}}]}


def test_valid_unicode_is_preserved_but_corruption_is_blocked():
    assert validate("chapter", chapter()) == []
    assert "TEXT_ENCODING_CORRUPTION" in {d["code"] for d in validate("chapter", chapter("Itâ€™s DNA"))}
    assert "LITERAL_NEWLINE_ESCAPE" in {d["code"] for d in validate("chapter", chapter(r"DNA\n"))}
    assert validate("chapter", chapter("DNA\nRNA")) == []


def test_tab_local_images_survive_normalization():
    source = {"documentId": "doc", "tabs": [{"tabId": "t.0", "title": "Article", "inlineObjects": {
        "img1": {"inlineObjectProperties": {"embeddedObject": {"description": "DNA", "imageProperties": {"contentUri": "https://example.org/dna.png"}}}}
    }, "body": {"content": [{"sectionBreak": {}}, {"paragraph": {"elements": [{"inlineObjectElement": {"inlineObjectId": "img1"}}]}}]}}]}
    snapshot = snapshot_from_document(source)
    assert not snapshot["diagnostics"]
    assert snapshot["assets"][0]["contentUri"] == "https://example.org/dna.png"
    assert snapshot["assets"][0]["description"] == "DNA"
    diagnostics = validate_artifact("chapter", chapter(), {"sourceMap": [], "assetBindings": []}, snapshot)
    assert {d["code"] for d in diagnostics} >= {"SOURCE_NODE_UNMAPPED", "SOURCE_IMAGE_UNBOUND"}


def test_unresolved_record_is_not_a_resolution_just_because_it_has_a_pointer():
    snapshot = {"normalized": [{"nodeId": "n1", "runs": [{"content": "Missing paragraph"}]}]}
    manifest = {"sourceMap": [{"nodeId": "n1", "manifestPointer": "/resolutions/0"}], "resolutions": [{"nodeId": "n1", "status": "unresolved", "reason": "Content missing"}]}
    assert "UNRESOLVED_RESOLUTION" in {d["code"] for d in validate_artifact("chapter", chapter(), manifest, snapshot)}


def test_question_card_requires_complete_buffers_and_answer_references():
    content = chapter()
    buffer = lambda value: {"value": value, "files": []}
    question = {"type": "mcq", "question": buffer("Which?"), "options": [
        {"id": "a", "value": buffer("A")}, {"id": "b", "value": buffer("B")}
    ], "answers": ["b"], "content": buffer(""), "explanation": buffer("A is incorrect. Source.\n\nB is correct. Source."), "topic": "source-topic"}
    content["blocks"].append({"id": "q1", "type": "questionsAddCard", "data": {"instanceId": "unique-1", "questions": [question]}})
    assert validate("chapter", content) == []
    question["answers"] = ["missing"]
    assert "INVALID_QUESTION" in {d["code"] for d in validate("chapter", content)}
def test_porting_reference_matches_canonical_document():
    canonical = Path(__file__).resolve().parents[1] / "docs" / "google-docs-porting-reference.md"
    assert resource_text("porting-reference.md") == canonical.read_text(encoding="utf-8")


def test_mcp_stdio_serves_instruction_and_schema_resources():
    import json
    import sys
    from jsonschema import Draft202012Validator
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def check():
        async with stdio_client(StdioServerParameters(command=sys.executable, args=["-B", "-m", "fivehive_mcp.server"])) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                result = await client.call_tool("instructions", {"content_type": "chapter"})
                assert not result.is_error
                payload = result.structured_content or json.loads(result.content[0].text)
                assert payload["contentType"] == "chapter"
                delivered = await client.read_resource("fivehive://instructions")
                assert payload["workflow"] == "".join(part.text for part in delivered.contents)

                for uri, filename in (
                    ("fivehive://editorial-standards", "editorial-standards.md"),
                    ("fivehive://porting-reference", "porting-reference.md"),
                ):
                    resource = await client.read_resource(uri)
                    assert "".join(part.text for part in resource.contents) == resource_text(filename)

                for content_type in ("chapter", "test", "frq"):
                    resource = await client.read_resource(payload["schemaUris"][content_type])
                    schema = json.loads(resource.contents[0].text)
                    Draft202012Validator.check_schema(schema)

    asyncio.run(check())
