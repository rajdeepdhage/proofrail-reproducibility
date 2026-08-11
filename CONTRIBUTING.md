# Contributing

This repository is a research artifact. Changes should preserve traceability,
provenance, and the distinction between modeled evidence and measured evidence.

1. Do not commit confidential, customer, account, or production banking data.
2. Keep the `synthetic_research` and `crypto_onchain` provenance labels intact.
3. Add or update a check when changing a metric, schema, generator, or verifier.
4. Run `make verify` before proposing a change.
5. Run `make manifest` last, then run `make verify` again.
6. Describe any changed result and its effect on the thesis claims in the pull
   request and in `CHANGELOG.md`.

Changes to analytical definitions require corresponding updates to
`docs/metrics.md`, `docs/evidence_status.md`, and the thesis methodology. A
passing script is not enough if the interpretation has changed.
