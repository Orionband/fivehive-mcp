# Google Docs API mapping

This mapping is implemented as a retrieval guide for the MCP. The MCP calls `documents.get` with `includeTabsContent=true`, traverses `tabs` and `childTabs`, and records `tabId`, title, parent, index, and source UTF-16 ranges.

| Docs API source | normalized source | FiveHive destination | blocking condition |
|---|---|---|---|
| `Tab`, `childTabs` | ordered tab tree | selected chapter/test/FRQ source | multiple tabs without explicit selection |
| `StructuralElement.paragraph` | paragraph node plus text runs and paragraph style | paragraph/header/list blocks | unsupported paragraph element |
| inherited `TextStyle`/`ParagraphStyle` | resolved bold/italic/link/heading/alignment | field-specific HTML or rich text | style cannot be represented |
| `Table` and `TableCell` | rectangular cells plus row/column spans | native table or KaTeX array | merged/nested table requiring user choice |
| `InlineObjectElement` | asset ID, source range, description, crop/effects | image block or question file | temporary image unavailable |
| `Equation` | equation marker and source range | validated KaTeX or reviewed image | no authoritative formula/image |
| `FootnoteReference` and `footnotes` | reference plus note body | ordinary reference text/diagnostic | note cannot be associated |
| `suggestedInsertionIds` / deletion IDs | suggestion inventory | selected text view | unresolved suggestions without user decision |
| links, bookmarks, rich links, chips, dropdowns | display text plus target metadata | validated links or plain text | unsafe/unresolved external target |
| headers, footers, breaks, columns | separate layout inventory | omission or explicit conversion | semantic content would be lost |

Google image `contentUri` values are temporary and must be downloaded during extraction. Native equation objects do not expose LaTeX. The MCP therefore stops and asks the user when no authoritative equation representation is available. It does not export PDF or DOCX.

The website-specific schema and all field-level rules remain in `docs/google-docs-porting-reference.md`.
