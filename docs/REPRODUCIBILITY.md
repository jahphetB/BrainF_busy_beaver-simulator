# Reproducing Phase 1

This guide preserves Phase 1 reproduction. For the completed Phase 2 runner,
limits, streaming exports, and benchmarks, see [EXPERIMENTS.md](EXPERIMENTS.md).

## Environment and provenance

Run from the repository root with Python 3.11 or newer. The Phase 1 local
validation used Python 3.13.1 on Windows. There are no third-party runtime or
test dependencies. The CLI bootstraps the `src/` package for a fresh checkout;
tests do the same. Packaging metadata also lives in `pyproject.toml`.

The source experiment is commit `c86e07947ca2975375d199ae23cc18daa7f49122`.
`data/historical/original_generate.py` and `original_README.md` preserve that
version. Git normalizes text line endings; the baseline's source SHA-256 also
normalizes CRLF to LF. No other source normalization is performed.

## Commands

```powershell
python --version
python generate.py
python generate.py --max-steps 512
python generate.py --max-steps 512 --json
python -B -m unittest discover -s tests -v
git diff --check
```

The first experiment defaults to 100 steps, exactly four commands, the alphabet
`><+-.,[]`, and empty input. The second changes only the execution budget.
Both use `legacy-u8-right-v1`. The JSON summary contains these settings and the
engine version. It deliberately has no generated timestamp, making repeated
summary output deterministic. Full versioned experiment datasets, timing, and
environment manifests will be added in Phase 3.

To print independently reproduced historical evidence:

```powershell
python -B scripts/capture_legacy_baseline.py
```

This command runs the archived script rather than importing the new engine.
It prints the same JSON object as `data/historical/baseline.json`. The test
suite verifies exact parsed equality. Preserve the frozen baseline; do not
regenerate it from a changed interpreter to make a failing test pass.

## What the tests establish

- 4096 unique length-four candidates in the original order, including invalid
  strings; 1514 valid executions at each of two budgets.
- All 3028 valid execution results agree with the archived interpreter on
  status, executed steps, output bytes, pointer, and complete allocated tape.
- Record hashes and summary counts match independently captured historical
  evidence. Every historical outcome group's membership also agrees.
- 18 hand-derived JSON cases cover wrapping, byte I/O, EOF, left boundaries,
  allocation, skipped and nested loops, step/cycle cutoff precedence, input
  position, and both 512-step programs.
- Independent modular arithmetic verifies why those two loops need 512 steps.
- Trace snapshots agree with ordinary execution and are immutable. Cycle
  start/period evidence identifies equal control states, even with new output.
- Invalid syntax/configuration, unresolved tape growth, outcome equivalence,
  JSON output, CLI errors, and import-time behavior are exercised.

These are regression and semantic checks, not a formal verification of the
Python runtime or a proof that every possible Brainfuck source is implemented
correctly. The archived interpreter is independent code but has the same
historical design; hand-derived cases provide complementary evidence.

## Trace and byte display

```powershell
python generate.py --trace '>>>+'
python generate.py --trace ',.,.' --input-hex ff41
python generate.py --trace '+[.]' --max-steps 100
python generate.py --trace '+[+]' --max-steps 512
```

Quote Brainfuck source to protect shell metacharacters. A trace contains one
before/after event per executed instruction and a final result. `+[.]` is
proven cycling after four executed instructions despite producing output.
Byte representations and JSON integer arrays are display encodings, not UTF-8
output-byte measurements. Invalid trace source exits with code 2. A valid
trace that reaches the step limit completes normally and reports unresolved
status; it does not claim a program error or nontermination.

## Boundaries of Phase 1

No length-five through length-seven experiment has been run. No measured
performance forecast, output/memory productivity study, paper, or browser
implementation is claimed. The step budget is not a memory or time budget.
Phase 2 must introduce those resource controls before proposing larger runs.
