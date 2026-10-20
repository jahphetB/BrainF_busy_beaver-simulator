# Phase 2 completion record

## Delivered

1. Configurable lazy enumeration for lengths 1-7, direct candidate-rank decoding,
   exact valid-syntax counts, JSON settings, and a no-execution cost preview.
2. Executed-step/output/visited-cell/final-nonzero measurements and productivity
   ratios; T/O/M/D/U summaries; replayable record witnesses; explicit tape,
   output, state-history, deadline, candidate, and outcome-storage budgets.
3. Bounded streaming aggregation and JSONL export, byte-based tape storage,
   elimination of unnecessary cycle history for loop-free source, and measured
   performance/feasibility pilots with reproducible sampling and source hashes.

The original semantics and 100/512-step length-four results remain unchanged.
Configuration/output controls stop evaluation; they do not turn resource limits
into proof of nontermination. Unexamined candidates are reported separately.

## Verification

`python -B -m unittest discover -s tests -v`: **61 tests passed** on Python 3.13.1.
This includes the preserved 3028 independent valid-program comparisons and
additional limit, metric, streaming, deadline, combinatorial-count, export, and
record-replay checks. A sandbox filesystem restriction affected one temporary-file
test; the test and full suite passed with the required filesystem permission.

The small validation run covers lengths 1-4 at 512 steps. Length four reproduces
T=512, O=4, M=5, D=228, U=0. The saved benchmark measures a 3.83x core timing
ratio versus the original archived interpreter on valid length-four programs,
and much lower traced allocation peaks for the streaming runner. See
[benchmark methodology and limitations](../benchmarks/README.md).

No exhaustive search for lengths 5-7 was run. Their benchmark observations come
from fixed-seed samples, not complete research datasets. No new theoretical
maximum, novelty, or publication claim is made.

## Next phase, awaiting approval

Phase 3 will execute progressively larger feasible experiments, export versioned
research datasets and provenance, replay records, and compare limits/semantics.
Begin with lengths five and six at 512 steps under documented time/storage
budgets, then examine actual cost and unresolved programs before increasing
cutoffs or attempting length seven. Sample projections are not guaranteed times.
