# Research data index

`historical/` preserves the original length-four implementation and baseline.
`runs/v1/` contains the Phase 3 version-one research datasets. Existing run
directories are immutable inputs; reproduction uses new directories.

| Run | Cell width | Lengths | Instruction budget | Candidate records |
| --- | ---: | --- | ---: | ---: |
| [primary-n1-5-s512](runs/v1/primary-n1-5-s512/summary.json) | 8 | 1-5 | 512 | 37448 |
| [primary-n6-s512](runs/v1/primary-n6-s512/summary.json) | 8 | 6 | 512 | 262144 |
| [steps4096-n4-6](runs/v1/steps4096-n4-6/summary.json) | 8 | 4-6 | 4096 | 299008 |
| [cell4-n4-6-s4096](runs/v1/cell4-n4-6-s4096/summary.json) | 4 | 4-6 | 4096 | 299008 |

Each directory includes `manifest.json`, `config.json`, `summary.json`,
`summary.csv`, `programs.jsonl.gz`, and `programs.csv.gz`. Manifests record source
commit/file hashes, actual environment, timestamps, artifact hashes/sizes, and
record totals. Every candidate is saved, including invalid syntax. No run has
unevaluated candidates, but lengths five/six have execution-limit cases.

Derived artifacts in [analysis/v1](analysis/v1/manifest.json):

- [summary.csv](analysis/v1/summary.csv) and [summary.json](analysis/v1/summary.json): all configurations.
- [witnesses.json](analysis/v1/witnesses.json): 33 replayed T/O/M witness records.
- [runtime-output.csv](analysis/v1/runtime-output.csv): actual halted runtime/output pair frequencies.
- [sensitivity.json](analysis/v1/sensitivity.json): paired status transitions and changed runtimes.
- `cycle-certificates.jsonl.gz`: 10078 replayed repeated-state certificates.
- `unresolved.json.gz`: complete records for step/resource-limited programs.
- [structural-proofs.json](analysis/v1/structural-proofs.json): supplemental proofs for four fresh-cell growth programs, preserving raw runner classifications.
- [verification.json](analysis/v1/verification.json): record-accounting and replay coverage.

[The reproduction check](verification/phase3-reproduction.json) documents an
independent rerun of the 37448-record primary dataset with identical compressed
CSV/JSONL hashes. [Instructions](../docs/PHASE_3_REPRODUCIBILITY.md) explain how to
reproduce or verify the files. [Results and limitations](../docs/RESULTS.md)
explain their scientific interpretation. No originality claim is attached to
these datasets before the Phase 4 literature review.
