# Changelog

## 0.1.1 - 2026-10-26

- Recorded U.S. Provisional Patent Application No. 64/183,770 in the README and
  the thesis availability statement.
- Corrected the description of ProofRail's 27.9% non-routine share: 12.1% held
  or disputed and 15.9% released after delayed evidence.
- Documented the H4 result and the difference between the `log1p` (all rows)
  and base-ten (positive amounts) versions of the test.
- The verify workflow now refreshes `MANIFEST.sha256` automatically after each
  push, so browser edits no longer fail the integrity check.

## 0.1.0 - 2026-08-02

- Prepared the artifact as a GitHub-ready reproducibility draft.
- Added CI, a Makefile, unit tests, and exact generator-regeneration checks.
- Added the frozen 5,000-row ProofRail input used by the KNIME comparison.
- Added an H4 row-level export contract and KS analysis script.
- Added evidence-status and release/citation guidance to prevent overclaiming.
- Marked DOI and final repository metadata as pending rather than completed.
