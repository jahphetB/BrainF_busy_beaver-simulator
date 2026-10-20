# Brainfuck Computational Productivity Research

**From Short Programs to Complex Computation: An Empirical Study of Brainfuck Program Length, Runtime, and Output Productivity**

This project studies how short Brainfuck programs use execution time, output,
and memory under explicitly defined semantics. It extends the original
length-four experiment. It does not solve the classical Busy Beaver problem or
compute exact Kolmogorov complexity.

**Status:** Phases 1 and 2 are implemented and validated. The engine supports
bounded streaming experiments for lengths 1-7. Publication datasets, expanded
experiments, the research paper, and the interactive website remain later phases.

## Run the validated baseline

Requires Python 3.11 or newer. Validated locally with Python 3.13.1. No runtime
or test dependencies need installation. Run from the repository root:

```powershell
python generate.py
python generate.py --max-steps 512
python generate.py --max-steps 512 --json
python -B -m unittest discover -s tests -v
```

The default command preserves the historical **100-step** experiment. The JSON
option prints a structured summary with version, semantics, configuration,
classification counts, and witnesses; it is not a full per-program dataset.

Trace a program through the same interpreter:

```powershell
python generate.py --trace '>>>+'
python generate.py --trace ',.,.' --input-hex ff41
python generate.py --trace '+[+]' --max-steps 512
```

Tracing is opt-in; imports no longer execute experiments or print traces.
`generate.run_program(program, max_steps)` retains the original five-item tuple
for valid command-only programs. New code uses the package's structured result.

## Verified length-four results

All 4096 strings over `><+-.,[]` are considered. Exactly 1514 are syntactically
valid and 2582 are invalid.

| Measurement | Historical 100-step limit | Extended 512-step limit |
| --- | ---: | ---: |
| Proven halted | 1482 | 1484 |
| Proven nonterminating by repeated state | 30 | 30 |
| Unresolved after step limit | 2 | 0 |
| Distinct halted outcomes | 228 | 228 |
| Duplicate halted programs | 1254 | 1256 |
| Maximum observed halting steps | 4 | 512 |

The two previously unresolved programs, `+[+]` and `-[-]`, each halt after
**512 executed instructions** with no output and a zero cell. Each performs
255 arithmetic loop iterations: `1 + 1 + 255 * 2 = 512`. A cutoff of 511 still
leaves the closing bracket unexecuted. Both outcomes were already represented,
so resolving these programs adds no distinct outcome.

The 100-step results remain valid historical observations. Complete
classification at length four supports a finite-model maximum of 512,
conditional on the implementation and enumeration being correct. This is not
an exact classical Busy Beaver value, a general halting algorithm, or a result
about other semantics or lengths.

## Execution model

`legacy-u8-right-v1` uses 8-bit wrapping cells, a right-growing zero-initialized
tape, a clamped left boundary, byte I/O, and EOF writing zero. Primary baseline
input is empty. Every executed command costs one step. A nonzero `]` continues
after its matching `[`, so the opening bracket is not re-executed on each
iteration. Research source must contain only commands and valid brackets.

A halted outcome consists of output bytes, final pointer, and the entire
allocated tape, including trailing zeros. Output is separate from memory.
A repeated control state proves nontermination; reaching a step limit does not.

See [the full semantics](docs/SEMANTICS.md) for ordering at cutoffs, the cycle
argument, input handling, and outcome equivalence.

## Architecture

| File or directory | Responsibility |
| --- | --- |
| `generate.py` | Checkout-friendly CLI and legacy tuple adapter; no import-time experiment. |
| `src/brainfuck_research/syntax.py` | Strict source validation and bracket maps. |
| `src/brainfuck_research/interpreter.py` | Execution, cycle evidence, and shared trace logic. |
| `src/brainfuck_research/models.py` | Immutable states, results, and trace events. |
| `src/brainfuck_research/enumeration.py` | Lazy length 1-7 enumeration, direct ranks, and exact syntax counts. |
| `src/brainfuck_research/analysis.py` | Outcome groups and descriptive statistics. |
| `src/brainfuck_research/config.py` | Validated execution and experiment budgets. |
| `src/brainfuck_research/experiments.py` | Baseline and streaming searches, coverage, and cost preview. |
| `src/brainfuck_research/export.py` | JSON-safe records and summaries. |
| `src/brainfuck_research/cli.py` | Command-line options and presentation. |
| `src/brainfuck_research/experiment_cli.py` | Bounded experiment configuration and JSONL export. |
| `experiments/configs/` | Reproducible experiment settings. |
| `benchmarks/` | Measured performance, engineering validation, and feasibility pilots. |
| `tests/` | Semantic, differential, analysis, and CLI tests. |
| `tests/fixtures/semantics.json` | Hand-derived cases for future Python/JavaScript parity. |
| `data/historical/` | Original code/README and independently reproduced baseline hashes. |
| `scripts/capture_legacy_baseline.py` | Baseline reproduction using only archived code. |

## Scientific interpretation

A halting program provides a description of its outcome under a specified
interpreter and encoding; it does not establish that the description is
shortest. Three bits encode each command, but universal-machine description
bounds include decoder overhead and require plain/prefix complexity to be
distinguished. Conditional outcome frequency is empirical surprisal, not exact
Kolmogorov complexity. No novelty or compression advantage is claimed.

Read [the audit and correction report](docs/AUDIT.md),
[reproduction instructions](docs/REPRODUCIBILITY.md), and
[the approved five-phase plan](docs/PLAN.md).

## Bounded experiments and performance

```powershell
python generate.py experiment --config experiments/configs/phase2-validation.json
python generate.py experiment --lengths 5 6 7 --exhaustive --estimate
python generate.py experiment --lengths 5 --max-programs 1000 --max-seconds 10
```

The first command validates lengths 1-4. The second estimates candidate and
instruction ceilings **without executing programs**. The third evaluates a
bounded alphabet-order prefix, not an unbiased sample. Defaults limit candidates,
wall time, tape, output, state history, and retained outcomes. Use `--report` and
`--records` with new filenames to save JSON summaries and streamed JSONL records.

Summaries report maximum halted runtime T, output O, visited cells M, distinct
halted outcomes D, and evaluated unresolved programs U. Unexamined candidates
are counted separately. Incomplete coverage or unresolved programs produces
observed lower bounds. Resource limits are not nontermination proofs.

See [the experiment guide](docs/EXPERIMENTS.md) for metric definitions, budgets,
configuration, and export commands. **61 tests pass**, including the historical
baseline comparisons. [Measured benchmarks](benchmarks/README.md) show a 3.83x
core timing ratio versus the archived original on the tested length-four workload;
streaming also substantially reduces traced Python allocation peaks.

## Current limits and next phase

Exhaustive searches through length four are validated. Lengths 5-7 have only
bounded benchmark samples so far. Time limits are cooperative, and state/outcome
byte budgets measure retained payloads rather than total process memory. Pilot
runtime projections can miss rare expensive programs and do not extrapolate to
larger step limits. [Phase 3](docs/PHASE_2.md) requires approval before expanding
the research experiments and publishing versioned datasets.

There is no website deployment or live URL yet.
