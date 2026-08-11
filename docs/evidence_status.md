# Evidence Status and Claim Boundaries

This page is the shortest reliable guide to what the repository currently
establishes. It should be updated before the thesis, a paper, or a release uses
stronger wording.

| Hypothesis | Status | Evidence currently present | Claim boundary |
|---|---|---|---|
| H1: lower authorization latency | Complete within the modeled benchmark | One-tailed Mann-Whitney U, rank-biserial effect size, bootstrap interval, sensitivity envelope, and an exact paired sign robustness check | The primary latency analysis has 70 observed ProofRail values and 75 bank values; the paired check uses the 70 shared trace IDs. This is synthetic/modeled evidence, not production-bank performance. |
| H2: fewer manual touches | Complete within the modeled benchmark | The same analysis family, with 75 observations per system and 75 matched trace IDs | Manual touches are generated from the study's operational model. They are not observations from a bank's internal workflow. |
| H3: higher auditability | Partly measured, partly descriptive | 240/240 seeded mutations detected and localized; standalone verifier checks the published chain; rubric components are published | Tamper detection is measured on the supplied chain and mutation set. Completeness, independent verifiability, and non-repudiation scores remain researcher-defined rubric judgments. |
| H4: distributional calibration | Pending | The generator and the planned KS script are present | The row-level bank and ProofRail KNIME exports have not yet been supplied, so no H4 test result is published. A non-significant KS result would not prove equivalence. |
| H5: terminal-state composition | Descriptive; exploratory chi-square available | Four KNIME schemas/results and `spss/h5_state_counts.csv` | The extracts do not encode comparable held/disputed/reversed states. That describes these datasets; it does not prove that every blockchain protocol or smart contract is incapable of implementing recourse. Ethereum failure status is not the same construct as a ProofRail hold. |

## Two Evidence Layers

The performance layer (H1-H3) replays 75 synthetic cases through ProofRail and a
modeled bank process. The data-characterization layer (H4-H5) samples 5,000 rows
per system in KNIME. These layers answer different questions and should not be
pooled into one performance ranking.

## Required Before Journal Submission

1. Export the bank and ProofRail sampled row-level tables described in
   `benchmark/row_level/README.md` and run H4.
2. Decide whether H4 is a difference test or a pre-specified equivalence claim;
   failure to reject a KS null is not evidence of equivalence by itself.
3. Report H1's valid observation counts and paired robustness result.
4. Present H5 as terminal-state coding in the analyzed extracts, with Ethereum
   execution failure separated from reversible settlement states.
5. Replace repository and DOI metadata only after the tagged artifact is public.
