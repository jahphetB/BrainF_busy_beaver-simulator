# Research paper and figure reproduction

Read [the eight-page PDF](brainfuck-productivity.pdf) or edit
[the Markdown manuscript](report.md). The PDF is generated from that manuscript;
there is no second copy of its prose in the renderer.

The report includes the required academic sections, explicit metric definitions,
pseudocode, sensitivity comparisons and limits. The [literature audit](LITERATURE_AUDIT.md)
maps claims to verified sources; [BibTeX](references.bib) provides editable
bibliographic records. This is a research report, not a claim of peer review or
a new Busy Beaver record.

## Build on Windows

Use Python 3.13.1 for the validated environment. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r paper/requirements.txt
.venv\Scripts\python.exe -B paper/make_figures.py
.venv\Scripts\python.exe -B paper/build_paper.py
.venv\Scripts\python.exe -B paper/verify_paper.py
```

On other platforms substitute `.venv/bin/python`. The dependency lock records
the tested versions; another platform/Python version has not been verified.
Dependencies are isolated from the standard-library-only research engine.
Internet access is needed to install packages, not to build from saved data.

The figure generator checks its input hashes and validates all 12 distributions
against saved halted counts and maxima. It writes three figures in vector SVG
and PDF, plus 300-dpi PNG for embedding. [statistics.json](statistics.json)
contains additional descriptive fractions, with their input hashes.

The PDF builder supports the manuscript's headings, paragraphs, inline emphasis,
code, tables, web links, figures and explicit pagebreak comments. It embeds fonts
bundled with Matplotlib. It deliberately rejects a result outside eight pages.
After editing, check each rendered page under ignored `tmp/pdfs/`; adjust prose
or page breaks when necessary. PDFium renders locally because Poppler was not
available on the validated Windows host. The recorded visual review covered all
eight pages; extraction checks alone do not verify layout.

[build-manifest.json](build-manifest.json) records source/output hashes and package
versions. The verifier checks saved dataset hashes, current engine-source
agreement, distributions, both manuscript tables, witness execution, active PDF
reference links, and the build hashes. It does not audit every sentence or prove
an external reference true; those checks are documented in the literature audit
and Phase 4 report. Same-environment rebuild determinism is checked separately.

## Figure interpretation

| Figure | Saved source | Interpretation |
| --- | --- | --- |
| 01-records | `data/analysis/v1/summary.csv` | Runtime/output maxima versus length; logarithmic axes; three configurations. |
| 02-runtime-output | `data/analysis/v1/runtime-output.csv` | Every observed halted runtime/output pair at lengths 5/6, 8-bit, B=4096; color is multiplicity. Symmetric-log axes retain zero output. |
| 03-memory-outcomes | `data/analysis/v1/summary.csv` | Halted visited cells and distinct outcomes; B=512 for n=1..3, B=4096 for n=4..6. |

All figures are descriptive. Incomplete execution classification can censor
extrema even when candidate enumeration is exhaustive. The four length-five
timeouts have separate nontermination proofs; 88 length-six cases retain
unresolved runner status. Equal D across widths does not imply identical outputs.

Recreating raw experiments and certificates is a separate operation documented
in [Phase 3 reproduction](../docs/PHASE_3_REPRODUCIBILITY.md). The paper build does
not rerun those expensive steps or modify historical research data.
