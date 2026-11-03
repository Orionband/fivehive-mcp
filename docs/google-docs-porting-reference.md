# Google Docs → FiveHive: JSON and MCP implementation reference

The current editorial companion is `fivehive://editorial-standards`, delivered in full by `instructions` and `fivehive://instructions`. It incorporates all eight tabs of the [Website Porting Onboarding](https://docs.google.com/document/d/1ndEzGkivUaixkYwQWrDjKfKgZSD4allK40qpIPJULDY/edit), plus explicit biology/chemistry house rules. Source bullet symbols versus numbering must be resolved through list definitions; converted practice must not retain duplicate prose choice lists. Image citation text is exactly **Image Source**, linked to the supplied source page. Preserve book/page-only credits without inventing links.

Classify hyperlinks by purpose: omit clearly internal drafting/source-document navigation, record the editorial exclusion, and leave the Google Doc unchanged. Preserve intended student resources/citations and ask when a link is ambiguous. Do not import linked documents automatically or invent replacement FiveHive URLs. Question groups use local numbering from 1 with the total shown; adapt source labels and shared lead-ins in the JSON, not the rendering code.

## Mandatory fidelity gate for MCP clients

Read `fivehive://instructions` before converting. It returns the full bundled
porting procedure, including source retrieval, encoding, formatting, images,
embedded practice, source coverage, and rendered review. It is not sufficient
to validate JSON without comparing the saved content with the source.
The AI client performs that comparison.

Use the structured Google Drive `get_document` resource. A readable-text fetch
does not preserve images, paragraph styles, list identity, tables, or answer-key
structure. Save connector JSON directly as UTF-8; literal backslash-n prose and
mojibake require source comparison. Preserve valid non-ASCII characters.

Map every normalized source node using `sourceMap` entries with `nodeId` and
`targetPointer`, or `manifestPointer` for a metadata relocation. Map each source
image using `assetBindings` with `assetId` and `targetPointer`. These mappings
are mechanically checked but do not prove semantic fidelity or uploaded image
availability. Actual download/upload/readback and rendered checks remain required.

Mechanical validation checks supported structures, IDs, source mappings, asset bindings and encoding. These checks do not infer an article's intended content from words in its headings or byline. The AI must compare the source with the saved content to establish coverage and fidelity.

For chapter practice, use `questionsAddCard` and complete `QuestionFormat[]`:
prompt, stimulus, choices, supplied answer IDs, every source explanation, empty
attachment arrays where appropriate, topic, and a unique instance ID. Keep real
blank lines between choice rationales. Preserve heading levels and inline
emphasis. Source images require real image blocks/question attachments with
verified private website assets; a caption or workflow alert is insufficient.

This reference describes the website's JSON formats and conversion constraints. Confirm compatibility with the configured website deployment; examples are illustrative data, not source material to reuse.

## 1. The three formats to keep separate

1. **Editor JSON:** EditorJS `OutputData`, used by the chapter import/export UI. Contains the article body only.
2. **Website storage:** Firestore subject/unit listings and chapter documents. A chapter document wraps Editor JSON in `data`, adds metadata, and changes table row arrays into a map.
3. **Proposed MCP request:** source document, destination, conversion policy, metadata, assets, and diagnostics. This wrapper must be unpacked before sending the article body to the existing editor.

AP Porting is the subject slug `porting`, titled `AP Porting`. It uses the same chapter schema and editor as other subjects. `src/lib/apPortingDefaults.ts` currently defines an empty `units` array. There is no separate porting language or populated starter curriculum.

This reference's guide JSON is the **chapter study-guide editor** format. The `/guides` route is a separate, hardcoded **FAQ Docs catalogue** using external links through `APsection`; it does not use this EditorJS import path. Do not assume `/guides` is a content storage collection or that a chapter import edits its FAQ links. A port intended to replace those external FAQ documents would need an explicit destination/product change as well.

## 2. Editor JSON envelope

```json
{
  "time": 1793577600000,
  "version": "2.30.2",
  "blocks": [
    {
      "id": "heading01",
      "type": "header",
      "data": { "text": "Cell Structure", "level": 1 }
    },
    {
      "id": "paragraph01",
      "type": "paragraph",
      "data": { "text": "Cells contain <b>organelles</b>." }
    }
  ]
}
```

| Field | Current contract | MCP validation recommendation |
| --- | --- | --- |
| `time` | Number; editor uses `Date.now()` | Finite integer milliseconds since Unix epoch |
| `version` | String; starter content uses `2.30.2` | Emit the verified compatible editor version; not an MCP schema version |
| `blocks` | Array in display order | Validate every block against its type |
| block `id` | Editor block identity | Unique, nonempty, CSS-safe string within an article |
| block `type` | Registered tool key, case-sensitive | Allow only supported block types |
| block `data` | Object whose fields depend on type | Validate required strings, arrays, enums, and numeric ranges |
| block `tunes` | Optional tune object | Currently only alignment is relevant here |

The chapter importer checks only that `blocks` is an array, `time` is numeric, and `version` is a string. It does **not** deeply validate blocks, HTML, URLs, math, questions, or attachments. Its error message omits the version requirement even though the code requires it.

JSON must have quoted keys, no comments, no trailing commas, no `undefined`, no `NaN`, and escaped control characters. Use a JSON serializer instead of assembling strings. Omit absent optional fields rather than filling them with `null` unless a field explicitly supports null.

## 3. Complete chapter block vocabulary

The block tools are `header`, `paragraph`, `image`, `list`, `questionsAddCard`, `math`, `quote`, `table`, `code`, `alert`, `embed`, and `delimiter`.

`alignment` is a tune. `inlineCode`, `Marker`, and `underline` are inline tools. They are **not standalone blocks**; the presence of a key in `EDITOR_TOOLS` does not make it a block type.

### Header

```json
{
  "id": "h01",
  "type": "header",
  "data": { "text": "Energy and Matter", "level": 2 },
  "tunes": { "alignment": "center" }
}
```

The configured editor offers levels **1, 2, 3**. The renderers clamp levels to 1–6, so a level 4–6 can display but is outside the configured authoring choices. Convert deep headings using a declared policy and report the change; do not promise unchanged editor round trips.

### Paragraph

```json
{
  "id": "p01",
  "type": "paragraph",
  "data": { "text": "A <b>bold</b> term, <i>emphasis</i>, and $@x^2$." }
}
```

Text is a string that can contain inline markup. It is not Markdown. Split document paragraphs into separate blocks; a string containing `# Heading` does not become a header. Separate Google text runs are usually combined into one paragraph string, retaining supported run formatting.

### Alignment

For **paragraph, header, and list** blocks:

```json
{ "alignment": "justify" }
```

This is the value of `block.tunes`, with `alignment` one of `left`, `center`, `right`, `justify`. It is a string, not `{ "alignment": { "alignment": "center" } }`. Missing means left. Saving strips invalid alignment and removes explicit left alignment. Quotes and images have their own alignment fields.

### Lists, including nested lists and checklists

```json
{
  "id": "list01",
  "type": "list",
  "data": {
    "style": "ordered",
    "meta": { "start": 1, "counterType": "numeric" },
    "items": [
      {
        "content": "First item",
        "meta": {},
        "items": [
          { "content": "Nested item", "meta": {}, "items": [] }
        ]
      },
      { "content": "Second item", "meta": {}, "items": [] }
    ]
  }
}
```

- `style`: `unordered`, `ordered`, or `checklist`.
- Top-level `meta`: always emit an object. The chapter save handler accesses it directly and can throw if missing.
- Ordered metadata: `start` is a number; `counterType` is `numeric`, `lower-roman`, `upper-roman`, `lower-alpha`, or `upper-alpha`.
- Each item: `content` string, `meta` object, recursive `items` array. An old-style array of strings is incompatible with this renderer.
- Checklist item metadata: `{ "checked": true }` or `{ "checked": false }`.
- Item content supports the same inline math parser as paragraphs.
- Current rendering recursively reuses the outer list's style and numbering metadata. Mixed ordered/unordered nesting and independent nested numbering do not have faithful renderer support. Checklist inputs are rendered as HTML controls; this is not a persisted student checklist feature.
- Numbering/start behavior uses custom CSS counters; visually verify lists that start above 1 or use nonnumeric styles.

### Table: editor form

```json
{
  "id": "table01",
  "type": "table",
  "data": {
    "withHeadings": true,
    "content": [
      ["Quantity", "Value"],
      ["Energy", "$@E=mc^2$"]
    ]
  }
}
```

- `withHeadings` makes the first row the header.
- `content` is a two-dimensional array of cell **strings** in the editor.
- `rows` and `cols` occur in a helper interface but are not required by the custom renderer; the row data defines the actual table.
- The renderer treats nonmath cell content as plain text and escapes HTML. `<b>word</b>` is shown as text, not bold formatting.
- Inline `$@...$` math is supported in cells.
- No website table model for row spans, column spans, nested tables, cell images, cell-level rich content, widths, or Google table styling. Flatten with explicit diagnostics or use an approved image fallback.

### Table: Firestore form

```json
{
  "id": "table01",
  "type": "table",
  "data": {
    "withHeadings": true,
    "content": {
      "row0": ["Quantity", "Value"],
      "row1": ["Energy", "$@E=mc^2$"]
    }
  }
}
```

Firestore does not permit an array directly inside an array, so `processTable` converts all rows to a map on save. Keep a canonical editor object and derive a separate storage copy; do not mutate the canonical object while preparing writes. This restriction does not forbid lists of objects which themselves contain arrays. [Firestore data types](https://firebase.google.com/docs/firestore/manage-data/data-types).

**Existing defects:** the client rehydrator converts only the first table, and both client and server sort row keys lexicographically. For 11+ rows, `row10` precedes `row2`. A correct MCP must not silently accept that corruption: fix readers to convert every table and sort numeric suffixes, or reject/report those cases until fixed. Padding keys would deviate from the writer's current naming and is not a substitute for fixing readers.

### Image

```json
{
  "id": "image01",
  "type": "image",
  "data": {
    "file": {
      "url": "https://example.org/assets/cell.png",
      "storageRefFullPath": "images/cell.png"
    },
    "caption": "A cell diagram. Source",
    "altText": "Diagram of a cell showing the nucleus and mitochondria",
    "richCaption": [
      { "text": "A cell diagram. ", "marks": [] },
      {
        "text": "Source",
        "marks": [{ "type": "link", "href": "https://example.org/source" }]
      }
    ],
    "withBorder": false,
    "withBackground": false,
    "stretched": false,
    "centerImage": true,
    "width": 70
  }
}
```

The example URL is illustrative and is not a provided asset.

| Field | Meaning |
| --- | --- |
| `file.url` | Durable browser-accessible image URL; canonical editor form |
| `file.storageRefFullPath` | Real Firebase Storage object path, optional for external images |
| `caption` | Plain fallback caption; keep synchronized with rich caption text |
| `altText` | Explicit accessible description; falls back to plain caption when absent |
| `richCaption` | Array of `{ text, marks }` segments |
| `withBorder`, `withBackground` | Boolean display options |
| `stretched` | Full-width display when custom width is absent |
| `centerImage` | Boolean horizontal centering |
| `width` | Numeric percentage of content column; editor resize range 15–100 |

Caption marks: `{type:"bold"}`, `{type:"italic"}`, `{type:"underline"}`, `{type:"highlight"}`, `{type:"link",href:"..."}`. `marks` is an array, allowing combinations. Segments contain text, not embedded HTML. A nonempty rich caption takes precedence over `caption` in rendering.

Caption links accept validated HTTP, HTTPS, mailto, and single-slash site-relative paths. Protocol-relative URLs, whitespace-containing URLs, and dangerous schemes are rejected. Do not apply this caption-specific policy as proof that all other fields are sanitized.

The editor uploader accepts images or `.svg` files up to **5 MiB**, uploads them to `images/<milliseconds>_<filename>`, and records URL plus storage path. Preserve MIME type, including `image/svg+xml`. SVG sizing relies partly on the storage path/URL identifying SVG; retain the extension.

The renderer has legacy support for `data.url`, but emit `file.url` for editor compatibility. Never invent a storage path for an external image: explicit editor image deletion can delete the referenced Storage object. Sharing one stored asset across independent chapters requires a deletion/reference policy because the current image tool has no reference counting. Custom width overrides stretching in rendering; emit consistent values.

### Display math

```json
{ "id": "math01", "type": "math", "data": { "text": "\\frac{a}{b}=c" } }
```

Use raw LaTeX in `data.text`, without `$`, `$$`, or `$@` delimiters. JSON escapes each backslash as `\\`. Display math uses KaTeX with `throwOnError: true`: invalid input can throw during article rendering. Validate before writing.

Inline math uses literal `$@` followed by LaTeX and a closing `$`, for example `"Speed is $@\\frac{d}{t}$."`. This parser is used in paragraphs, headers, list items, table cells, and question rich text; do not assume quotes, alerts, embeds, or image captions run it. Its regex cannot contain an internal dollar sign. Conventional `$...$`, `$$...$$`, and `\\(...\\)` are not automatically recognized as inline math by the site's parser.

The renderers load `mhchem` and define `\\unit` and `\\qty` macros. Use the exact macro definitions in the code when validating; do not assume the names mean a complete SI-units package. The site is using KaTeX, not a general TeX engine.

Exact JavaScript macro configuration currently shared by the renderers:

```ts
const katexMacros = {
  "\\unit": "\\,\\mathrm{#1}",
  "\\qty": "#1\\,\\mathrm{#2}",
};
```

### Quote

```json
{
  "id": "quote01",
  "type": "quote",
  "data": { "text": "Quoted text", "caption": "Attribution", "alignment": "left" }
}
```

Use `left` or `center`. The renderer only special-cases center. Quote alignment is in `data.alignment`, unlike paragraph alignment. Text and caption are inserted as HTML; sanitize before constructing them. No dedicated inline math pass here.

### Code

```json
{ "id": "code01", "type": "code", "data": { "code": "print(\"hello\")\n" } }
```

`code` is plain source text, not escaped HTML. The renderer runs automatic language detection with highlight.js. No stored language field is consumed by the custom renderer. Inline code in a paragraph is HTML `<code>...</code>`, not a `code` block or a Markdown backtick span.

### Alert / callout

```json
{
  "id": "alert01",
  "type": "alert",
  "data": { "type": "warning", "align": "left", "message": "Check your units." }
}
```

`type`: `primary`, `secondary`, `info`, `success`, `warning`, `danger`, `light`, `dark`. `align`: `left`, `center`, `right`. The actual field is **`message`**, not `text` (an installed package README example is inconsistent; the runtime and website renderer agree on `message`). HTML message content requires sanitization. No dedicated inline math pass.

### Embed

```json
{
  "id": "embed01",
  "type": "embed",
  "data": {
    "service": "youtube",
    "source": "https://www.youtube.com/watch?v=VIDEO_ID",
    "embed": "https://www.youtube.com/embed/VIDEO_ID",
    "width": 560,
    "height": 315,
    "caption": "Video explanation"
  }
}
```

This is a shape example, not a real video. `service` is used by the EditorJS embed tool. Website rendering consumes `source`, `embed`, `width`, `height`, and `caption`; a destructured `regex` variable is unused. Emit only services supported by the installed embed tool and validate the service/URL combination. A Google Docs hyperlink is not automatically an embed. The renderer inserts iframe URL and caption into HTML; arbitrary supplied iframe URLs are not a safe import contract. A converter should normally retain links as links and create embeds only by explicit policy.

### Divider

```json
{ "id": "divider01", "type": "delimiter", "data": {} }
```

Rendered as a horizontal rule.

## 4. Inline formatting is different in three places

### Article text

Paragraphs, headers, and list content can carry EditorJS inline markup. Core bold/italic, links, inline code, marker/highlight, and underline are available through the configured editor. Treat the installed editor/tool sanitizer as the round-trip contract, not the browser's ability to display arbitrary HTML. A conservative serializer should produce `<b>`, `<i>`, `<u>`, `<mark>`, `<code>`, and validated `<a href="...">` as appropriate and escape literal text. Verify `<br>` and superscript/subscript round trips before relying on them in article blocks; they have explicit support in question rich text, but are not a promise of this article toolbar.

The article renderer decodes HTML entities before rendering inline markup; entity escaping by itself is not an adequate sanitizer for untrusted input. Table cells follow a separate decode-then-escape path. A server-side importer needs deliberate, field-specific sanitization and render tests, including literal `<`, `&`, and text that resembles tags. Do not copy arbitrary Google-export HTML or CSS into these fields.

Unsupported typography includes arbitrary font faces/sizes, text colors, highlight palettes, indentation measurements, line spacing, columns, page margins, and exact page layout. Highlight generally maps to one semantic highlight appearance.

### Question / FRQ rich text

The allowed tags are `strong`, `b`, `em`, `i`, `u`, `mark`, `br`, `div`, `sup`, `sub`, `ul`, `ol`, `li`. Attributes are stripped. In particular, hyperlinks and arbitrary styles are not preserved in these question fields. Normalize bold/italic to `strong`/`em` when generating question text.

The renderer additionally recognizes `$@...$` math, triple-backtick code fences, and `[image:...]` placeholders inside text nodes. Code fence language names are not parsed specially; use a `code` block for article source code. Ordinary Markdown is not a general question formatting language.

### Image captions

Use structured `richCaption` segments and marks described above. Caption math and inline code are not a dedicated supported mark. Caption formatting must not be serialized as question HTML.

## 5. Questions embedded in guides

```json
{
  "id": "questions01",
  "type": "questionsAddCard",
  "data": {
    "instanceId": "question-set-unique-01",
    "questions": [
      {
        "type": "mcq",
        "topic": "Cell Structure",
        "question": { "value": "Where is most DNA stored in a eukaryotic cell?", "files": [] },
        "content": { "value": "", "files": [] },
        "options": [
          { "id": "a", "value": { "value": "Nucleus", "files": [] } },
          { "id": "b", "value": { "value": "Ribosome", "files": [] } }
        ],
        "answers": ["a"],
        "explanation": { "value": "The nucleus houses most of the cell's DNA.", "files": [] },
        "calculatorOverride": "inherit"
      }
    ]
  }
}
```

Two options illustrate the data shape; an AP-style item can have four. The schema does not require exactly four.

```ts
type CalculatorPermission = "allowed" | "not-allowed" | "inherit";
type CalculatorType = "fourFunction" | "scientific" | "graphing";

interface QuestionInput {
  value: string;
  files: QuestionFile[];
}

interface QuestionFile {
  key: string;
  name: string;
  url?: string;
  id?: string;
  alt?: string;
  order?: number;
}

interface QuestionFormat {
  question: QuestionInput;
  type: "mcq" | "multi-answer" | "frq";
  options: { id: string; value: QuestionInput }[];
  answers: string[];
  explanation: QuestionInput;
  content: QuestionInput;
  topic: string;
  calculatorOverride?: CalculatorPermission;
  bookmarked?: boolean;
}
```

- `question`: prompt; `content`: stimulus/passage used in the test renderer's left pane; `explanation`: rationale/sample answer.
- `answers` contains option IDs, never indexes or answer text. Validate all references and unique option IDs. Proposed validation: one answer for `mcq`, multiple permitted for `multi-answer`.
- `frq` here is the simple question-card free-response variant; options/answers are unused, and explanation holds the sample answer. It is **not** the digital FRQ template with grading rubrics.
- Emit all required buffers, arrays, and `topic`, even when empty. Omit `bookmarked` for published source content; it is a test interaction field.
- A guide with one question displays Check For Understanding; multiple questions display a quiz.
- `instanceId` is used in a CSS selector and `localStorage` key `questions_<instanceId>`. Use unique selector-safe IDs such as UUIDs; avoid spaces, punctuation needing CSS escaping, or duplicate values across independent blocks.
- The chapter importer preserves block IDs and instance IDs. A standalone `AdminImport.tsx` utility can regenerate them, but its validation only requires `time` and `blocks`, and it does not save a chapter. Do not assume that utility is part of the chapter import path.
- **Editor initialization caveat:** `QuestionsAddCard.render()` mounts a component that initially reads localStorage instead of passing its imported `questions` directly. The preview renderer seeds localStorage and dispatches `questionsUpdated`. Import-to-editor behavior therefore depends on the preview/browser lifecycle. A headless writer should persist `data.questions` directly and validate rendering; an editor import needs explicit round-trip testing or an initialization fix.

### Question attachments

```json
{
  "value": "Use the graph below. [image:image-graph-01]",
  "files": [
    {
      "key": "image-graph-01",
      "name": "graph.png",
      "url": "https://example.org/assets/graph.png",
      "alt": "Graph of velocity against time",
      "order": 0
    }
  ]
}
```

Key prefix determines rendering: images use `image-` or `image/`; audio uses `audio-` or `audio/`. A URL alone without a suitable key does not guarantee rendering. These files use a different shape from article image blocks.

Files are sorted by `order` (missing values use 999). `[image:1]` chooses the first sorted file, `[image:<key>]` selects a key, and `[image:<filename>]` can select a case-insensitive filename or base name. Prefer key references: numeric matching uses permissive `parseInt`, and filenames can collide. Unmatched placeholders remain text. Referenced files render inline; unreferenced image/audio files render afterward. Other generic attachments do not have a corresponding generic renderer here.

`processQuestions` uploads files lacking an HTTP URL by looking in IndexedDB using browser-local keys, then fills `url`. That browser state is not present in an MCP process. Resolve and upload attachments server-side; emit durable URLs. Do not place `blob:` URLs, Google authentication-dependent URLs, or unresolved local file keys in a published payload.

Calculator permission resolves question override → set default → course default. Missing/`inherit` falls through; no explicit allowed value ultimately means disabled. Do not assume guide question cards expose every testing feature merely because the shared type has the field.

## 6. Destination structure and Firestore chapter documents

```text
subjects/{subjectSlug}
subjects/{subjectSlug}/units/{unitId}
subjects/{subjectSlug}/units/{unitId}/chapters/{chapterId}
subjects/{subjectSlug}/units/{unitId}/tests/{testId}
subjects/{subjectSlug}/units/{unitId}/frqs/{frqId}
```

Subject listing shape:

```json
{
  "title": "AP Porting",
  "hasUnit0": false,
  "calculatorDefault": "inherit",
  "referenceSheets": [],
  "units": [
    {
      "id": "unitA123",
      "title": "Unit 1: Cells",
      "chapters": [
        { "id": "chapA123", "title": "Cell Structure", "isPublic": false }
      ],
      "tests": [],
      "frqs": []
    }
  ]
}
```

The unit document duplicates the unit object from the subject's `units` array. The subject document drives ordering and navigation. A standalone chapter document does not automatically appear in navigation. When adding content, preserve all existing units, tests, FRQs, reference sheets, titles, visibility, and order unless the request changes them.

Chapter storage shape, shown as SDK-oriented TypeScript because timestamps are not plain JSON:

```ts
{
  id: chapterId,
  title: `${unitId}/chapter/${chapterId}`,
  author: "Author name",
  createdAt: /* Firestore Timestamp or SDK Date */,
  isPublic: false,
  data: /* OutputData with every table converted to row map */
}
```

The chapter display title belongs to the listing entry (`unit.chapters[].title`). Existing metadata/types are inconsistent: `Content` declares `displayName`, while the normal article writer does not populate it. Do not make up a dependency on `displayName`. The metadata title written by the article editor is the route fragment, not the first header or necessarily the visible chapter title.

**Current writer caveat:** `ArticleCreator.handleSave()` writes a fresh UUID in `id`, resets `createdAt`, and uses `setDoc` without merge, with only `id`, `createdAt`, `author`, `title`, and `data`. Thus it can remove `isPublic` and other metadata previously written by the structure editor. The route/document ID remains the true target. For a new MCP writer, explicitly preserve creation metadata and unrelated fields, keep document identity stable, and coordinate visibility with listings. Reopening and saving via the existing editor can still erase those extra fields until that behavior is fixed.

Public availability requires consistent `isPublic` in both the chapter listing and content document. The public server page checks the listing; Firestore rules check the content document. Updating only one can leave a link visible but unreadable, or an unlisted document publicly readable.

### Routes and IDs

Admin chapter route: `/admin/subject/{subjectSlug}/{unitId}/chapter/{chapterId}`.

Public chapter route: `/subject/{subjectSlug}/unit-{displayNumber}-{unitId}/chapter/{chapterId}/{formattedChapterTitle}`.

Display number comes from array position, starting at 1 or at 0 when `hasUnit0` is true. The public reader extracts unit ID from the last hyphen-delimited unit segment and chapter ID from the first two hyphen-delimited components. Current admin IDs are short alphanumeric strings. **Do not start using arbitrary hyphenated UUIDs for unit/chapter IDs without fixing these readers.** This restriction does not apply to question `instanceId`, which has a different purpose. Existing `formatSlug` strips characters outside `[a-z1-9 ]` before turning spaces into hyphens, including the digit 0; reuse or intentionally fix that behavior instead of inventing a competing route formatter.

### SDK objects versus Firestore REST JSON

The examples above describe application data. Firestore's REST API uses typed values, not ordinary JSON directly:

```json
{
  "fields": {
    "author": { "stringValue": "Author name" },
    "isPublic": { "booleanValue": false },
    "createdAt": { "timestampValue": "2026-11-02T12:00:00Z" },
    "data": {
      "mapValue": {
        "fields": {
          "time": { "integerValue": "1793577600000" },
          "version": { "stringValue": "2.30.2" },
          "blocks": { "arrayValue": { "values": [] } }
        }
      }
    }
  }
}
```

Prefer an SDK with explicit serialization helpers over manually constructing this encoding. `data.time` is milliseconds, a test's `time` is seconds, FRQ `timeLimitMinutes` is minutes, and Firestore `createdAt`/`updatedAt` are timestamps. Do not conflate them.

Firestore documents have a 1 MiB size limit and a maximum map/array nesting depth of 20. Measure the stored representation with headroom; long guides, deeply nested lists, and subject listings can exceed limits. Store image bytes in Storage, not Base64 in the chapter. [Firestore limits](https://firebase.google.com/docs/firestore/quotas).

## 7. Other authored content that a broader porting MCP may support

### Standalone MCQ / question tests

These are not EditorJS documents. They use `QuestionFormat[]` directly:

```json
{
  "name": "Cells Practice",
  "instanceId": "porting_unitA123_test_testA123",
  "time": 1200,
  "directions": "Choose the best answer.",
  "questions": [],
  "isPublic": false,
  "calculatorDefault": "inherit",
  "calculatorType": "graphing",
  "referenceSheetEnabled": false,
  "referenceSheetId": ""
}
```

`questions` contains the objects defined above. The test editor derives its instance ID from route segments joined with underscores. The unit's `tests` listing contains at least `id`, name, and visibility; the shared `UnitTest` type also declares questions/timing fields, although listing writes and content writes are separate at runtime. Preserve established listing entries instead of copying large question banks into every listing.

The test editor shown in this repository has no chapter-style JSON import/export panel. A chapter payload must not be submitted as a test payload.

### Subject reference sheets

```json
{
  "id": "sheetA123",
  "title": "Formula Sheet",
  "content": { "value": "Useful formula: $@E=mc^2$", "files": [] }
}
```

These live in `subject.referenceSheets`. Tests and FRQs reference their ID, with separate enabled flags. They use question rich text, not EditorJS blocks.

### Digital FRQs with rubrics

These use their own nested schema, not `QuestionFormat.type = "frq"`:

```json
{
  "subject": "porting",
  "unitId": "unitA123",
  "title": "Cell Investigation",
  "directions": "Answer all parts.",
  "directionsFiles": [],
  "sectionLabel": "Section II",
  "sectionSubtitle": "Free Response",
  "timeLimitMinutes": 30,
  "isPublic": false,
  "calculatorDefault": "not-allowed",
  "calculatorType": "graphing",
  "referenceSheetEnabled": false,
  "referenceSheetId": "",
  "questions": [
    {
      "id": "question-01",
      "stimulus": "A researcher observes cells.",
      "stimulusFiles": [],
      "calculatorOverride": "inherit",
      "parts": [
        {
          "id": "part-01",
          "title": "A",
          "prompt": "Identify one organelle involved in ATP production.",
          "promptFiles": [],
          "answerType": "text",
          "status": "public",
          "criteria": [
            {
              "id": "criterion-01",
              "description": "<strong>Mitochondrion</strong> identified.",
              "descriptionFormat": "html",
              "descriptionFiles": [],
              "points": 1
            }
          ]
        }
      ]
    }
  ]
}
```

- Optional document `id` and Firestore `createdAt`/`updatedAt` timestamps may also exist.
- Question stimulus, directions, and part prompt are rich-text strings with parallel attachment arrays.
- `answerType`: `text` or `equation`; part `status`: `public` or `legacy`. A part's public status determines inclusion in new attempts, not document visibility.
- Criterion points are normalized to nonnegative whole numbers; totals are derived by summing rubric criteria.
- `descriptionFormat: "html"` is required when storing a rich HTML rubric description. Without it, the description is intentionally treated as legacy plain text, because plain `x<y` must not be parsed as HTML.
- Keep part IDs stable across edits and reordering: submitted responses and grades reference them. Part IDs should be unique across the template, not only within one question. Keep criterion and question IDs stable too.
- Normalizers drop parts/questions without stable IDs and wrap legacy flat question arrays. Emit the current nested shape instead of relying on legacy migration.
- Timing defaults to 90 minutes for older templates without `timeLimitMinutes`.
- Part titles are positional display labels recomputed as A, B, etc. within each question by the editor's save builder; IDs remain the persistent identity.
- Use `writeFrqWithListing` / the same transactional listing pattern as the editor to keep subject and unit FRQ listings consistent with the template.
- Preserve removed parts as `legacy` when existing submissions need them; do not renumber identities from array positions.
- Port authored templates only. Student responses, submissions, and grades are separate records and are not source-guide content.

## 8. Google Docs extraction and conversion

Use structured Docs content, not plain-text extraction, when formatting and images matter. The connected Drive plugin exposes a native `get_document` capability; plain `fetch`/text tools are useful for inspection but do not establish a lossless source format. Confirm the actual connector result includes the required structural fields before depending on it.

For a custom Google API client, request `documents.get` with `includeTabsContent=true`, traverse child tabs, and select tab IDs explicitly. Omitting it can yield only the first tab. Set a suggestions policy explicitly and record it; do not modify the source document merely to choose a view. [Docs get API](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/get), [tab handling](https://developers.google.com/workspace/docs/api/how-tos/tabs).

Google indices are UTF-16 code units. Preserve tab ID and source ranges in a conversion map. Native equation objects do not supply a LaTeX body in the documented resource; do not invent equations from their presence. Image `contentUri` is temporary (default lifetime 30 minutes), so materialize it promptly and upload a durable website asset. Crop/rotation effects need explicit handling before rehosting original bytes. [Docs resource, equations, and image properties](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents).

The following is the **proposed conversion policy**, not an implemented feature:

| Google Docs source | Website output | Policy / loss to report |
| --- | --- | --- |
| Normal paragraph and text runs | `paragraph.data.text` | Combine runs, preserve spaces, encode supported inline formatting |
| Heading 1–3 | `header` with matching level | Keep hierarchy |
| Title / subtitle / Heading 4–6 | Declared mapping to header/paragraph | Report collapsed levels or subtitle styling |
| Bold / italic / underline | Appropriate article HTML or caption marks | Use field-specific serializer |
| Highlight | Semantic `mark` / caption highlight | Report color collapse |
| Superscript / subscript | Explicit question tags or math conversion | Article editor round trip needs verification |
| Hyperlink | Validated article `<a>` or caption link mark | Question text cannot retain hyperlink attributes |
| Bulleted / numbered paragraph | Recursive list item | Group contiguous lists; preserve nesting and starts where supported |
| Mixed nested list styles | Separate blocks or declared flattening | Current recursive renderer reuses outer style |
| Inline image in paragraph | Image block between text blocks | Split surrounding text in source order; report loss of inline flow |
| Positioned image / drawing | Extracted image block when obtainable | Resolve anchor position; report wrapping/cropping/layout changes |
| Rectangular simple table | `table` | Flatten cells to text; preserve supported math |
| Merged cells / nested tables / images in cells | Explicit fallback or blocked conversion | Do not silently discard spans or content |
| Literal LaTeX in source | Inline `$@...$` or `math` | Parse/validate, do not double-wrap existing math |
| Native Docs equation | Diagnostic until authoritative extraction exists | Source LaTeX or reviewed image/export fallback required |
| Code paragraph/section marked by source convention | `code` | Preserve source characters and line breaks |
| Quote/callout explicitly identified | `quote` / `alert` | Do not infer semantics from color/indent alone |
| Horizontal rule | `delimiter` | Preserve separator |
| Page/section break | Boundary or omitted layout marker | Report if author intended semantic separation |
| Footnote/endnote | Proposed references section + textual markers | No native website footnote block; preserve note content explicitly |
| Headers/footers/page numbers | Policy-controlled omission | Record omission; never confuse with body paragraphs |
| Table of contents | Omit or regenerate | Website navigation/headings differ from document pagination |
| Smart chips / bookmarks / internal links | Resolved text/link when possible | Do not publish unresolved source-local identifiers |
| Comments and suggestions | Diagnostics / selected content view | Never publish review comments by accident |
| Multiple tabs | One chapter per selected tab or explicit concatenation | Record order; do not silently omit tabs |
| MCQs, answers, explanations | Explicit question parser → `QuestionFormat` | Require reliable delimiters/source structure; do not guess keys |

For image conversion, retain accessible descriptions and attribution. Do not infer missing alt text or answers as source facts. A generated description or inferred classification must be marked as such in diagnostics.

For source styles, resolve inherited/default formatting rather than assuming every text run explicitly repeats bold/font/etc. Remove only the paragraph terminator when making blocks; do not globally trim intentional spaces or line breaks in code. A heading followed by an empty paragraph should not create an unexplained content gap.

Capture an extraction snapshot/revision identifier when available. Keep source credentials and temporary image-access URLs out of public article metadata and logs.

### Editorial porting profile

These editorial conventions supplement the schemas. Use the bundled editorial standards for the reviewed onboarding rules and subject-specific notation.

#### Preserve source content and disclose changes

- Preserve paragraphs, sentences, examples, explanations, lists, questions, choices, supplied model answers, captions, and citations in their original order.
- Do not summarize, paraphrase, shorten, add explanations, or silently omit difficult content. Do not insert workflow instructions or explanatory image-placeholder paragraphs into the published body.
- Preserve supported bold, italic, and underline in ordinary text. Record formatting losses where the target field cannot represent them.
- Separate formatting repairs from content changes. When a small spelling or mathematical correction is made under the authorized conversion policy, record the exact original, replacement, source location, and reason. Ambiguous mathematical errors require a diagnostic rather than an inferred correction.
- Keep an omission/correction report outside the article JSON. An import with unresolved source content must not be reported as a complete, faithful port.

#### Heading conventions

- Main section headings use `header` level 1; subheadings use level 2, and deeper subheadings use level 3.
- Remove underline markup from headings, while preserving appropriate ordinary-text emphasis.
- Keep the article's overall topic number and title in destination metadata rather than adding a duplicate body header solely for that title. If title text already exists in the source body, track its relocation explicitly so the fidelity check can distinguish relocation from accidental omission.
- This profile can override the earlier proposed direct mapping of Google heading levels. Record the chosen heading mapping in the conversion plan and apply it consistently.

#### Math typography conventions

Within this profile, put mathematical variables, equations, inequalities, expressions, and mathematical numeric values—including standalone numerical answer choices—inside the appropriate math representation. Do not wrap structural topic numbers, option IDs, list numbering, dates, or every prose numeral indiscriminately.

- Prefer `\\dfrac` for fractions, retaining smaller `\\frac` where appropriate inside exponents or roots.
- Use `\\displaystyle` for limits, integrals, summations, and other inline expressions where display sizing is intended. A `math` block already renders in display mode.
- Use matched `\\left` / `\\right` around mathematical delimiters where appropriate; do not mechanically replace function-command braces or LaTeX argument braces with delimiters. Check readability for long expressions and line wrapping.
- Use proper commands such as `\\lim`, `\\infty`, `\\geq`, `\\leq`, and `\\neq`.
- Repair malformed LaTeX and JSON escaping, then validate the **parsed string** with KaTeX. Do not validate only a visually plausible Markdown/code-fence rendering.
- The reviewed onboarding specifies authored units through `\unit` / `\qty` and chemical formulas/ions through mhchem `\ce`. Do not author unit substitutes using `\mathrm`; the current website's unit macros internally use upright text, which is an implementation detail to preserve. The editorial companion defines numeric-quantity handling and exemptions for structural labels and scientific identifiers, plus gene/protein/sequence conventions. Never blanket-rewrite legacy notation or identifiers.

Example paragraph data with the profile's typography:

```json
{
  "text": "The limit is $@\\displaystyle\\lim_{x\\to\\infty}f\\left(x\\right)=\\dfrac{3}{5}$."
}
```

Use `$@...$` in supported inline text fields; continue to use **undelimited** LaTeX inside `math.data.text`. The editorial preference does not change that schema distinction.

#### Mathematical tables as KaTeX arrays

Use KaTeX arrays for mathematical tables under the editorial profile, preserving headings, values, columns and row order:

```json
{
  "id": "mathTable01",
  "type": "math",
  "data": {
    "text": "\\begin{array}{|c|c|c|}\\hline x & 1 & 2 \\\\ \\hline f\\left(x\\right) & 3 & 5 \\\\ \\hline \\end{array}"
  }
}
```

This avoids the native table row-map conversion for that block. Native table blocks remain valid website data. KaTeX arrays are suitable for math-focused grids; they do not preserve semantic HTML table headers, editable cells, merged-cell layouts, embedded images, or arbitrary prose styling. Use `\\text{...}` for textual labels, escaping TeX-special characters correctly, and record that this policy changes table accessibility/editability. Do not silently force every general-purpose Google Docs table into math.

#### MCQ normalization and explanation spacing

- Keep practice MCQs in `questionsAddCard` blocks at their original position relative to article text. Preserve the source's actual choice count, ordering, wording, answer key, and explanations.
- Each question group starts at 1 and displays its current position and total. Update group-local lead-ins, prompt labels and cross-references consistently, preserving original numbers in source metadata. Keep meaningful mathematical numbers, citations and unrelated references. Use existing rendering behavior.
- Store choice bodies without a redundant `A.`, `B.`, etc. prefix when using this profile, and map displayed letters to positions in the unchanged option array.
- For newly created four-choice items, the profile prefers string option IDs `"1"`, `"2"`, `"3"`, `"4"`. These are strings, not numeric values. The website also accepts other string IDs. Preserve existing IDs during updates unless deliberately remapping every answer reference.
- Set `topic` to the source's known topic number, such as `"1.7"`; do not infer it from an unrelated destination unit.
- Keep written-response questions separate from MCQs using the supported simple `frq` card or digital FRQ mode, as appropriate. Preserve supplied model answers; do not invent them.
- Where the source provides per-choice rationales, retain each rationale and use labels such as `A is incorrect.` or `B is correct.` consistently. Separate A–D entries by **two actual newline characters**. Relabeling a rationale's introductory label is normalization; do not replace its explanatory content or synthesize missing rationales.
- Format mathematical content throughout option values and explanations, including standalone mathematical numbers, with inline math syntax.

Example explanation buffer:

```json
{
  "value": "A is incorrect. The expression approaches $@3$.\n\nB is correct. The limit is $@5$.\n\nC is incorrect. The expression does not approach $@7$.\n\nD is incorrect. The expression does not approach $@9$.",
  "files": []
}
```

In the serialized JSON file, `\n\n` represents two newlines after `JSON.parse`. A parsed string containing the four literal characters backslash-n-backslash-n is a double-escaping error. Question rendering uses `whitespace-pre-wrap`, so actual newline separators matter. The example above illustrates spacing only; it is not an answer key for another example in this reference.

Authored question compatibility:

1. **`questionInstance` is not a required authored field.** The shared `QuestionFormat` type defines `question`. The preview/hydrator derives a `questionInstance` alias from it. Generate canonical `question.value`; if an explicitly supported legacy payload already includes an alias, keep both values synchronized during normalization. Do not fabricate renderer-derived aliases.
2. **Automatic A–D labeling is not universal.** The current guide Check For Understanding and quiz renderers display option content without adding letter badges. The editor labels options numerically. If explanations refer to A–D, verify the intended display surface; add UI labels or agree on a labeling policy rather than claiming the guide automatically supplies them. Keep option labels as presentation data instead of silently altering answer identities.

Use an EditorJS version compatible with the destination website. A version string alone does not establish tool or schema compatibility; check the destination's actual import/export contract.

#### Images and handoff information

Preserve original figures and graph content; do not replace them with unrelated generated images. Preserve captions/citations and associate question images with the exact question. Use supported image/attachment fields and verified URLs only.

If automatic image insertion cannot be completed, return an external placement manifest containing source object identity, output block/question identity, caption/citation, the text immediately before and after the figure, and the unresolved reason. This is diagnostic handoff information, not a placeholder paragraph to inject into the article. A port with pending image placements is incomplete and must be labeled accordingly.

#### Inspect the saved result, not just the proposed output

Alongside the validation contract below, enforce this profile against the actual saved/exported JSON:

- Compare source and output coverage in order, including emphasis, all question parts, explanations, and figure placements. Permit only recorded relocations/normalizations/corrections.
- Check heading levels, the absence of underlined headers, the chosen table policy, and math in all question/option/explanation fields.
- Inspect parsed explanation values for actual blank lines between source-provided per-choice rationales, plus sensible sentence spacing. Do not manufacture a four-part explanation where the source supplies a different structure.
- Check removed presentational prefixes, topic values, unique IDs, and answer-to-option mappings after any ID changes.
- Validate KaTeX against strings read back from the JSON file; ensure the storage/readback representation has not changed escaping.
- If the editor displays different text or formatting, investigate serialization, sanitizer behavior, browser-local state, and caches using the observed payload.
- Return an import-ready Editor JSON artifact when export is requested, plus the external diagnostics/correction/asset report. No report or MCP wrapper belongs inside the raw EditorJS envelope.

## 9. MCP workflow

Use the implemented tools and bundled schemas described in the README and workflow resource. The AI interprets source content; the MCP manages structured source snapshots, artifacts, assets and website API calls. Discover destinations and compare source content before submission. Keep authentication and provenance out of public article data.

## 10. Validation required before calling a conversion successful

This is the proposed acceptance contract for the MCP:

- Envelope fields have correct types; all block types are recognized; IDs are unique and selector-safe where needed.
- All text buffers, list item arrays/meta, table cells, and question objects are structurally complete.
- Both renderer paths handle every emitted block; no unsupported block is silently omitted.
- HTML is sanitized for the specific destination field and survives its decode/render behavior; links and iframe URLs follow explicit allowlists.
- KaTeX accepts every display formula; inline formulas use the website delimiters and supported syntax.
- Every source paragraph/object is accounted for in output, an explicit omission, or a diagnostic. Nonempty diagnostics do not become an unqualified success.
- No original answer key, option, rubric line, note, table span, image, or caption is fabricated or silently lost.
- All question answers point to existing options; question attachment placeholders resolve; media URLs work outside the source Google session.
- Every table is converted in both directions; row ordering remains numeric; 11+ rows and multiple tables are specifically exercised after reader fixes.
- Public visibility and titles agree across content and listings; routing resolves the actual destination IDs.
- Stored size/depth fit Firestore limits with headroom, including changes to the duplicated subject/unit listings.
- New imports, repeat imports, conflicts, independent copies, asset failures, and rollback have defined outcomes.
- Round-trip test: source → editor JSON → Firestore representation → editor JSON → rendered chapter. Also reopen and save in the website editor to detect dropped fields or browser-local question state problems.

Meaningful fixtures include: plain guide; styled text with literal `<`/`&`; nested and mixed lists; multiple tables with double-digit row indices; image with rich caption; inline/display math including invalid LaTeX; one and multiple question cards with media; standalone test; digital FRQ with a rich rubric and stable legacy parts; and a multi-tab Google Doc containing an unsupported native equation.

The public server helper uses a **24-hour** fetch revalidation interval, and the client content cache uses **48 hours**. A direct database write does not invalidate those caches. Implement a real invalidation/version strategy or report the delay; do not promise immediate public visibility from a successful database readback alone.

## 11. Website implementation reference

These paths refer to the separate website repository, not to dependencies on a local checkout:

| Source | Why it matters |
| --- | --- |
| `src/components/article-creator/Editor.tsx` | Tool registration, image data/uploader, version check, raw JSON import/export |
| `src/components/article-creator/ArticleCreator.tsx` | Chapter path, metadata, destructive full document save, table/question processing |
| `src/components/admin/AdminImport.tsx` | Separate shallow validation and ID regeneration utility |
| `src/components/article-creator/FetchArticleFunctions.tsx` | Attachment uploads, table row-map conversion, first-table-only client restoration |
| `src/components/article-creator/Renderer.tsx` | Client renderer, math/HTML semantics, question preview seeding |
| `src/components/article-creator/editorjs-render.ts` | Server-compatible renderer; must stay aligned with client rendering |
| `src/components/article-creator/QuestionsHydrator.tsx` | Public interactive question hydration and CSS selector/localStorage contract |
| `src/components/article-creator/custom_questions/QuestionsAddCard.tsx` | Question-card constructor/render/save behavior |
| `src/components/article-creator/custom_questions/QuestionInstance.tsx` | Browser-local question state and one-versus-many display |
| `src/components/article-creator/custom_questions/RenderAdvancedTextbox.tsx` | Question markup, file-key prefixes, inline image matching, code/math tokens |
| `src/components/article-creator/custom_questions/richText.ts` | Allowed question tags and sanitizer behavior |
| `src/components/article-creator/caption-rich-text/` | Caption types, coercion, links, rendering, plain-text fallback |
| `src/components/article-creator/alignment.ts` and `AlignmentTune.ts` | Allowed tune values and serialization |
| `src/types/content.ts`, `src/types/firestore.ts`, `src/types/questions.ts` | Shared application type declarations; compare with actual writers |
| `src/app/admin/subject/[slug]/page.tsx` | Short IDs, mirrored listings, structure writes/deletes, AP Porting reset |
| `src/app/admin/subject/[slug]/[unit]/test/[id]/page.tsx` | Standalone test content load/save and timing |
| `src/components/subject/unit-accordion.tsx` | Public URL generation and ordering |
| `src/app/subject/[slug]/(sidebar)/[unit]/chapter/[id]/[title]/page.tsx` | Public visibility decision and server/client branch |
| `src/app/subject/[slug]/(sidebar)/[unit]/chapter/[id]/[title]/useFetchAndCache.tsx` | Client route ID parsing, table restoration, 48-hour cache |
| `src/lib/sitemap-data.ts` | Firestore REST decoding, server table restoration, 24-hour revalidation |
| `src/lib/apPortingDefaults.ts` | AP Porting's current empty initial structure |
| `src/types/frq.ts`, `src/lib/frq/template.ts`, `src/lib/frq/editorState.ts` | Digital FRQ contract, normalizers, payload construction |
| `src/lib/firestore/frqListing.ts`, `src/lib/frq/listing.ts` | Transactional FRQ/listing synchronization |
| `src/lib/calculator.ts` | Calculator enums and permission precedence |
| `firestore.rules` | Client read/write authorization |

Installed package source/readmes were used to cross-check list metadata, alert output, and math-tool fields. Resolve any package upgrade against the lockfile and actual runtime before treating these details as a permanent standard.
