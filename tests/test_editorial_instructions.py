from fivehive_mcp.resource_files import resource_text


def test_editorial_instructions_include_numbering_and_citations_without_hash_workflow():
    from fivehive_mcp.server import instructions
    workflow = instructions("chapter")["workflow"]
    for term in ("Image Source", "glyphSymbol", "HBA2", "eEF2", "mhchem", "gene/protein", "1/3", "29–31", "starts at 1", "do not modify website renderers", "3.13 and 3.14", "Do not blanket-delete every Google URL", "never guess a slug"):
        assert term.lower() in workflow.lower()
    assert "hash" not in workflow.lower()
    assert "hash" not in resource_text("porting-reference.md").lower()
