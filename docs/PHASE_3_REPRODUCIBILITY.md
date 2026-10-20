# Reproducing the version-one study

Use Python 3.11 or newer; the recorded runs used Python 3.13.1 on Windows.
There are no third-party execution/test dependencies. Run commands from the
repository root. The datasets identify the engine's exact committed source and
individual LF-normalized file hashes. Version 0.3.0 preserves the default
8-bit semantics and adds the separately identified 4-bit model.

## Inspect and verify existing datasets

```powershell
python generate.py dataset verify data/runs/v1/primary-n1-5-s512
python generate.py dataset verify data/runs/v1/primary-n6-s512
python generate.py dataset verify data/runs/v1/steps4096-n4-6
python generate.py dataset verify data/runs/v1/cell4-n4-6-s4096
python -B -m unittest discover -s tests -v
```

Verification reads each saved record, checks compressed-file SHA-256 hashes,
compares CSV with JSON, checks enumeration order, reconstructs metrics and
summaries, and checks complete-coverage syntax counts. It does not claim to
re-execute all programs. A missing completion manifest means an incomplete
artifact export. A `completed` manifest means export finished, not that every
program halted or every requested search completed: inspect coverage and U.

## Re-execute the study

The destinations must not already exist. The following commands create a
separate reproduction rather than overwriting the saved version-one evidence:

```powershell
python generate.py dataset run --config experiments/configs/phase3-primary-n1-5.json --output output/reproduction/primary-n1-5-s512
python generate.py dataset run --config experiments/configs/phase3-primary-n6.json --output output/reproduction/primary-n6-s512
python generate.py dataset run --config experiments/configs/phase3-steps4096-n4-6.json --output output/reproduction/steps4096-n4-6
python generate.py dataset run --config experiments/configs/phase3-cell4-n4-6.json --output output/reproduction/cell4-n4-6-s4096
```

Each run has a finite 60-second cooperative execution/export budget, no candidate
cap, and explicit tape/output/state/outcome limits. All saved runs completed
their candidate spaces within those limits. A slower machine may produce a
partial run; coverage and stopped statuses expose that difference. Increasing a
time budget is a new configuration and should be recorded as such. Do not change
instruction or cell-width settings and call the result the same experiment.

The generic `config.json` in each manifest's reproduction hint refers to that
dataset's saved configuration; use its full path from the repository root if
reproducing directly from a run folder instead of the named configuration above.

## Compare a reproduction

```powershell
python scripts/compare_reproduction.py data/runs/v1/primary-n1-5-s512 output/reproduction/primary-n1-5-s512
```

This checks exact configuration and compressed-record hashes, and compares
scientific summaries after excluding elapsed-time fields. Gzip output has fixed
header timestamps and no embedded filename. Matching records are expected only
when the same deterministic execution limits complete; wall-time interruptions
can vary. Runtime measurements, host metadata, timestamps, and manifest hashes
are not expected to be identical. The comparison reports whether the source
trees match, rather than requiring the same Git commit when only docs changed.

The recorded reproduction check is
[`data/verification/phase3-reproduction.json`](../data/verification/phase3-reproduction.json).
Its temporary duplicate dataset was removed after successful comparison.

## Rebuild analysis and evidence

```powershell
python scripts/analyze_phase3.py --runs data/runs/v1 --output output/phase3-analysis
```

Use a new output directory. This verifies all four datasets, replays all cycle
classifications and selected T/O/M witnesses, checks eight-bit witnesses against
the archived interpreter, derives runtime/output frequencies, compares paired
limit and cell-width results, and saves supplemental fresh-cell nontermination
proofs. It can take longer than one simulation because it audits two encodings
and replays evidence for nearly 900,000 candidate records across configurations.

`cycle-certificates.jsonl.gz` has one certificate per recorded cycle, including
the equal control state at two different steps. The fixed-input determinism
argument is in [SEMANTICS.md](SEMANTICS.md). Structural proofs are intentionally
restricted to four literal programs; other unresolved cases are not labeled
nonterminating by resemblance or timeout.

`data/analysis/v1/manifest.json` hashes all derived artifacts, references the
input dataset manifests, and records the analysis script hash. Rebuilding with
the same inputs and script should reproduce these deterministic analysis files.

## Data encoding

`programs.jsonl.gz` contains complete `result_record` objects, including source,
status, instruction/data pointers, steps, input position, output-byte array,
allocated tape, cycle evidence, resource reason, and derived metrics.
`programs.csv.gz` represents the same rows; tape is a compact JSON array and
output is hexadecimal bytes. Empty optional CSV fields mean null, not zero.
The program column is Brainfuck source text. Invalid-source records have no
execution metrics. `summary.csv` is the convenient small table for analysis.

Do not mix widths or budgets in a single length-only statistic. Do not convert
resource/step limits to nontermination or omit unexamined candidates from
coverage. Preserve source and configuration provenance when deriving results.
