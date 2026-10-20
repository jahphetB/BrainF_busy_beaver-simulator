# Literature verification and contribution assessment

Checked 2026-10-20. This is a focused review, not a systematic literature review.
Publisher pages, author-hosted work, author-uploaded manuscripts and the original
software repository support the comparisons. No external experiments were rerun.
Titles/authors/identifiers below were checked against the linked sources.
The bibliography deliberately omits unverified publication dates, page ranges
and identifiers. Search snippets alone are not the basis for technical comparisons.

| Paper reference | Verified source and use | Limits on comparison |
| --- | --- | --- |
| [1] Radó, 1962 | [Publisher metadata and abstract](https://onlinelibrary.wiley.com/doi/abs/10.1002/j.1538-7305.1962.tb00480.x): title, author, volume 41(3), pp. 877-884 and DOI checked. Historical origin of the problem. | Full publisher text was not required for this attribution; formal runtime definition is supported by [2]. |
| [2] Aaronson, 2020 | [Author-hosted survey](https://www.scottaaronson.com/papers/bb.pdf), pp. 1-2: runtime maximization over halting, blank-tape Turing machines. Year also checked on the author's [announcement](https://scottaaronson.blog/?p=4916). | Survey is contextual; no current Busy Beaver record is asserted. |
| [3] Cristofani, undated | [Language reference](https://brainfuck.org/brainfuck.html): instructions, matching brackets, jump after matching opening bracket, implementation variations. | Our clamped boundary and EOF-zero are explicitly selected dialect rules. |
| [4] Čibej, Robič and Mihelič, 2014 | [Author-uploaded full manuscript](https://www.researchgate.net/publication/267327970_Empirical_Estimation_of_the_Halting_Probabilities), sections 2-4: six-command grammar, uniform generation, sampled runtimes and changed loop semantics. Conference/year corroborated by [University of Ljubljana](https://www.fmf.uni-lj.si/en/study-mathematics/programmes/2isrm/2026/courses/266/). | This is prior enumeration and semantic-sensitivity work. Its grammar and sampled populations differ from ours; we do not adopt cutoff-based nonhalting labels. No DOI or formal proceedings pagination verified. |
| [5] Eterevsky, undated | [Original repository README](https://github.com/eterevsky/beaver), Method/Dialect/Results: runtime and visited-cell searches, invariant reasoning, no I/O, overflow termination on cell arithmetic and left boundary. | Reported enumeration through 18 and resolution through 12 are the author's claims, not reproduced here. Numeric records cannot be ranked against our wrapping-cell model. |
| [6] Calude and Stay, arXiv v4 (2007) | [Author preprint](https://arxiv.org/abs/cs/0610153v4): probabilistic runtime results assume a distribution over time. | Does not certify our individual cutoff cases as nonhalting. Cite this verified version, not uninspected journal pagination. |
| [7] Soler-Toscano et al., 2014 | [Publisher article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0096223): authors, date, 9(5):e96223, DOI; finite Turing-machine output-frequency approach to complexity approximation. | This work does not validate our conditional outcome frequencies as exact Kolmogorov complexity. |
| [8] Faase, undated | [Author's page](https://www.iwriteiam.nl/Ha_bf_numb.html): short programs generating numeric constants, with a required final cell/pointer configuration. | Numeric magnitude is a different objective from emitted byte count or runtime; no record comparison. |

Discovery queries included “Brainfuck busy beaver enumeration research”,
“Empirical Estimation of the Halting Probabilities”, “The Busy Beaver Frontier”,
and the exact titles of [1], [6], [7]. The Busy Beaver Gauge page was a discovery
link to [8], not authority for our numeric records. A guessed arXiv identifier for
Aaronson resolved to an unrelated paper and was rejected; the bibliography uses
the verified author-hosted PDF.

## Claim boundaries

- **Established:** Busy Beaver optimization, Brainfuck enumeration, and
  semantics-dependent behavior have substantial prior work.
- **Reproduced here:** the archived length-four baseline and interpreter outcomes.
- **Measured here:** paired cutoff/width changes, exact saved outcome counts,
  runtime-output distributions, and replayable witness/cycle records.
- **Model-level argument:** the four length-five right-growing loops do not halt;
  the proof is elementary and no priority claim is made.
- **Potential contribution:** an inspectable teaching/research artifact joining
  raw data, explicit semantics, resource accounting and replay evidence.
- **Not established:** a new Busy Beaver record, new complexity theorem, new
  enumeration method, compression improvement, or a general law of productivity.

The paper's novelty claim is limited to this repository's implementation and
documented experiment. A wider search and independent replication would be
needed to establish research priority.
