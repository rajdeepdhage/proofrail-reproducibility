# ProofRail — Reproducibility Package

Data, logs, and analysis tooling for reproducing the benchmark results in
**"Programmable Settlement Without Tokenization: A Hybrid Book-Entry Ownership
Registry with Event-Driven Conditional Settlement as an Alternative to Tokenized
Financial Infrastructure."**

ProofRail is an event-driven conditional settlement engine that operates on
existing bank rails. Funds and ownership claims are recorded as electronic
book entries at regulated deposit institutions rather than as tokens on a
distributed ledger; disbursement is governed by a rules engine that releases,
holds, or reverses value only when authenticated evidence of defined real-world
events has been received. Every state change is written to a hash-linked audit
log. See [`docs/methodology.md`](docs/methodology.md) for how the mechanism
works and [`docs/metrics.md`](docs/metrics.md) for exactly how each reported
number is defined and computed.

> **Artifact status: public-draft ready, not final-release ready.** The supplied
> H1-H3 checks and four KNIME aggregate comparisons are reproducible. H4 still
> requires two row-level KNIME exports, and no permanent DOI has been issued.
> See [`docs/evidence_status.md`](docs/evidence_status.md) before citing a
> hypothesis result.

---

## What this repository is for

The claim being supported is not "trust these results" but **"recompute these
results yourself."** Three things make that possible without access to the
engine's source code:

1. **Every reported number is derived from published per-transaction traces.**
   `metrics/compute_metrics.py` recomputes the headline metrics from
   `benchmark/logs/` and diffs them against the published summary tables. If
   they disagree, the script fails.
2. **The audit-integrity claim is independently checkable.**
   `verifier/verify_audit_chain.py` is a standalone read-only tool that
   recomputes the hash chain of a sample audit log. It shares no code with the
   engine that wrote the chain.
3. **Both supplied input populations are regenerable byte-for-byte.** The
   generator, seed, frozen 75-case performance input, and frozen 5,000-row KNIME
   ProofRail input are included and checked automatically.

## Quick start

```bash
# After downloading or cloning the repository:
cd proofrail-reproducibility

# 1. Recompute all reported metrics from the raw traces and check them
#    against the published summary tables.
python3 metrics/compute_metrics.py --check

# 2. Independently verify the sample audit chain.
python3 verifier/verify_audit_chain.py verifier/sample_audit_chain.db

# 3. Verify the four-comparison design invariants from the KNIME outputs.
python3 metrics/check_comparison_invariants.py

# 4. Run the H1/H2 hypothesis tests with breakeven analysis.
python3 metrics/hypothesis_tests.py

# 5. Measure tamper-detection empirically (240 mutation trials).
python3 metrics/tamper_experiment.py

# 6. Or run the complete integrity, regeneration, analysis, and test suite.
bash scripts/verify.sh
```

No third-party Python packages are required for the automated checks. Use
Python 3.9 or later; KNIME is required only to re-execute its visual workflows.

## Headline results

Recomputed by `metrics/compute_metrics.py` from `benchmark/logs/normalized_comparison_rows.csv`
(75 cases per system, identical case population for both):

| Metric | Manual bank workflow | ProofRail |
|---|---|---|
| Authorization latency, mean (s) | 3906.09 (n=75) | 0.0139 (n=70) |
| Authorization latency, p50 (s) | 3171.10 (n=75) | 0.00 (n=70) |
| Authorization latency, p90 (s) | 5364.26 (n=75) | 0.081 (n=70) |
| Manual verification touches / case | 3.20 (n=75) | 0.0267 (n=75) |
| Automated checks / case | 0.97 | 5.75 |
| Auditability rubric (rollup) | 8.00 | 11.97 |

**These are simulation-based demonstration figures, not measured production
performance.** Both the bank baseline and the ProofRail population are
synthetic; the bank workflow is a *modeled* process, because the source banking
datasets do not expose internal approval and settlement timestamps. Sensitivity
ranges over the modeled assumptions are published in
`benchmark/results/bank_sensitivity_sweep.json` and should be read alongside
the point estimates above.

Five held/disputed ProofRail cases do not have an authorization-latency value,
so H1's original independent-sample test uses 70 ProofRail observations and 75
bank observations. The hypothesis script also reports an exact paired sign test
on the 70 shared trace IDs. This observation-count difference must be disclosed
where H1 is reported.

## Four-comparison results (data-characterization layer)

The same three-way comparison is run four times, holding the bank and ProofRail
legs constant while varying the blockchain comparator, so that ProofRail's
position is tested against every blockchain settlement model rather than a
blended average. All runs use n = 5,000 records per system, seed 42.

| Comparison | Blockchain mean (USD) | Blockchain exception rate |
|---|---|---|
| Bank vs. ProofRail vs. USDC stablecoin | 29,441.11 | 0.0000 |
| Bank vs. ProofRail vs. Bitcoin | 184,841.76 | not reported (no status field) |
| Bank vs. ProofRail vs. Ethereum | 4,504.63 | 0.0050 (failed execution) |
| Bank vs. ProofRail vs. smart-contract events | n/a (non-monetary) | not reported (no status field) |

Constant across all four: banking mean 70,763.32 / exception rate 0.1236;
ProofRail mean 4,692.25 / exception rate 0.2792. That constancy is verified
automatically by `metrics/check_comparison_invariants.py`, which fails if either
leg varies.

> **Do not read the exception-rate column as a performance ranking.** ProofRail's
> 27.9% counts cases held or disputed pending evidence. Blockchain zeros, blanks,
> and Ethereum execution failures are not the same construct. The analyzed
> extracts do not encode comparable held/disputed/reversed terminal states; that
> is a descriptive dataset finding, not proof that every blockchain protocol or
> smart contract is incapable of implementing recourse. See
> [`docs/comparison_results.md`](docs/comparison_results.md) before citing these
> figures.

## Hypothesis evidence

| | Claim | How it is established |
|---|---|---|
| **H1** | Lower authorization latency | Supported within the modeled benchmark: Mann-Whitney U (one-tailed), rank-biserial effect size, bootstrap interval, sensitivity analysis, and a 70-pair exact sign robustness check |
| **H2** | Fewer manual touches | Supported within the modeled benchmark by the same analysis family and a 75-pair exact sign robustness check |
| **H3** | Higher auditability | **Not a significance test.** Tamper-evidence is *measured*: 240/240 mutations detected and localized. Independent verifiability is demonstrated by the standalone verifier. Completeness and non-repudiation remain published rubric judgements. |
| **H4** | Distributional calibration | **Pending.** The planned two-sample KS script is included, but the required row-level bank and ProofRail KNIME exports are not yet present. Non-rejection would not prove equivalence. |
| **H5** | Terminal-state composition | Descriptive evidence from four extracts; the supplied chi-square table is exploratory and covers only systems with a coded status. Do not generalize the result to all blockchain designs. |

Because H1 and H2 show complete separation in this generated population, the
p-values add little beyond the effect sizes and matched-case checks. The
**breakeven analysis** asks whether the result survives the defined 27-scenario
model envelope. It does; this is robustness within the model, not evidence of
production-bank performance. Full detail, including what remains open, is in
[`docs/hypothesis_evidence.md`](docs/hypothesis_evidence.md).

## Repository layout

```
generator/          Seeded synthetic case generator (SettleSim)
benchmark/data/     Frozen input population + generation profile
benchmark/row_level/ Contract for the two pending H4 KNIME exports
benchmark/logs/     Per-transaction step-level traces (the evidence base)
benchmark/results/  Published summary tables, analysis report, provenance
benchmark/results/knime/   Exported tables from the four KNIME comparisons
metrics/            Metric recomputation, hypothesis tests, design invariants,
                    and the tamper-detection experiment
verifier/           Standalone read-only audit-chain verifier + sample chain
knime/workflows/    The four executable KNIME workflows (inspectable node by node)
knime/figures/      Rendered workflow graphs (SVG)
docs/               Methodology, metric definitions, data dictionary
scripts/            Manifest generation and integrity verification
tests/              Standard-library unit tests
```

## What is included, and what is not

**Included:** the case generator, both frozen ProofRail input populations, all step-level
execution logs, the metric computation and design-invariant code, the audit-chain
verifier, the comparison summaries, the provenance and sensitivity files, the
four executable KNIME workflows, and their exported result tables.

**Not included, and why:**

- **Source banking and blockchain datasets.** The J.P. Morgan AI Research
  synthetic datasets are distributed on request by their publisher and cannot be
  redistributed here. See [`DATA_ACCESS.md`](DATA_ACCESS.md) for the request
  procedure, the expected filenames and columns, and the blockchain extraction
  specifications.
- **The ProofRail engine core** (rules evaluation and audit-chain *write* path).
  A patent application covering parts of this mechanism is being prepared. The
  read-only verifier, the complete execution traces, and the metric code are
  published instead, which is sufficient to recompute and independently check
  every reported result. Full source is available to journal reviewers and
  thesis committee members on request under confidentiality; public release is
  planned once patent protection.

This division is stated plainly rather than obscured: a reader can verify the
results, and can see precisely which component is withheld and why.

## Reproducing from scratch

See [`REPRODUCE.md`](REPRODUCE.md) for the full procedure, including
regenerating the case population from its seed and re-running the KNIME
comparison workflows.

## Citing

If you use this package, please cite the thesis and this repository — see
[`CITATION.cff`](CITATION.cff). The final GitHub URL and DOI are intentionally
absent until those identifiers actually exist. Follow
[`docs/release_and_citation.md`](docs/release_and_citation.md) to publish and
archive a citable version.

Before describing the package as journal-ready, run `make release-check`. It is
expected to fail in this draft while H4, the repository URL, and DOI are pending.

## Licensing

| Component | License |
|---|---|
| Code (`generator/`, `metrics/`, `verifier/`, `scripts/`) | MIT — see [`LICENSE-CODE`](LICENSE-CODE) |
| Data, logs, results, and documentation | CC BY 4.0 — see [`LICENSE-DATA`](LICENSE-DATA) |

The MIT license applies only to the code published here and grants no rights in
the ProofRail engine core or any patent rights.

## Disclaimer

All data in this repository are synthetic or modeled. Nothing here represents
measured performance of any production payment system, and no result should be
read as a claim about the live operations of any financial institution.

*This publication includes or references synthetic data provided by J.P. Morgan.*
