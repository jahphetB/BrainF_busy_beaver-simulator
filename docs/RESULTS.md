# Phase 3 experimental results

The version-one study exhaustively considers candidate strings through length
six under explicitly bounded execution. It compares instruction budgets and
cell width. Exhaustive candidate coverage does **not** imply every valid program
has been resolved. All records, including syntax-invalid candidates, are saved.

Primary semantics are `legacy-u8-right-v1`: wrapping 8-bit cells, right-growing
tape, clamped left boundary, empty input with EOF-zero, and the documented
instruction-counting convention. The cell-width comparison uses `u4-right-v1`.

## Primary experiment: 512 instructions

| Length | Candidates | Halted | Proven cycles | Unresolved U | T | O | M | D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 8 | 6 | 0 | 0 | 1 | 1 | 2 | 5 |
| 2 | 64 | 37 | 0 | 0 | 2 | 2 | 3 | 19 |
| 3 | 512 | 232 | 2 | 0 | 3 | 3 | 4 | 67 |
| 4 | 4096 | 1484 | 30 | 0 | 512 | 4 | 5 | 228 |
| 5 | 32768 | 9638 | 322 | 36 | 511 | 5 | 6 | 760 |
| 6 | 262144 | 63713 | 2988 | 480 | 512 | 6 | 7 | 2500 |

T/O/M are maximum observed halting steps, output bytes, and visited cells among
halted programs. D counts distinct halted outcomes. Invalid syntax is excluded
from the halted/cycle/unresolved columns; the complete classification counts are
in the downloadable summaries. Every row has complete candidate coverage.

The original 100-step length-four result remains documented and reproducible;
it is not overwritten by these experiments.

## Instruction-limit sensitivity: 4096 instructions

| Length | Halted | Proven cycles | Unresolved U | T | O | M | D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 1484 | 30 | 0 | 512 | 4 | 5 | 228 |
| 5 | 9670 | 322 | 4 | 767 | 255 | 6 | 764 |
| 6 | 64077 | 3016 | 88 | 1026 | 510 | 7 | 2536 |

Of the 36 previously unresolved length-five cases, 32 halt with the higher
budget and four remain step-limited. Of the 480 length-six cases, 364 halt,
28 yield a repeated-state proof, and 88 remain step-limited. No program in these
runs stopped for another resource limit. The dataset records these transitions
individually in `data/analysis/v1/sensitivity.json`.

The 512-step cutoff makes observed T decrease from length four to five even
though longer halting witnesses exist. For example, `+[+].` needs 513 steps and
is excluded from that cutoff's halted records. This is a censoring effect of
the experiment, not evidence that larger programs intrinsically do less work.
Increasing the cutoff also reveals 255- and 510-byte outputs that the primary
experiment misses. Runtime and output conclusions are therefore limit-dependent.

## Cell-width sensitivity at the same 4096-step limit

| Length | 8-bit T | 4-bit T | 8-bit O | 4-bit O | M in both | D in both | U in both |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 512 | 32 | 4 | 4 | 5 | 228 | 0 |
| 5 | 767 | 47 | 255 | 15 | 6 | 764 | 4 |
| 6 | 1026 | 66 | 510 | 30 | 7 | 2536 | 88 |

Matched per-program comparison finds identical classifications at this cutoff,
not merely equal aggregate totals. Among programs halted in both models, runtime
changes for 2 length-four, 34 length-five, and 398 length-six programs. Equal D
counts do not imply equal outcome values: byte values and generated outputs can
differ. These observations apply only to the evaluated widths, lengths, and
cutoff; they are not a theorem about arbitrary widths or longer programs.

## Replayable witnesses and productivity

| Program | Length | 8-bit halting steps | Output bytes | Role |
| --- | ---: | ---: | ---: | --- |
| `+[+]` | 4 | 512 | 0 | Runtime record; wraps cell 1 back to zero. |
| `+[<+]` | 5 | 767 | 0 | Runtime record; left-boundary no-op adds work. |
| `+[+.]` | 5 | 767 | 255 | Output record; each iteration emits one byte. |
| `+[<>+]` | 6 | 1026 | 0 | Runtime record; increments a second cell through a full wrap. |
| `+[+..]` | 6 | 1022 | 510 | Output record; emits two bytes per iteration. |

The complete witness file includes final tape, pointer, actual output bytes,
metrics, and the roles of each selected example. Tied programs exist; the table
does not imply these witnesses are unique.

For b-bit cells, `+[<+]` executes `2 + 3*(2^b - 1)` instructions. For `+[<>+]`,
the first `<` is clamped, `>` enters an initially zero second cell, and the
four-instruction loop body executes `2^b` times: `2 + 4*2^b`. These give 767/47
and 1026/66 steps at eight/four bits. `+[+.]` emits `2^b - 1` bytes and
`+[+..]` emits twice that number. Both finish with a zero cell; their output is
not their final tape. Independent arithmetic regression tests cover these counts.

At eight bits, the length-five records give 153.4 steps and 51 output bytes per
source command; length six gives 171 steps and 85 output bytes per command.
The maximum-runtime and maximum-output witnesses at length six differ. The
saved `runtime-output.csv` distribution contains actual halted-program counts
for every observed (runtime, output) pair, enabling later trade-off analysis.

Observed maximum halted memory visitation is n+1 in these runs, witnessed by
moving right n times. This is an observation about halted executions; it is not
a general upper bound on the memory a length-n program can visit.

## Termination and nontermination evidence

Every one of the **10,078 cycle classifications across configurations** was
replayed. The compressed certificates record the program/model, first and
repeated step, period, equal control state, and bytes emitted during the cycle.
Under deterministic fixed-input execution, equality of instruction pointer,
data pointer, allocated tape, and input position forces repeating control
behavior. Accumulated output need not match because it cannot affect execution.

The four length-five programs still step-limited at 4096 are:

```text
+[>+]
+[>-]
-[>+]
-[>-]
```

They have a separate nontermination proof on the right-unbounded tape. The
initial sign makes cell zero nonzero. Each iteration moves right to a fresh
zero cell and changes it by one modulo the cell range. That new cell is always
nonzero, so `]` jumps back to `>`. Induction shows continued rightward movement
and no loop exit. This works for both tested cell widths, while the continuously
growing tape prevents an exact repeated-state certificate.

These supplemental proofs are saved separately. Raw runner classifications and
U are preserved, rather than silently rewriting a step-limit observation into
a cycle result. Thus the four length-five cases are known nonterminating by
this additional argument; the 88 length-six cases retain their unresolved
runner classification and have not received a complete proof analysis. Headline
records remain labeled as observed values; no classical Busy Beaver value is
claimed.

## Verification and provenance

- All **897,608 candidate records across four configurations** passed checksum,
  CSV/JSON agreement, enumeration-order, exact syntax-total, and summary-accounting
  checks. This count includes repeated candidates across configurations and invalid
  syntax; it is not a count of distinct executed programs.
- All 33 selected maximum-witness records were replayed. The 24 eight-bit
  witnesses also agree with the archived original interpreter. Four-bit witness
  counts have independent arithmetic tests; the archived code does not implement
  four-bit cells.
- All 10,078 recorded cycles have replayed repeated-state certificates.
- A fresh reproduction of the 37,448-record lengths 1-5 dataset produced identical
  compressed JSONL and CSV hashes and identical scientific summaries. Timings and
  timestamped manifests naturally differ.
- Every dataset identifies engine version 0.3.0 and committed source
  `8a7ce03825edaac753f809a62c0ee5b7596bb9bb`, with matching engine-file hashes.

See [reproduction instructions](PHASE_3_REPRODUCIBILITY.md),
[dataset index](../data/README.md), and
[machine-readable verification](../data/analysis/v1/verification.json).

## Limits and contribution status

Execution/export took approximately 2.38 seconds for primary lengths 1-5,
15.97 seconds for primary length six, 19.06 seconds for the higher-limit
comparison, and 18.27 seconds for the four-bit comparison on the recorded host.
These are measured run times, not general performance guarantees; manifest
setup, final file closure, and verification are outside the runner timer.

Length seven was deferred. The observed length-six export cost alone suggests
roughly two minutes under a simple eightfold extrapolation, with additional
uncertainty from rare costly programs. Investigating execution-limit effects
through length six was more useful within this phase's bounded run plan. No
length-seven research dataset or convergence claim is made.

Only two cell widths, empty input, one pointer-boundary rule, and one outcome
equivalence definition were studied. Time budgets are cooperative. Memory caps
measure retained payload rather than process RSS. Exhaustive enumeration and
cross-checks reduce implementation risk but are not formal verification. Data
integrity verification is distinct from independently rerunning all executions.

These are reproduced baseline findings and newly measured observations in this
repository. The completed [Phase 4 paper](../paper/report.md) compares them with
verified prior Brainfuck enumeration and Busy Beaver work. The defensible
contribution is a reproducible empirical artifact, with explicit semantics,
paired comparisons and preserved uncertainty. Research priority or a new record
is **not established**. No exact Kolmogorov complexity or compression improvement
is inferred. See the [literature audit](../paper/LITERATURE_AUDIT.md).

Phase 4's complete distribution analysis additionally finds that 9634/9670
(99.63%) and 63641/64077 (99.32%) observed halted programs finish within their
source length in instructions at lengths five/six, respectively (8-bit, B=4096).
These are descriptive fractions conditional on observed halting. They are not
eventual halting probabilities or evidence resolving the remaining programs.
The reproducible calculation is in [paper/statistics.json](../paper/statistics.json).
