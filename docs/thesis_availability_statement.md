# Data and Code Availability Statement

Text for inclusion in the thesis and in any journal submission. Replace the
bracketed placeholders before use.

---

## Full version (journal submission)

> **Data and code availability.** The synthetic case population, complete
> per-transaction execution logs, metric computation code, a standalone
> audit-chain verifier, and the KNIME analysis workflows supporting this study
> are openly available at
> https://github.com/rajdeepdhage/proofrail-reproducibility and permanently
> archived at [DOI]. Reported metrics can be recomputed from the published
> traces using `metrics/compute_metrics.py`, which verifies its output against
> the published summary tables; the audit-integrity claim can be independently
> checked using `verifier/verify_audit_chain.py`, which shares no code with the
> engine that produced the chains. The structural claim behind the
> four-comparison design — that the bank and ProofRail legs are held constant
> while only the blockchain comparator varies — is likewise verifiable from the
> exported tables using `metrics/check_comparison_invariants.py`.
>
> The J.P. Morgan AI Research synthetic banking datasets used as the banking
> comparator are distributed by their publisher on request and are therefore not
> redistributed; request procedures, expected filenames, and column
> specifications are documented in the repository. This publication includes or
> references synthetic data provided by J.P. Morgan.
>
> The ProofRail engine core is subject to a pending patent application and is
> not publicly released. It is available to reviewers and examiners on request
> under confidentiality. Public release is planned once patent prosecution
> permits. All published results are simulation-based demonstration evidence
> derived from synthetic and modeled data; they are not measured production
> performance.

## Short version (thesis chapter footnote)

> All data, execution logs, metric code, the audit-chain verifier, and the four
> executable KNIME comparison workflows supporting this chapter are available at
> https://github.com/rajdeepdhage/proofrail-reproducibility (archived at [DOI]).
> Source banking datasets are distributed by their publisher on request; see the
> repository's `DATA_ACCESS.md`. The engine core is withheld pending patent
> prosecution and is available to examiners on request.

---

## Where to use it

- **Thesis Chapter 2** — replace phrases promising that artifacts are "archived
  with the thesis" with the concrete repository URL and DOI.
- **Thesis front matter** — include the full version.
- **Journal submission** — most venues require this statement in a dedicated
  section; the full version above is written to satisfy that requirement.

## Obtaining a DOI

Deposit a tagged release on [Zenodo](https://zenodo.org/) (link the GitHub
repository, then publish a release) or [OSF](https://osf.io/). Zenodo mints a
DOI per release plus a concept DOI covering all versions. Cite the
version-specific DOI so that a reader retrieves exactly the artifacts used.
