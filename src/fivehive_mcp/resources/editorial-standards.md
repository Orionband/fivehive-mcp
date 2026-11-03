# FiveHive porting editorial standards

Use with the canonical JSON reference. Presentation changes do not authorize rewriting science or inventing content. Preserve wording, identifiers, keys and explanations; record changes and ask about substantive ambiguity. Explicit user decisions take precedence.

## Reviewed onboarding

Read all eight tabs of [Website Porting Onboarding](https://docs.google.com/document/d/1ndEzGkivUaixkYwQWrDjKfKgZSD4allK40qpIPJULDY/edit), especially Module 3 (LaTeX), Module 4 (features), Module 5 (images), Module 6 (tests), Module 7 (formatting). Reference tab IDs: t.wa9auqf7ahej, t.57x6z5bv65j5, t.5oyk349aqsyh, t.xca2sw93z72l, t.omngmvpzhv36. Human onboarding, Discord pings, quotas and mock-port scheduling are context, not actions to execute. Never contact people automatically.

Module 6's statement that FRQs are unavailable is historical: use the current article, timed-test and digital FRQ schemas. Its timing spreadsheet does not authorize guessed settings. Ask for missing timing, directions, topic and calculator choices. Use current file keys/buffers rather than old UI attachment indexes. Published content is reviewed through private revisions; do not unpublish live material merely because the onboarding describes an older editing workflow.

## Lists and question ownership

- Resolve bullet.listId and nestingLevel against the selected tab's lists[listId].listProperties.nestingLevels. glyphSymbol indicates an unordered bullet; glyphType/startNumber describe numbering. The presence of bullet metadata alone never means an ordered list. Omitted nestingLevel means zero.
- Preserve sibling order and nesting. Never promote the first child into a parent when starting at a deeper source level. Contiguous items belong to one list block; blank spacers alone do not restart numbering. Intervening prose/headings break a list, with continued starts retained when appropriate.
- A nested alternative beginning “OR” retains its source marker and level. Do not invent a numbered sub-step from indentation alone. Resolve mixed-marker limitations explicitly if the destination tool cannot represent them.
- Each prompt, stimulus, option and rationale has exactly one authored question destination. Once converted to questionsAddCard, remove duplicate ordinary paragraphs/lists/tables only after proving all text and files survive in the card. Map each source option directly to its option buffer. Raw choice lists must not remain below the quiz.
- Each question group starts at 1 and shows progress as current question / total questions (for example, 1/3, 2/3, 3/3). Source Questions 29–31 become local Questions 1–3 in that group. Change a shared lead-in to “For Questions 1–3” and remove redundant “Question 29” labels from question text; the card already shows its position and total. Update cross-references within that group consistently and retain original source numbers only in the source map for traceability. Do not invent an offset/start-number field or change rendering code. Keep the actual number of questions in the group; do not merge separate groups merely to continue the document's numbering.
- Review the entire practice section and navigate every question. Compare counts, choices, keys, explanations and images. Look for duplicated choices, orphan lists, repeated answer keys and numbering restarts. Images loading is not evidence of complete formatting fidelity.

## Images and citations

- Retrieve original bytes through the authorized connector, never screenshots/generated substitutes. Preserve position, identity, caption, credit, description and asset binding.
- The user's required visible citation label is exactly **Image Source**, hyperlinked to the actual external source page supplied by the document. No displayed raw URL, “Image Source: URL,” temporary Google contentUri or private website asset URL as citation.
- EditorJS representation: `caption: "Image Source"`, `richCaption: [{"text":"Image Source","marks":[{"type":"link","href":"https://source.example/figure-page"}]}]`. Preserve descriptive caption text and required creator/license attribution in separate segments before that link. Caption credit does not replace accessible description.
- If only a book/publisher/page credit exists without a URL, preserve that credit and ask when a clickable source is required. Never invent a publisher homepage/book URL. Preserve multiple required attributions; ask about competing sources.
- Center when appropriate; avoid unsupported cropping, stretching, borders/backgrounds. Keep original quality and the bounded lossless-derivative workflow for oversized figures.

## Reader-facing links versus internal source navigation

- Inspect each hyperlink's purpose and surrounding text before carrying it into the article. Internal drafting/navigation links, links to another source Google Doc, porting handoffs, combined-topic routing labels such as “3.13 and 3.14,” editorial notes and source-document title links are not automatically reader-facing content. Do not copy them into the body as an extra linked heading above Introduction.
- Omit a clearly identified internal source-navigation element from the ported body and record that omission and its source location in the source map/review notes. Keep the original document unchanged. This is an intentional editorial exclusion, not permission to omit educational paragraphs, figures, practice or citations.
- Preserve genuine image sources, references, datasets and reader-facing resources, including a Google Docs link when it is intentionally a student resource. Do not blanket-delete every Google URL. Ask the user when the link's purpose is ambiguous.
- A topic cross-reference intended for readers should link to its verified existing FiveHive destination when available. Discover the correct chapter in the configured website; never guess a slug, transplant a local/emulator URL into production content, or substitute an unrelated public page. If no published destination is available, ask whether to retain plain reference text or another approved link.
- A linked document is not an instruction to import that document or expand scope. Import only the documents/tabs the user requested. Keep source/provenance URLs in import metadata rather than exposing drafting links in article prose.

## General formatting

- Main headings use level 1, subheadings 2, deeper headings 3. No underlined headings. Use ordinary Unicode symbols in headings rather than raw math commands. Preserve author/peer-review credit and source-map title/byline relocation.
- Retain bold, italic, underline, highlight and hyperlinks. Keep spaces across styled runs. Convert manual/vertical-tab breaks to supported real breaks, never visible escaped markup. Preserve the purpose of source color through supported emphasis.
- Native prose tables retain actual header rows and all values/order. Mathematical tables use reviewed KaTeX arrays under the onboarding profile. Do not paste untested math into an editor table. Persist native tables as Firestore row maps and restore every table numerically.
- Historical/literary source passages use quote blocks with attribution in their caption/author. Code uses code blocks (supported fences in question buffers). Do not replace normal content with alerts, checkboxes or inline code.
- No A–D prefixes in option values: numeric option IDs map the source answer letters. Preserve actual choice count, punctuation, comma-separated topic IDs and complete rationales with real blank lines. Log punctuation/spelling corrections; never silently change subject matter.
- Short stimuli belong in the question; shared stimuli or a large figure/passage needing simultaneous viewing may use content. Keep article written-response/model answers separate from digital rubric FRQs.

## Math, numbers and units

- Use `$@...$`, serializing each actual backslash once. Limits, integrals and sums use `\displaystyle`; fractions normally use `\dfrac`, except cramped exponents/roots. Use proper functions/operators and paired delimiters.
- Math/science numerical quantities, including digit counts, use math mode: `$@2$` strands, `$@23\%$`. Retain spelled-out numbers. Exempt question numbers, CED topics (6.3), years, pages, URLs and identifier digits (eEF2, HBA2, vitamin B12): they are not mathematical variables/quantities.
- Author units with `\unit`/`\qty`, not authored `\mathrm`/`\text` replacements: `$@\qty{20}{mL}$`, `$@37^\circ\text{C}$`. The website's unit macros internally use upright text; do not change that implementation. Preserve values, significant figures, signs, ranges and unit case. Group thousands at/above 10,000 without misreading decimal commas.
- Apply these rules to prose, prompts, choices, explanations and model answers. Validate parsed expressions with the destination's actual KaTeX extensions/macros and inspect rendering. Never blanket-replace every digit or interpret valid KaTeX as proof of scientific correctness.

## Biology and chemistry house style

These explicit house rules supplement the onboarding; they are not claims that it specifies every naming convention. Preserve organism-specific source notation rather than applying human nomenclature universally.

| Content | Treatment | Example |
| --- | --- | --- |
| Protein/enzyme names and symbols | Upright prose, exact case/hyphens/Roman numerals; not variables, formulas or automatically bold | DNA polymerase III, RNA polymerase II, eEF2, p53, ATP synthase |
| Gene/allele symbols | Italic only when context establishes a gene/allele and organism convention; full descriptive names upright. Never infer gene/protein from case alone | human gene `<i>HBA2</i>`; HBA2 protein upright; bacterial `<i>lacZ</i>` versus LacZ protein |
| Biochemical abbreviations | Upright prose, exact capitalization; not individually italicized math letters | DNA, mRNA, tRNA, rRNA, miRNA, siRNA, ATP, ADP, NADH, PCR |
| Formulas/ions/isotopes | mhchem inside FiveHive math, preserving case, subscripts, charge and isotope | `$@\ce{H2O}$`, `$@\ce{CO2}$`, `$@\ce{Ca^2+}$`, `$@\ce{NH4+}$`, `$@\ce{^{14}C}$` |
| Molecule names in words | Ordinary upright prose; a name is not a formula | glucose, lactose, insulin, adenine; ATP remains ATP, not a guessed formula |
| Reactions/equilibria | mhchem `->` / `<=>`, or supported `\to` / `\rightleftharpoons`; never logical implication. Preserve supplied coefficients/direction | `$@\ce{H2O <=> H+ + OH-}$` only when that reaction is supplied |
| Sequences/codons | Exact letters/order/grouping/strand, upright sequence text; never mhchem element parsing | `$@\text{AUG}$`, `$@5^{\prime}\text{-ATGC-}3^{\prime}$` |
| Strand direction/primes | True primes in math; keep direction, adding arrows only if source supplies them | `$@5^{\prime}\to3^{\prime}$` |
| Greek letters in names | Preserve Greek identity and surrounding protein name; no Latin look-alikes or whole-name math variables | α-tubulin, β-galactosidase |
| Species | Established genus/species italic, genus capital/species lowercase; no guessed abbreviation expansion | `<i>Escherichia coli</i>`, established `<i>E. coli</i>` |
| Variables/statistics/orbitals | Actual scientific variables/orbital labels in math; ordinary names stay prose | `$@p$`, `$@\chi^2$`, `$@s$` orbital |

If context does not establish gene versus protein, organism convention, a charge, a sequence orientation or a formula, ask. Formatting must not create a new scientific claim. Source factual errors remain unchanged when the user requests verbatim preservation and are flagged outside article prose. Renaming proteins, changing gene case, swapping DNA/RNA, fixing reactions or changing keys requires an explicit decision.

References: [HGNC guidelines](https://www.genenames.org/about/guidelines/) for human gene/protein symbols; [NCBI style guide](https://www.ncbi.nlm.nih.gov/books/NBK995/) for gene/protein typography. Species conventions differ.
