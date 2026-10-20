# Phase 4 completion: analysis and academic paper

Phase 4 delivers an eight-page paper, editable source, publication figures,
verified bibliography and reproduction documentation. Phase 5 has not started.

## Deliverables

- [PDF report](../paper/brainfuck-productivity.pdf) and
  [editable Markdown](../paper/report.md), covering all eleven requested academic
  sections, mathematical definitions, pseudocode, results and limitations.
- Three figures, each in SVG, PDF and 300-dpi PNG under `paper/figures/`.
  Captions specify population, cutoff, axes and unresolved-case interpretation.
- Eight [bibliographic entries](../paper/references.bib) and a
  [source-by-claim literature audit](../paper/LITERATURE_AUDIT.md).
- [Build instructions](../paper/README.md), pinned isolated dependencies,
  descriptive statistics and a source/output hash manifest.
- Reproducible plotting, PDF authoring/rendering and artifact verification
  scripts under `paper/`. Engine source and raw datasets are unchanged.

## Findings and contribution assessment

The report connects length, runtime, output, memory visitation and outcome
equivalence. Cutoff censoring hides long-running/high-output witnesses; changing
cell width changes records despite identical paired classifications in the
tested comparisons. The complete distribution reveals that 99.63% and 99.32%
of observed halted length-five/six programs finish within n instructions at the
higher cutoff, even though rare witnesses dominate maxima.

Existing research already studies Brainfuck enumeration, semantic sensitivity,
runtime records and memory records. Several prior models differ materially
from this repository's wrapping cells, left clamp and byte I/O. The paper
therefore claims a reproducible empirical artifact and methodological
demonstration, not a new search method, classical Busy Beaver result, established
record priority or exact Kolmogorov complexity.

The four length-five raw timeouts retain their separate nontermination proofs.
The 88 length-six cases remain unresolved by the runner. Literature verification
does not remove this uncertainty or constitute independent replication.

## Verification performed

- All **77 existing regression tests passed** on Python 3.13.1.
- Figure generation reconciles all **12** distributions with saved halted counts
  and runtime/output maxima, and verifies input hashes.
- `verify_paper.py` passes dataset/analysis/current-engine hash checks, all six
  primary table rows, five displayed witness replays, conditional percentages,
  tab indentation, output hashes, eight-page PDF structure and active reference
  links.
- Repeated figure/PDF builds produced byte-identical recorded artifacts in the
  tested environment. Generated text is normalized to LF for Git portability.
- All eight PDF pages were rendered and visually inspected: text, code, tables,
  figures, accented names, citations and page furniture are legible without
  clipping or overlap. A pagination overflow was corrected before delivery.
- The bibliography was checked against publisher pages, author-hosted work,
  an author-uploaded manuscript and the original software repository. Unverified
  identifiers and external benchmark claims were excluded.

Build dependencies are isolated in ignored `.venv/`. ReportLab creates the PDF;
PDFium renders review PNGs because Poppler was unavailable on the host.
The reviewed paper's editable source is Markdown, not DOCX. Review images are
ignored under `tmp/pdfs/`; final artifacts and their source are committed.
Package versions and file hashes are in
[the build manifest](../paper/build-manifest.json). Visual inspection is distinct
from automated content/integrity checking.

## Next approval checkpoint

Phase 5 is the React/Vite research website: introduction and methodology,
interactive data dashboard, bounded simulator with Python/JavaScript agreement
fixtures, responsive/accessibility checks, production build and deployment
guidance. It will use the actual versioned data and expose unresolved cases.
Implementation requires the user's next phase approval under the agreed plan.
