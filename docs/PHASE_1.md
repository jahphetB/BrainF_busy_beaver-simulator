# Phase 1 completion record

Validated on 2026-10-19 with Python 3.13.1.

## Delivered

1. Preserved original source and README, independent baseline capture, and
   per-program evidence hashes for budgets 100 and 512. Documented execution
   semantics, outcome equivalence, scientific corrections, and the approved plan.
2. Separated syntax, execution, immutable models, enumeration, analysis,
   configuration, orchestration, serialization, and command-line presentation.
   Preserved the default baseline command and the legacy valid-program tuple
   adapter. Traces now use the same core as normal execution.
3. Added 30 automated tests, including 18 shared hand-derived semantic fixtures,
   3028 valid-program differential comparisons, independent modular arithmetic,
   historical group-membership checks, and CLI behavior.

## Verification

`python -B -m unittest discover -s tests -v`: 30 tests passed.

Both historical and extended baseline summaries match the archived program:
1482/1484 halted, 30/30 proven cycles, 2/0 unresolved, 228/228 distinct outcomes,
and maximum observed halting steps 4/512. The values correspond to budgets
100/512, respectively. Both `+[+]` and `-[-]` halt at exactly 512 instructions.

No scientific discrepancy remains in the historical counts. The earlier
README's interpretation and API descriptions needed correction. Existing
unmatched-bracket direct calls and non-command input had unspecified accidental
behavior; the research API now rejects these before execution. Original source
is archived with its original formatting; maintained code uses tabs.

## Next approval checkpoint

Phase 2: configurable enumeration for lengths 1-7, additional measurements,
resource limits, and benchmarks. Estimate costs before approving expensive
exhaustive runs. No Phase 2 work is included in this completion record.
