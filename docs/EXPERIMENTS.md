# Phase 2 experimental engine

The default `python generate.py` command still reproduces the original
100-step length-four baseline. Use the separate `experiment` command for
streaming searches with resource limits. No third-party dependencies are needed.

## Reproduce the small validation run

```powershell
python generate.py experiment --config experiments/configs/phase2-validation.json
python generate.py experiment --config experiments/configs/phase2-validation.json --json
python -B -m unittest discover -s tests -v
```

This covers lengths 1-4 at 512 steps per program with empty input. The
configuration records every budget, including the total 30-second cooperative
deadline. The measured engineering validation is preserved in
[`benchmarks/phase2-validation.json`](../benchmarks/phase2-validation.json).

| Length | T | O | M | D | U |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 1 | 2 | 5 | 0 |
| 2 | 2 | 2 | 3 | 19 | 0 |
| 3 | 3 | 3 | 4 | 67 | 0 |
| 4 | 512 | 4 | 5 | 228 | 0 |

These are validation results under one model and one instruction budget, not a
novelty claim or the completed Phase 3 experimental study. Original 100-step
results and independent archived-code regression tests remain intact.

## Metrics and uncertainty

For evaluated programs of exactly length n:

- **T(n):** maximum executed instructions among proven halted programs.
- **O(n):** maximum actual output bytes among proven halted programs.
- **M(n):** maximum distinct cells visited among proven halted programs,
  including the initial cell.
- **D(n):** distinct halted outcomes: output bytes, final pointer, and complete
  allocated tape, including trailing zeros.
- **U(n):** evaluated valid programs stopped by the instruction budget or
  another execution resource limit. Both classes remain unresolved.

T/O/M are null when there is no halted witness. D and U can be zero even for
an empty evaluated prefix; this does not imply that the unevaluated search space
has no outcomes or unresolved programs. `coverage.not_evaluated_candidates`
always reports candidates that were never executed or syntax-classified.

Every valid record also includes final nonzero cells, the final tape, output
bytes, steps/source-length and output-bytes/source-length ratios. These describe
the observed prefix for interrupted executions; only halted executions contribute
to T/O/M/D. Nonzero-cell count is a final-state measurement, not a peak.

Summaries store one replayable witness and a tie count per maximum, rather than
an unbounded list of ties. The maximum ratios are T/n and O/n within each length.
Counts include every evaluated candidate exactly once. `exhaustive` means all
`8^n` candidates were considered; `fully_resolved` additionally requires U=0.
Incomplete coverage or U>0 labels productivity records as observed lower bounds.
Even a complete result applies only to the documented finite model and length.

## Preview cost without running a search

```powershell
python generate.py experiment --lengths 5 6 7 --exhaustive --max-steps 512 --estimate
```

`--estimate` never invokes the interpreter. It reports raw and valid candidate
counts and an instruction-budget ceiling, not a runtime forecast. For k bracket
pairs, choose their positions, choose one balanced Catalan bracket sequence, and
fill other positions with six non-bracket commands:

`valid(n) = sum(comb(n, 2k) * Catalan(k) * 6^(n - 2k))`.

The formula is checked against small exhaustive enumeration and an independent
prefix-depth counting recurrence through length seven.

## Configure bounded runs

```powershell
python generate.py experiment --lengths 5 --max-programs 1000 --max-steps 512 --max-seconds 10
python generate.py experiment --lengths 4 --max-tape-cells 4 --max-output-bytes 2 --json
```

The first command evaluates an alphabet-order prefix, not a random sample.
Do not interpret its classification fractions as unbiased population estimates.
Use increasing, unique lengths between 1 and 7. `--exhaustive` removes only the
candidate cap: other budgets still apply, and the result can remain partial.
JSON configuration and budget flags cannot be mixed, avoiding hidden overrides.

| Budget | Default | Scope |
| --- | ---: | --- |
| `max_steps` | 512 | Executed instructions per program. |
| `max_programs_per_length` | 10000 | Includes invalid candidates; null removes this cap. |
| `max_seconds` | 30 | Whole experiment; finite and positive. |
| `max_distinct_outcomes` | 100000 | Retained exact outcome keys per length. |
| `max_outcome_bytes` | 16777216 | Retained output+tape byte payload per length. |
| `limits.max_tape_cells` | 4096 | Allocated cells per program. |
| `limits.max_output_bytes` | 65536 | Output buffer per program. |
| `limits.max_seen_states` | 100000 | Stored control-state keys per program. |
| `limits.max_state_bytes` | 16777216 | Sum of stored control-state tape payloads. |
| `limits.max_seconds` | null | Optional program deadline, always clamped to remaining experiment time. |

Limits stop observations without changing cell arithmetic or the tape model.
The order of checks is documented in [SEMANTICS.md](SEMANTICS.md). State and
outcome byte budgets measure payload, not Python object overhead or process RSS.
Separate entry-count caps bound metadata growth. Tape/output snapshots create
bounded temporary copies. Deadlines are checked cooperatively, so configuration,
syntax, aggregation, filesystem I/O and operating-system delays can overshoot
the nominal wall-clock budget. This is not a hard operating-system sandbox.

When a new halted outcome would exceed retained storage, the runner counts that
known-distinct outcome without retaining its key and immediately stops that
length. D therefore stays exact for the evaluated prefix, with
`unretained_final_distinct_outcome=true`. The halted result is still counted and
exported. No later results are compared against an incomplete set. Repeated
outcomes at the storage cap do not require new keys. Budgets reset per length;
the global deadline does not reset.

## Stream results to disk

```powershell
python generate.py experiment --lengths 4 --report summary.json --records records.jsonl
```

Use new filenames; existing outputs are never overwritten. Parent directories
must already exist. JSONL writes one evaluated record per line, including invalid
source, resource reasons, metrics, and final state. It does not accumulate a result
list in memory. JSON encodes output as integer byte arrays. Output files can grow
large, so estimate work and use bounded configurations before exporting larger
searches. I/O failure aborts the command; incomplete files are not completed runs.
The summary is written only after execution succeeds.

Phase 3 will add publication datasets, provenance manifests, checksums, limit
sensitivity experiments, and expanded record investigations.

## Architecture and validation

`config.py` validates budgets; `enumeration.py` streams candidates and supports
direct rank decoding for benchmarks; `interpreter.py` executes with limits;
`StreamingSummary` aggregates exact counts with bounded storage; `experiments.py`
tracks coverage and deadlines; `experiment_cli.py` loads settings and streams
`export.py` records. The original materialized baseline is kept for compatibility
and regression testing only.

61 tests passed on Python 3.13.1, including the original 3028 valid-program
differential comparisons, resource boundaries, accounting, replayed T/O/M
witnesses, storage-cap duplicates, deterministic deadline tests, configuration
validation, and JSON/JSONL integration. One Windows sandbox run denied temporary
directory access; the export test and full suite passed when run with permission.
