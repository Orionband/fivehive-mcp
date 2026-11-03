# Required FiveHive porting procedure

Read fivehive://porting-reference, fivehive://editorial-standards and fivehive://schemas/{content_type} before authoring. The editorial standards include the reviewed Website Porting Onboarding and biology/chemistry house style. The AI client performs semantic conversion; this MCP has no language model. A successful tool call or valid schema does not establish fidelity.

Match the existing Biology and Precalculus articles' heading hierarchy, retained emphasis, source-author credits, figure captions, math and interactive practice. The bundled fivehive://website-examples resource records inspected examples and renderer contracts. Compare the actual destination surface: guide cards, timed MCQs, simple written-response cards and digital rubric FRQs have different structures.

## 1. Retrieve and inventory the source

Use the authorized Google Drive get_document tool with the full native document resource. Do not substitute get_document_text, readable fetch output, or reconstructed text-only paragraphs. Keep tab bodies, text runs/styles, named styles, lists, tables, inlineObjects and positionedObjects. Traverse child tabs. Image dictionaries may live on each tab, not the document root. Select all requested tabs and use their exact titles as metadata. Discover existing destination IDs through list_destinations; never substitute emulator fixture IDs for production IDs.

Save the exact connector JSON with UTF-8 and a JSON serializer. Do not pipe Unicode JSON through a shell/codepage, concatenate JSON strings, or encode/decode text to ASCII. Preserve valid Unicode including curly quotes, arrows and Greek letters. Mojibake such as “â€™”, replacement characters, unpaired surrogates, and literal backslash-n prose are defects to investigate against the source. Never globally replace backslashes: LaTeX commands need them. A JSON escape \n becomes a real newline when parsed; the two literal characters backslash and n must not appear as paragraph terminators. Remove only actual paragraph-ending newlines; preserve internal breaks as supported markup.

Call ingest_source_document and inspect its diagnostics and asset inventory. Inventory headings, emphasis, tables, images, hyperlinks, citations, equations, practice prompts, options, keys and explanations. Missing source structure is a blocker. Ask about suggestions or unavailable source content instead of inventing a resolution.

### Questions and recovery: keep the import moving

When an issue needs a user decision, ask the user a specific question immediately: identify the article, source location/question/image, exact inconsistency, and the smallest actionable choices. Batch related questions when helpful, and continue independent articles while waiting. Do not finish with only a list of blockers when a question could resolve them. Never guess answer keys, invent missing practice, silently omit images/questions, or treat an acknowledgment as a correction. Record the user's answer, apply it only to the affected material, then check the saved content again. An exclusion authorized for one question/article does not authorize excluding other material.

Fix mechanical problems autonomously: retry transient failures with bounds, inspect the structured API error, preserve UTF-8, repair storage representations, and retry the same idempotent submission. Do not create duplicate chapters after an uncertain response: inspect job status and discovery first. If a temporary source image URL expires, use its retained original or refresh that asset through the source connector. A vague mention of practice questions in an introduction is not proof that the document actually contains a practice section; inspect the entire selected tab before labeling conversion incomplete.

The existing website/editor image limit is 5 MiB, with a bounded 50 MiB source download. Retain the original locally. Oversized static images may use a verified lossless WebP derivative with identical decoded pixels/dimensions; record the transformation. If that still exceeds the upload limit, ask the user whether to resize/compress or supply a smaller original. Do not resize, use lossy compression, drop animation frames, or omit the image without a decision.

For expired image URLs without a retained original, retrieve the full document again through Google Drive and call ingest_source_document with the same tab_ids and refresh_artifact_id. Refresh requires identical normalized content and source asset IDs; changed text is rejected and needs a newly reviewed artifact. Refresh invalidates the old review. Submit errors expose an HTTP status, API error code and requestId; use these to diagnose the failure, rather than reporting only “FiveHive returned errors.”

After resolving issues, resume uploads → validation → source comparison → private draft → website preview check. If the user has already explicitly requested publication, publish the successfully reviewed content within that authorization without repeatedly asking. Otherwise present the concrete draft for publication approval. Never publish an unresolved article or imply that an upload alone published it. Partial success is reported per article with its draft/public URL and exact outstanding question; work on the remaining articles continues.

## 2. Author the chapter with the correct blocks

Use header blocks at levels 1–3, paragraph HTML for prose, nested list blocks for lists, and supported native tables for simple grids. Resolve inherited formatting. Preserve bold with <b>, italics with <i>, and hyperlinks as validated <a> markup. Do not flatten everything into paragraphs. Preserve text order and meaningful spaces between runs. Relocate the title/byline to metadata only with a source-map record; do not use “Google Drive source” as a replacement author when the source names an author.

Classify links before copying them. Exclude clearly internal drafting/source-navigation links (for example, a Google Doc linked as “3.13 and 3.14” above Introduction) from the article body, recording the exclusion. Preserve genuine reader-facing resources and citations; ask when purpose is ambiguous. Resolve educational topic references to verified website destinations rather than leaking a drafting-document link or guessing a replacement URL. Each question group restarts at 1 and shows its total; apply the editorial standards' local-numbering rule in the content, without modifying renderers.

Each source image must become a real image block or a question attachment at its original position. Split text around inline images. Resolve positioned-image anchors explicitly. Materialize temporary image URIs promptly, inspect bytes and dimensions, retain captions/citations and accessible descriptions, and upload through the private asset workflow. Never replace a figure with an alert, a caption alone, or an “image retained for review” placeholder. A failed download/upload or unavailable preview is blocking. Do not claim an asset tool works until its server job exists, its ID is correct, and authorized readback succeeds. Keep temporary Google URLs out of published JSON.

For image blocks use data.file.url plus the supported caption/size fields from the reference. For question media use QuestionInput.files with image-prefixed stable keys and [image:key] placeholders. Those formats are different. Bind each source asset ID to its exact content JSON pointer in manifest.assetBindings.

For source citations, use the exact visible label Image Source linked through data.richCaption to the source page, with plain data.caption as the fallback text. Preserve separate descriptive captions and required attribution. Never display raw URLs or fabricate links for book/page-only credits. See the editorial standards for the exact JSON shape. Upload source images through the private asset workflow, then check the saved JSON and website preview with all uploads complete. Asset upload alone does not publish content.

## 3. Convert embedded practice into questionsAddCard

Practice questions belong in questionsAddCard blocks at their source position, not prose paragraphs or answer-key tables. Each card needs a unique selector-safe instanceId and data.questions containing complete QuestionFormat objects:

    {
      "type": "mcq",
      "question": {"value": "Source prompt", "files": []},
      "options": [
        {"id": "1", "value": {"value": "Source choice A", "files": []}},
        {"id": "2", "value": {"value": "Source choice B", "files": []}}
      ],
      "answers": ["2"],
      "explanation": {"value": "A is incorrect. Source rationale.\n\nB is correct. Source rationale.", "files": []},
      "content": {"value": "", "files": []},
      "topic": "6.1"
    }

This two-choice example illustrates the shape; preserve the source's actual number and order of choices. Answer values are option IDs, never indexes or choice text. Obtain correctness only from the supplied key. Keys may be tables labeled Accuracy + Explanation or inline Answer (D): paragraphs. Preserve every rationale; separate per-choice rationales with two actual newlines in the parsed explanation. Remove duplicate prose answer-key blocks only after all their content is mapped into the card. Preserve stimulus/question images inside their corresponding buffers. Flag missing/ambiguous keys, mismatched option counts, duplicate source options, or conflicting rationales; do not repair subject matter by guessing.

One question displays Check For Understanding; multiple questions display a quiz. Standalone timed tests use their own schema; simple frq question cards are different from digital rubric FRQs. Do not invent timing, rubrics or calculator settings. Preserve literal LaTeX meaning and validate the website math delimiters/escaping throughout prompts, choices and explanations.

## 4. Superdancer's editorial conventions (adapted to the current website)

Preserve every paragraph, sentence, example, list, question, explanation and source emphasis in order. Do not summarize, paraphrase or add introductions. Use level 1 for main sections, level 2 for subheadings, and level 3 for deeper headings. Never underline headings. Keep the article topic/title in destination metadata; record relocation of any matching source heading. Ordinary prose retains meaningful bold, italic and underline.

Use FiveHive inline math $@...$. Fractions use \dfrac except when smaller fractions are appropriate inside exponents/roots; limits, sums and integrals use \displaystyle. Use proper operators and paired delimiters without changing meaning. Apply the reviewed onboarding's numerical-quantity rules and the editorial standards' identifier exemptions. Units use \unit/\qty; chemical formulas use mhchem \ce. Validate parsed LaTeX after serialization with the deployed macros/extensions. Do not blindly rewrite valid legacy expressions or the unit macros' internal implementation.

Use KaTeX arrays with column specifications and \\hline for mathematical tables when faithful and readable. Preserve all values, headings, columns and row order. Keep general prose/comparison tables in supported native table blocks; the older blanket array rule is not suitable for every biology table. Block merged/nested/image-containing cells if no faithful representation is available. Disclose accessibility/editability changes for a table rendered as math.

For MCQs, remove only presentational question prefixes (Question 1:, 1.) and option prefixes (A., B., etc.). Preserve meaningful numbers in prompts and all choice wording/order. Prefer numeric option IDs ("1", "2", "3", "4") in source order, and map source answer letters to those IDs: source B becomes answers ["2"]. Use the actual source choice count. Canonical authored data uses question.value; questionInstance is a renderer-derived legacy alias and must not be fabricated. If an existing supported payload contains both, keep both synchronized. Keep topic from the source and omit bookmarked as authored interaction state. Use the deployed compatible EditorJS version from the reference, not an old sample's release-candidate version.

For source per-choice explanations, label each as A is incorrect., B is correct., etc., keep the rationale verbatim after the label, and separate entries with two real newline characters. Programmatically inspect the saved parsed explanation.value, not a console display or JSON string with double escaping. Keep mathematical numbers in rationales and numeric choices in math. Do not manufacture missing rationales or force an inline single-rationale key into four invented paragraphs.

The existing guide renderers do not consistently add A–D labels to choices. Verify the actual rendered card when explanations reference letters; do not assume an old sample describes the current UI. Preserve written-response prompts and supplied model answers in supported question structures separately from MCQs.

Retain original figures and citations, and identify exact placements by source object ID, question/block identity, and preceding/following text. If an image cannot be inserted, provide that placement manifest outside the article and mark the port incomplete. No unrelated generated substitutes or placeholder paragraphs. Deliver the reviewed JSON/export, asset inventory, placement/coverage report and exact correction log. Record original and replacement text plus reason for any spelling/math correction; ambiguous content changes require the user's decision. Reopen the saved file and the website editor to verify formatting and explanations actually survived. If the imported display differs, investigate its state/renderer instead of blaming an older user upload.

## 5. Coverage and review execution

Populate manifest.sourceMap with one record per normalized source node, using nodeId and targetPointer (a JSON pointer into content). A relocation uses a manifestPointer instead. Multiple source nodes may map to one block or question. Every source image also needs an asset binding with assetId and targetPointer. Record explicit source corrections, source-authorized omissions and unresolved questions separately; acknowledging an unresolved blocker is not a resolution.

Call validate_json, inspect every diagnostic, and resolve blockers. Compare the saved read_json result against the source, not against generated expectations. Check ordering, emphasis, headings, lists, complete text, citations, tables, all images, prompt/option/key mappings and every explanation. A successful validation call does not replace source comparison.

Submit a private draft, inspect website readback and the rendered chapter, and reopen it in the normal editor to test round-trip preservation. Verify images load without a Google session and MCQs display choices and explanations interactively. Report source/output counts and any unresolved differences. Publication requires explicit user instruction. If a stage is unsupported or unavailable, ask the user a focused question and continue independent work; do not silently downgrade to text-only or report a complete port. Correct formatting through the ported JSON and instructions; do not modify website renderers to make a port appear correct.
