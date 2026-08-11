# How Each Hypothesis Is Evidenced

The five hypotheses are not all established the same way, and one of them cannot
be established by a significance test at all. This document states, for each,
what kind of claim it is, what evidence supports it, and what that evidence does
not settle.

Run everything described here with:

```bash
bash scripts/verify.sh
```

---

## H1 — Authorization latency (one-tailed)

**Claim.** ProofRail reaches a settlement decision faster than the manual bank
workflow, with the payment rail held constant.

**Evidence.** `metrics/hypothesis_tests.py`

| | |
|---|---|
| Medians | ProofRail 0.0 s · bank 3,171.1 s |
| Mann-Whitney U (one-tailed) | U = 0, p < 1e-16 |
| Rank-biserial effect size | 1.0 (complete dominance) |
| Bootstrap 95% CI on median difference | [2,919.0, 3,478.5] s |
| Separation | Complete — slowest ProofRail case (0.083 s) faster than fastest bank case (1,097.4 s) |
| Paired robustness | 70/70 shared non-tied trace IDs favour ProofRail; exact one-tailed sign test p < 1e-16 |

**The significance test is close to a formality here, and saying so is the
honest move.** With zero overlap between the samples, the p-value was determined
the moment the two systems were defined. What carries the weight instead is the
breakeven analysis below.

**Sample note.** The latency test uses 70 ProofRail cases against 75 bank cases.
The five excluded ProofRail cases are those that terminated in a held state and
therefore have no release-authorization latency under the study's metric
definition. The result is consequently conditional on observed release latency.
The paired robustness check compares only the 70 trace IDs observed in both
systems; this missing-outcome limitation must remain visible in the paper.

---

## H2 — Manual verification touches (one-tailed)

**Claim.** ProofRail requires fewer human review touches per case.

**Evidence.**

| | |
|---|---|
| Medians | ProofRail 0.0 · bank 3.0 |
| Mann-Whitney U (one-tailed) | U = 0, p < 1e-16 |
| Rank-biserial effect size | 1.0 |
| Bootstrap 95% CI | [3.0, 3.0] touches |
| Separation | Complete — max ProofRail 1.0 vs min bank 2.0 |
| Paired robustness | 75/75 shared non-tied trace IDs favour ProofRail; exact one-tailed sign test p < 1e-16 |

**Substitution, not just elimination.** ProofRail averages 5.75 automated checks
per case against the bank workflow's 0.97. The touches are replaced by
authenticated machine checks rather than simply dropped, and both counts are
published per case so the substitution can be inspected rather than asserted.

---

## The real vulnerability in H1 and H2, and how it is answered

The bank baseline is **modeled, not measured**. The source banking datasets do
not expose internal approval, clearing, and reconciliation timestamps, so review
durations and touch counts were estimated. The fair objection is therefore not
"is the difference significant" but **"did you choose parameters that made your
system win?"**

Defending the chosen parameters would be weak. Instead the analysis computes the
**breakeven point** — how good the manual workflow would have to become before
the advantage disappears — and compares it against the entire sensitivity
envelope actually swept (27 scenarios, `benchmark/results/bank_sensitivity_sweep.json`):

- **Latency.** The fastest modeled bank authorization anywhere in the sweep is
  0.84 working hours (≈ 3,024 s). ProofRail's median is 0 s at the recorded
  resolution and its slowest observed release case is 0.083 s. Breakeven lies
  outside the defined sweep.
- **Touches.** The lowest modeled bank touch count anywhere in the sweep is 3.13.
  Breakeven would require 0 under the study's operational definition, so it is
  outside the modeled family.

**The result is robust to the parameter values inside this sweep.** It does not
show that every plausible or production bank workflow lies inside the modeled
family.

**What remains genuinely open,** and should be stated rather than hidden: the
modeled family itself could be wrong. If real bank conditional-payment workflows
resolve in seconds rather than hours, the model is misspecified in a way no
sensitivity sweep over its own parameters can detect. Anchoring the model's
parameters to published figures on manual payment-review times, or to measured
data from a cooperating institution, is the improvement that would close this —
and it is future work, not a claim made here.

---

## H3 — Auditability (structural comparison, **not** a significance test)

**Why no test.** The rubric assigns a near-constant score per system: every one
of the 75 bank cases scores exactly 8.0 (standard deviation 0), and 73 of 75
ProofRail cases score 12.0. There is no sampling variance. Running a
significance test on that would produce an impressive p-value that establishes
only that 8 ≠ 12 — a fact fixed by the scoring rule before any data were seen.
Reporting it as a hypothesis test would be circular, and a statistically literate
reader will notice.

H3 is therefore split into what can be **measured** and what remains **judgement**:

### Measured: tamper-evidence

`metrics/tamper_experiment.py` mutates the audit chain and runs the production
verifier against each mutation. Results over 240 trials (seed 42) on a 440-entry
chain:

| Mutation strategy | Detected | Localized |
|---|---|---|
| Payload alteration | 40/40 | 40/40 |
| Action relabelling | 40/40 | 40/40 |
| Timestamp shift | 40/40 | 40/40 |
| Settlement reassignment | 40/40 | 40/40 |
| Forged entry hash | 40/40 | 40/40 |
| Entry deletion | 40/40 | 40/40 |
| **Total** | **240/240 (100%)** | **240/240 (100%)** |

The forged-hash strategy is the demanding case: an adversary who alters content
*and* recomputes that entry's own hash so it is internally consistent. It is
still caught, because the following entry's `prev_hash` no longer matches —
detection shifts one link forward, which is precisely what the linked chain is
for. This is a measured detection rate, not a rubric score.

### Measured: independent verifiability

Demonstrated by existence: `verifier/verify_audit_chain.py` is a standalone,
read-only tool that shares no code with the engine that wrote the chain. Anyone
can run it against the published chain and confirm the result.

### Judgement: completeness and non-repudiation

These remain researcher-assigned rubric scores. They are published per case with
their four components broken out, so a reader who disagrees with the weighting
can recompute from the component columns. `metrics/compute_metrics.py`
independently re-derives the rollup from its components and fails if the stored
rollup disagrees with their sum. Report these descriptively; never attach a
p-value.

---

## H4 — Distributional calibration (two-tailed)

**Status: pending.** The aggregate KNIME tables are insufficient for a
distribution test. Export the two sampled row-level tables described in
`benchmark/row_level/README.md`, then run:

```bash
python3 metrics/h4_distribution_test.py \
  --json benchmark/results/h4_distribution_test.json
```

The script reports a two-sample KS statistic on `log1p(amount_usd)` and an
asymptotic two-sided p-value. This is a **calibration check, not an independent
finding**: generation was calibrated to the consolidated banking data, so
agreement is partly by construction. Failure to reject the KS null does not
prove equivalence. Report D, both sample sizes, the sampling seed, all excluded
values, and this limitation.

---

## H5 — Terminal-state composition and reversibility (omnibus)

**Claim, limited to the analyzed extracts.** Terminal-state coding differs by
dataset, and the four blockchain extracts do not encode a state directly
comparable to ProofRail's held or disputed state.

**Evidence.** The four KNIME comparisons
(`docs/comparison_results.md`). Across Bitcoin, Ethereum, smart-contract events,
and USDC, no dataset contains a field representing a held, disputed, or reversed
state. Ethereum's 0.5% "exception" rate is *failed execution*, not recourse.

The four-comparison design shows that absence separately in each supplied
extract rather than hiding it in a pooled crypto average. It does **not** prove
that all blockchain protocols or smart contracts are incapable of implementing
recourse; schema absence and protocol impossibility are different claims.

**Do not report exception rate as a ranked column.** ProofRail holds/disputes,
bank fraud/AML flags, and Ethereum execution failures are different constructs.
The supplied H5 chi-square is exploratory and omits Bitcoin and smart-contract
events because they have no commensurate status field. See
`docs/comparison_results.md`.

---

## Known asymmetry between the two layers

The data-characterization layer (H4, H5) runs at **n = 5,000 per system**. The
performance-evaluation layer (H1–H3) runs at **n = 75**. A reviewer will
reasonably ask why the headline performance claim rests on the smaller sample.

The replay can be re-run at 8,000–10,000 cases using the export feature, and
should be before submission. Nothing in the analysis code needs to change:
`metrics/hypothesis_tests.py` and `metrics/compute_metrics.py` read whatever is
in `benchmark/logs/`, so re-running the replay and replacing those logs is
sufficient. The expectation is that complete separation persists and the
confidence intervals tighten.
