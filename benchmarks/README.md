# Phase 2 performance and feasibility pilot

This directory contains engineering measurements, not publication research
datasets. The source runner is `benchmark_engine.py`; the measured result is
`phase2-pilot.json`. The small exhaustive validation report is
`phase2-validation.json`.

## Reproduce

```powershell
python -B benchmarks/benchmark_engine.py --output benchmarks/another-pilot.json
```

The output filename must be new. Defaults: three repeats, up to 2048 uniformly
sampled candidate ranks per length, fixed seed 20261019, and a 512-instruction
budget. Small spaces with at most 2048 candidates are enumerated completely.
Lengths 4-7 are sampled; the separate length-four regression/timing run is
exhaustive. Rank hashes allow the sampled workloads to be checked exactly.
Each sampled execution is capped at one second and each repetition at 30 seconds;
exceeding a time budget aborts the pilot rather than producing a misleading
complete projection. All sampled repetition summaries must agree.

The report captures actual Python/OS information, Git HEAD and dirty state, a
normalized source fingerprint, individual timings, resource configuration,
sample-only classifications, and limitations. `source_sha256` covers maintained
package code, `generate.py`, `pyproject.toml`, and the benchmark script. The saved
run was measured before the Phase 2 runner commit, so its recorded dirty state is
intentional; the source fingerprint identifies exactly what was measured.

## Measured performance

On the recorded Python 3.13.1 / Windows environment:

| Workload | Median elapsed time |
| --- | ---: |
| Archived original, all 1514 valid length-four programs, budget 512 | 0.05574 s |
| Current core with resource limits, same valid programs and budget | 0.01456 s |
| Current full streaming length-four runner, all 4096 candidates | 0.05599 s |

The core comparison gives a **3.83x** ratio on this workload, relative to the
original archived implementation, not relative to Phase 1. The full runner adds
invalid-source validation, budget setup, aggregation, and coverage reporting, so
its timing should not be substituted for the core-only comparison. No general
speedup claim follows from one small workload.

Separate `tracemalloc` runs measured peak traced Python allocations of
1,528,448 bytes for the materialized baseline versus 67,855 bytes for streaming
the same length-four search. This is not process RSS or the logical byte budgets
used for resource enforcement. Tracing allocation overhead is excluded from the
reported timing runs.

## Larger-length feasibility

| Length | Raw candidates | Valid candidates (exact count) | Sampled candidates | Median linear time projection |
| --- | ---: | ---: | ---: | ---: |
| 5 | 32768 | 9996 | 2048 | 0.42 s |
| 6 | 262144 | 67181 | 2048 | 3.35 s |
| 7 | 2097152 | 458562 | 2048 | 43.44 s |

These projections scale measured sampled execution+aggregation time by search
size. They exclude sample construction and file output. The length-seven repeat
projections ranged from approximately 26.06 to 47.84 seconds due to timing
variation; this is **not a confidence interval**. Samples can miss rare expensive
programs. The 512-step budget itself leaves some sampled programs unresolved.
Higher step budgets, larger outputs, and whole-search outcome growth require
new cost estimates. For perspective, length seven has an instruction-budget
ceiling of 234,783,744 at this cutoff, using its exact valid-syntax count.

No exhaustive length-five, six, or seven run was executed in Phase 2. For Phase 3,
start with length five, then six, under a finite 30-second experiment budget and
the documented storage caps. Inspect actual timing, unresolved counts, and
output sizes before expanding. Consider length seven separately with a larger
explicit time budget after those measurements; the default 30 seconds may not
complete it. A completed search still does not resolve step-limited programs.
