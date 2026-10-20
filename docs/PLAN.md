# Approved five-phase implementation plan

Each phase has three task groups and requires approval before the next phase.
Make at least two focused commits per phase and push completed work. Use tabs
for new code, keep research and presentation separate, and report real checks.

Phases 1-3 are implemented and verified. Phase 4 awaits approval. Completion
records: [Phase 1](PHASE_1.md), [Phase 2](PHASE_2.md), [Phase 3](PHASE_3.md).

| Phase | Task groups | Completion evidence |
| --- | --- | --- |
| 1: Audit and validation | Preserve baseline/semantics; modular Python refactor; regression and differential tests. | Original and extended length-four results reproduced, all valid final states compared, semantics and corrections documented. |
| 2: Experimental engine | Configurable streaming enumeration for 1-7; resource metrics and limits; performance improvements and benchmarks. | Correct accounting and metrics, regression agreement, measured cost estimates before large runs. |
| 3: Reproducible experiments | Progressively run feasible lengths; version datasets/configuration/provenance; examine limit and memory sensitivity. | Replayed witnesses, reproducible datasets, T/O/M/D/U summaries with uncertainty. |
| 4: Paper | Verify related work; analyze results and generate figures; write 6-8-page editable report. | Checked citations, data-backed claims, reproducible figures, reviewed rendered paper and honest novelty assessment. |
| 5: Website | React/Vite presentation/dashboard; bounded simulator; tests, production build, deployment guidance. | Shared Python/JS fixtures, actual datasets, responsive and accessible controls, verified build. |

Primary experiments use exactly n commands, empty input, and
`legacy-u8-right-v1`. Preserve historical allocated-tape outcome equivalence.
Report observed lower bounds when incomplete coverage or unresolved executions
could alter records. Discuss computational feasibility before expensive runs.

Phase 2 owns `config.py`, `experiments.py`, `export.py`, and `benchmarks/`
extensions. Phase 3 owns `data/runs/` and experiment configurations. Phase 4 owns
`paper/`, references and figures. Phase 5 owns `website/`, with components in
`src/components/` and separate scoped styles in `src/styles/`.
