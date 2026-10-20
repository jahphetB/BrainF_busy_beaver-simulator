# Phase 1 audit and correction report

## Scope and provenance

The original repository contained `generate.py` and `README.md`, with no tests
or machine-readable results. Both originals are preserved byte-for-byte under
`data/historical/` from commit `c86e07947ca2975375d199ae23cc18daa7f49122`.
Archived code retains its original formatting and claims for provenance; it is
not the maintained interpreter. `baseline.json` is derived from that code by
`scripts/capture_legacy_baseline.py`, independently of the refactored engine.
Its record hashes cover every valid program's status, steps, output, pointer,
and tape at both budgets. The source hash uses LF-normalized bytes so Git's
checkout line-ending conversion does not change source identity.

## Reproduced results

| Quantity | Historical budget 100 | Extended budget 512 |
| --- | ---: | ---: |
| All strings | 4096 | 4096 |
| Valid / invalid | 1514 / 2582 | 1514 / 2582 |
| Halted | 1482 | 1484 |
| Repeated-state nontermination | 30 | 30 |
| Unresolved | 2 | 0 |
| Distinct halted outcomes | 228 | 228 |
| Duplicate halted programs | 1254 | 1256 |
| Maximum observed halting steps | 4 | 512 |

The historical counts are correct for their execution budget. The two unresolved
programs, `+[+]` and `-[-]`, halt at 512 steps under the documented semantics.
Their final outcome already existed, so the number of distinct outcomes stays
228. Preserve the 100-step table rather than replacing it with the newer run.
Complete classification at length four supports a model-specific finite-search
maximum of 512, conditional on interpreter/enumeration correctness. It is not
a classical Busy Beaver value or a result about other semantics or lengths.

## Scientific corrections

- A timeout proves neither termination nor nontermination. Repeated complete
  control states do prove nontermination for fixed input; accumulating output
  need not be in that state because it does not affect control.
- "Shortest witness" means shortest among evaluated halting witnesses. With
  only length-four programs this comparison is trivial. It cannot establish
  globally shortest programs or exact Kolmogorov complexity.
- For plain complexity `C_U(x)`, a fixed decoder can interpret three bits per
  command, execute a halting program, and serialize its complete outcome.
  Consequently `C_U(x) <= 3n + c_U`. The fixed interpreter/serialization constant
  is essential; the observed raw code size is not the total universal-machine
  description size. Prefix complexity needs self-delimiting length information
  (or a known fixed length), not an unexplained `3n + constant` across all n.
- `-log2(group_size / halted_count)` is empirical surprisal conditional on this
  finite search and cutoff. It is not an estimator justified by the universal
  coding theorem and is not a measured Kolmogorov complexity.
- There are `2^k - 1` binary strings shorter than k bits. Among D distinct
  outcomes, at least `max(0, D - (2^k - 1))` require descriptions of at least k
  bits under any fixed binary description machine. With D=228 and k=7, this
  gives 101 outcomes. It does not identify those outcomes. `log2(228)` is about
  7.83, not 7; the integer threshold is a separate counting statement.
- Allocated trailing zeros are part of the original outcome definition. This
  captures some visitation history as well as memory values. Output bytes and
  tape values are different objects and must not be combined into output size.

## Engineering findings and Phase 1 treatment

| Finding | Treatment |
| --- | --- |
| Experiment executes on import | Guarded compatibility entry point and separate CLI. |
| Duplicate tracing interpreter | One step implementation, immutable before/after snapshots. |
| Brackets searched on each jump | Validate and construct one bracket map per execution. |
| Linear state/group scans | Exact tuple keys in dictionaries. Tape snapshots remain a scalability cost. |
| Empty input hardcoded; output stored as text | Byte input API and byte output, with explicit compatibility conversion. |
| Invalid direct interpreter inputs have accidental behavior | Validate syntax before execution; distinguish configuration errors. |
| README lists nonexistent functions | Document actual package modules and commands. |
| No tests or preserved baseline | Independent archived implementation, baseline hashes, semantic fixtures, differential tests. |

The original grouping string was not demonstrated to collide for valid outputs:
its final numeric fields can be separated from the right. Structured tuple keys
are a clearer representation, not a claimed fix for an observed collision.

## Remaining limitations

Phase 1 remains a small length-four study. Full tape snapshots and retained
execution records are unsuitable for unrestricted large searches. Memory,
output, and wall-clock budgets; broader metrics; benchmark-based feasibility;
versioned experiment datasets; literature review; paper; and website remain
future phases. No novelty or practical compression benefit is claimed.

The original and refactored interpreters agreeing is strong regression evidence,
not independent proof of all semantics. Hand-derived fixtures and modular
arithmetic checks complement the differential tests.

## Background references

- [Brainfuck reference](https://brainfuck.org/brainfuck.html), Daniel B. Cristofani.
- [Algorithmic complexity](https://www.scholarpedia.org/article/Algorithmic_complexity),
  Scholarpedia: plain/prefix distinctions and description-machine dependence.

A comprehensive related-work and novelty assessment is reserved for Phase 4.
