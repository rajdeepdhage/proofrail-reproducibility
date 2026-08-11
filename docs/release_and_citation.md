# GitHub Release and Citation Guide

The repository is ready to publish as a transparent work-in-progress research
artifact. It is not yet ready to describe as a complete journal evidence pack,
because H4 and the permanent repository identifiers are pending.

## Publish the Draft on GitHub

1. Create an empty public repository named `proofrail-reproducibility`.
2. From this directory, initialize Git, add the GitHub remote, and push the main
   branch.
3. Confirm the GitHub Actions `verify` workflow passes on Python 3.9 and 3.12.
4. In the repository description, state: "Synthetic and modeled research
   artifact; not measured production payment performance."
5. Add the final GitHub URL to `CITATION.cff` as `repository-code`.

## Prepare a DOI-Bearing Release

1. Complete H4 or explicitly remove H4 as a tested hypothesis from the paper.
2. Run `make verify`.
3. Run `make release-check`; resolve every item it reports.
4. Run `make manifest`, then `make verify` once more.
5. Tag the exact version used in the thesis or paper.
6. Connect the GitHub repository to Zenodo and archive that tagged release.
7. Add the version DOI and release date to `CITATION.cff`, regenerate the
   manifest, and create the final release tag if the archive workflow requires
   a metadata-only follow-up version.

Do not say that a DOI-bearing release exists until Zenodo or another repository
has actually issued the identifier.

## Suggested Artifact Citation

Replace the bracketed fields after release:

> Dhage, R. (2026). *ProofRail Reproducibility Package* (Version [version])
> [Software and data set]. [Archive]. https://doi.org/[DOI]

## Suggested Thesis Availability Statement

> The synthetic case population, execution logs, metric code, audit-chain
> verifier, and KNIME workflows supporting this study are available in the
> ProofRail Reproducibility Package at [GitHub URL], archived as version
> [version] at https://doi.org/[DOI]. The package identifies modeled and
> synthetic evidence explicitly and documents the access procedure for source
> data that cannot be redistributed.

The longer journal version remains in `docs/thesis_availability_statement.md`.
