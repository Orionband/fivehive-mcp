# FiveHive porting workflow

Read fivehive://porting-reference, fivehive://editorial-standards and the relevant fivehive://schemas/{content_type} before authoring. The AI client interprets the source and constructs content; the MCP provides structured tools, resources and validation. Schema validation does not establish fidelity.

## Source and destination

Retrieve the complete structured document through an authorized external connector. Preserve tabs, text runs and inherited formatting, lists, tables, image objects and separately located content. Select only the requested documents/tabs. Pass the resource to ingest_source_document and inspect diagnostics and assets.

Use list_destinations to identify the existing course, unit and item, if updating. Do not derive IDs from display names or reuse IDs from another environment. Confirm content type and missing destination choices with the user.

Save source data and JSON as UTF-8 through a serializer. Preserve valid Unicode, spaces across text runs, and meaningful line breaks. Distinguish parsed newlines from literal escape characters; preserve LaTeX backslashes.

## Content conversion

Preserve educational text, ordering, emphasis, headings, examples, citations and author credits. Use the destination's actual block and assessment schemas. Relocate title/byline to metadata with a source-map record. Apply the editorial standards consistently across subjects.

Resolve list markers and nesting from the source definitions. Classify hyperlinks by purpose: retain reader-facing references, exclude identified internal editorial navigation, and record exclusions. Resolve cross-references to verified destinations; ask about ambiguous links.

Convert source practice into complete questionsAddCard data at its source position. Preserve prompt, stimulus, choices, supplied answer IDs, explanations and media. Do not leave duplicate ordinary-text questions or answer keys. Preserve actual group sizes, rebase group-local labels consistently, and use the correct schema for timed tests, article written responses and digital rubric FRQs.

Use unique selector-safe block/card IDs. Provide complete value/files buffers and numeric option IDs in source order. Answer references must identify the supplied correct options. Preserve per-choice explanations with readable labels and actual blank lines. Obtain correctness, model answers, rubric criteria, timing and calculator settings from the source or user; do not invent them.

Follow the supported math delimiters, extensions and serialization described in the reference. Verify parsed expressions and the resulting display without changing mathematical meaning. Native prose tables and mathematical arrays serve different purposes; preserve headers, cell values, row order and accessibility information.

## Assets

Retain each source image at its intended position as an image block or question attachment. Keep the original bytes, descriptions, captions and attribution. Do not substitute screenshots, generated figures, placeholders or temporary source URLs.

For article images bind the source asset ID to the exact data.file.url pointer. For question media use the schema's file keys and inline placeholders. Upload through the private asset workflow. Use the linked Image Source caption convention from the editorial standards, retaining required descriptive and license information.

Source downloads are bounded at 50 MiB and uploads at 5 MiB. Supported lossless derivatives must preserve decoded pixels and dimensions. Ask before resizing, lossy compression or other changes to a figure.

If a source URL expires, use the retained original or retrieve a fresh document resource. ingest_source_document can refresh an artifact's image references only when the normalized source content and asset identities are unchanged. Treat actual source changes as content requiring a new comparison.

## Questions and recovery

Ask focused questions whenever source content, semantics, destination choices or supported representation is uncertain. Identify the source location, the problem and actionable options. Batch related questions when useful and continue independent work while awaiting answers.

Record decisions and apply them only to their stated scope. Do not infer general omission permission from one excluded item. Fix mechanical serialization or transport issues independently, retry transient failures with bounds, and inspect job status before repeating a submission. Preserve idempotency keys when retrying the same request.

## Validation and review

Use create_json, update_json and read_json to work with saved content. Populate sourceMap for source coverage and assetBindings for image placement. Record intentional omissions and corrections separately from unresolved questions.

Call validate_json and address its diagnostics. Mechanical checks cover supported structure and references; the AI must separately compare the complete source with the saved result, including every question, answer, explanation, citation and figure. Review source content directly rather than guessing its structure from heading words.

Submit a private draft, inspect the server readback and preview, and verify round-trip preservation in the existing editor. Check full question groups and all media, not merely the presence of components. Report unresolved differences accurately. Correct ported content through its JSON; do not alter website rendering code as part of a port.

## Publication

Publish only when authorized by the user and the source comparison and preview checks are complete. Existing publication authorization applies within its stated scope; do not ask for it repeatedly. Keep unresolved content private and continue unaffected imports. Return the actual draft/public URL and status; asset upload alone is not publication.
