# Metric Recomputation

Recomputes every reported benchmark figure from the per-transaction traces in
`../benchmark/logs/`, then diffs the result against the published summary in
`../benchmark/results/`. Disagreement beyond a 0.01 tolerance is reported as a
failure.

```bash
python3 compute_metrics.py            # recompute and print
python3 compute_metrics.py --check    # also diff against published summary
python3 compute_metrics.py --json out.json
```

Standard library only. Metric definitions are in
[`../docs/metrics.md`](../docs/metrics.md).

The script also re-derives the auditability rollup from its four components and
fails if the stored rollup disagrees with their sum — an internal-consistency
check on the rubric.

---

## Design-invariant check

`check_comparison_invariants.py` verifies the structural claim behind the
four-comparison design: that the bank and ProofRail legs are identical across all
four KNIME workflows and only the blockchain comparator varies.

```bash
python3 check_comparison_invariants.py
python3 check_comparison_invariants.py --json invariants.json
```

Exit codes: `0` invariants hold, `1` a constant leg varied, `2` inputs missing.
It reads the exported tables under `../benchmark/results/knime/` and needs no
KNIME installation. Results and their interpretation are documented in
[`../docs/comparison_results.md`](../docs/comparison_results.md).

---

## Hypothesis tests (H1, H2)

```bash
python3 hypothesis_tests.py
python3 hypothesis_tests.py --json results.json
```

One-tailed Mann-Whitney U with rank-biserial effect size and bootstrap
confidence intervals, plus a separation check and a **breakeven analysis** that
computes how much the modeled bank workflow would have to improve before the
advantage disappears. An exact paired sign test on shared trace IDs is included
as a robustness check because both systems use the same generated case IDs.
Standard library only; the U statistic and normal approximation with tie
correction are implemented directly. Results are scoped to the modeled study.

## H4 distributional calibration (pending row-level exports)

```bash
python3 h4_distribution_test.py \
  --bank ../benchmark/row_level/bank_random_n5000_seed42.csv \
  --proofrail ../benchmark/row_level/proofrail_random_n5000_seed42.csv \
  --json ../benchmark/results/h4_distribution_test.json
```

This reports two-sample KS D on `log1p(amount_usd)` and an asymptotic two-sided
p-value. It exits 2 while the required row-level files are absent. A large
p-value is not proof of equivalence.

## Tamper-detection experiment (H3, measured dimension)

```bash
python3 tamper_experiment.py --trials 240 --seed 42
```

Mutates a working copy of the audit chain (the original is never modified) using
six strategies — payload, action, timestamp, settlement reassignment, forged
entry hash, and deletion — and runs the production verifier against each.
Reports detection rate and localization accuracy as measured quantities rather
than rubric scores.

See [`../docs/hypothesis_evidence.md`](../docs/hypothesis_evidence.md) for how
each hypothesis is established and what remains open.
