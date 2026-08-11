# Row-Level KNIME Exports for H4

H4 cannot be computed from the aggregate `GroupBy` tables already published in
`benchmark/results/knime/`. Export the sampled rows from the final `Concatenate`
node before any `GroupBy` node and place two files here:

```text
bank_random_n5000_seed42.csv
proofrail_random_n5000_seed42.csv
```

Each file must contain `amount_usd`. Keep the fixed random seed at 42 and export
the sampled bank and ProofRail legs from the same workflow run. Do not export
the source population before sampling.

Then run:

```bash
python3 metrics/h4_distribution_test.py \
  --json benchmark/results/h4_distribution_test.json
```

The script uses `log1p(amount_usd)` so zero-valued journey events remain in the
declared banking sample. It reports the two-sample KS statistic and an
asymptotic two-sided p-value. Non-rejection does not establish equivalence; see
`docs/evidence_status.md` before writing the result.
