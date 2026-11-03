# Website format observations

Inspected live on 2026-11-02. These are presentation examples, not substitutes
for the original source content or permission to copy other authors' material.

- Biology course: https://www.fivehive.org/subject/biology
- Biology example: https://www.fivehive.org/subject/biology/unit-6-4rn1uPYm/chapter/53uhbiCx/transcription-and-rna-processing
- Precalculus course: https://www.fivehive.org/subject/precalculus
- Precalculus example: https://www.fivehive.org/subject/precalculus/unit-2-bbwzkGcx/chapter/c16zbQhY/composition-of-functions
- Precalculus mixed-practice example: https://www.fivehive.org/subject/precalculus/unit-1-9onvd7by/chapter/argceXaD/rational-functions-and-end-behavior

The Biology example has main sections as H1, RNA-processing subsections as H2,
14 bold/strong spans, three loaded article images with source captions, and a
five-question interactive practice quiz. It preserves curly apostrophes and
direction arrows. A generic byline or a flat text dump does not match it.

The Precalculus example uses H1/H2 sections, bold emphasis, rendered KaTeX,
and authored practice/solutions. Some existing articles contain written
solutions as prose; this is not evidence that MCQs should be flattened. Follow
the source and destination contract, using interactive question cards where
requested and supported, preserving supplied model answers.

The rational-functions example has loaded graphs/diagrams, rendered math,
written-response practice and its supplied answer guide, plus an interactive
question card. Preserve the distinction between the explanatory article,
written practice/model solutions and MCQ interaction. Inspect each question
type rather than assuming all Practice Problems sections are MCQs.

Implementation contracts checked in the repository:

- `QuestionFormat` contains question/content/explanation buffers with value and
  files, type, topic, options and answer IDs.
- One simple question card renders CheckForUnderstanding; multiple questions
  render QuizRenderer.
- `type: "frq"` on a guide card provides a response box and reveals the supplied
  sample answer. It is self-assessed. It does not create a digital rubric exam.
- Digital FRQs use nested questions, parts and grading criteria, with stable
  identities; use their separate schema and template renderer.
- Article image blocks use `file.url`; question media uses attachment arrays
  with matching image keys/placeholders. Preserve attribution in both cases.

Before review, compare the new rendered page with a relevant example for
structure, not identical prose. Check source-author credit, every emphasis,
heading hierarchy, actual image loads, question interaction, math, and real
explanation paragraph breaks. Do not replace a named source author with the
connector name. Do not invent a missing author; ask the user.
