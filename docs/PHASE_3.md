# Phase 3 completion record

## Delivered

1. Four versioned datasets with complete candidate coverage through length six,
   full compressed CSV/JSON execution records, summary tables, exact configs,
   measured timing/environment, source provenance, and artifact checksums.
2. Paired 512/4096-step and 8/4-bit cell-width comparisons; record-setting program
   examples, productivity distributions, and explicit unresolved classifications.
3. Complete saved-record verification, cycle/witness replay evidence, narrow
   structural nontermination proofs, and a reproduced dataset with identical
   compressed-record hashes. Results and exact reproduction commands are documented.

The four runs use committed engine source
`8a7ce03825edaac753f809a62c0ee5b7596bb9bb` (version 0.3.0). The original 8-bit
semantics and historical 100-step results remain intact.

## Verification

- 77 automated tests pass, including the original differential baseline and new
  export integrity, deterministic record reproduction, cell-width, cycle
  certificate, and arithmetic witness checks.
- 897608 saved candidate records across configurations reconcile in both CSV and
  JSON with enumeration order, syntax counts, coverage, and summary metrics.
- All 10078 recorded cycles were replayed into equal-control-state certificates.
- All 33 selected record witnesses were replayed; 24 eight-bit witnesses also
  agree with the archived original interpreter.
- A fresh 37448-record run produced identical compressed CSV/JSONL hashes and
  identical scientific summaries after excluding runtime measurements.

## Findings and limits

At 4096 steps, eight-bit length-five/six records reach T=767/1026 and O=255/510.
The runner leaves U=4/88, respectively; timeouts are not proofs of nontermination.
The four length-five cases have a separately documented fresh-cell growth proof.
Changing cells to four bits reduces those runtime records to 47/66 and output
records to 15/30. All statements are scoped to the evaluated models and lengths.

Length seven was deferred after measuring real export costs. No paper, website,
novelty claim, or complete proof classification for length six is claimed. These
limits are part of the research record, not hidden missing data.

## Next approval checkpoint

Phase 4: verified literature review, deeper analysis and publication-quality
figures, and the approximately 6-8-page editable academic report. Assess
originality against prior work before claiming a contribution. Phase 4 requires
approval before implementation.
