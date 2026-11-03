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


def test_plain_prose_practice_cannot_be_reviewed_as_complete():
    snapshot = {"normalized": [{"nodeId": "n1", "runs": [{"content": "Practice Questions"}]}]}
    manifest = {"sourceMap": [{"nodeId": "n1", "targetPointer": "/blocks/0"}]}
    assert "PRACTICE_NOT_CONVERTED" in {d["code"] for d in validate_artifact("chapter", chapter(), manifest, snapshot)}


def test_mention_of_practice_in_introduction_does_not_invent_a_missing_section():
    snapshot = {"normalized": [{"nodeId": "n1", "kind": "paragraph", "style": {"namedStyleType": "NORMAL_TEXT"}, "runs": [{"content": "In this cram article, we provide examples and practice questions to solidify your understanding."}]}]}
    manifest = {"sourceMap": [{"nodeId": "n1", "targetPointer": "/blocks/0"}]}
    assert "PRACTICE_NOT_CONVERTED" not in {d["code"] for d in validate_artifact("chapter", chapter(), manifest, snapshot)}


def test_unresolved_record_is_not_a_resolution_just_because_it_has_a_pointer():
    snapshot = {"normalized": [{"nodeId": "n1", "runs": [{"content": "Missing paragraph"}]}]}
    manifest = {"sourceMap": [{"nodeId": "n1", "manifestPointer": "/resolutions/0"}], "resolutions": [{"nodeId": "n1", "status": "unresolved", "reason": "Content missing"}]}
    assert "UNRESOLVED_RESOLUTION" in {d["code"] for d in validate_artifact("chapter", chapter(), manifest, snapshot)}


def test_question_card_requires_complete_buffers_and_answer_references():
    content = chapter()
    buffer = lambda value: {"value": value, "files": []}
    question = {"type": "mcq", "question": buffer("Which?"), "options": [
        {"id": "a", "value": buffer("A")}, {"id": "b", "value": buffer("B")}
    ], "answers": ["b"], "content": buffer(""), "explanation": buffer("A is incorrect. Source.\n\nB is correct. Source."), "topic": "6.1"}
    content["blocks"].append({"id": "q1", "type": "questionsAddCard", "data": {"instanceId": "unique-1", "questions": [question]}})
    assert validate("chapter", content) == []
    question["answers"] = ["missing"]
    assert "INVALID_QUESTION" in {d["code"] for d in validate("chapter", content)}


def test_generic_source_author_is_blocked_when_original_has_a_byline():
    snapshot = {"normalized": [{"nodeId": "n1", "runs": [{"content": "Written by Ansh, Peer Reviewed by Pedal and River Antonov"}]}]}
    manifest = {"metadata": {"author": "Google Drive source"}, "sourceMap": [{"nodeId": "n1", "manifestPointer": "/metadata/author"}]}
    assert "SOURCE_AUTHOR_NOT_PRESERVED" in {d["code"] for d in validate_artifact("chapter", chapter(), manifest, snapshot)}
    manifest["metadata"]["author"] = "Ansh; peer reviewed by Pedal and River Antonov"
    assert not validate_artifact("chapter", chapter(), manifest, snapshot)


def test_required_instructions_are_delivered_and_reference_matches():
    instructions = resource_text("workflow.md")
    for required in ("get_document", "UTF-8", "questionsAddCard", "assetBindings", "sourceMap", "two actual newlines", "read_json", "ask the user a specific question immediately", "continue independent articles", "already explicitly requested publication", "lossless WebP"):
        assert required in instructions
    canonical = Path(__file__).resolve().parents[1] / "docs" / "google-docs-porting-reference.md"
    assert resource_text("porting-reference.md") == canonical.read_text(encoding="utf-8")


def test_mcp_stdio_delivers_full_instructions_and_reference():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def check():
        import sys
        async with stdio_client(StdioServerParameters(command=sys.executable, args=["-m", "fivehive_mcp.server"])) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                result = await client.call_tool("instructions", {"content_type": "chapter"})
                assert not result.is_error
                assert "questionsAddCard" in str(result)
                assert "UTF-8" in str(result)
                assert "HBA2" in str(result)
                assert "glyphSymbol" in str(result)
                standards = await client.read_resource("fivehive://editorial-standards")
                assert "Image Source" in str(standards)
                assert "eEF2" in str(standards)
                reference = await client.read_resource("fivehive://porting-reference")
                assert "Mandatory fidelity gate" in str(reference)
                schema = await client.read_resource("fivehive://schemas/chapter")
                assert "questionsAddCard" in str(schema)
                examples = await client.read_resource("fivehive://website-examples")
                assert "precalculus" in str(examples)
    asyncio.run(check())
