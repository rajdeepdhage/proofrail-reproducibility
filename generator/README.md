# SettleSim — Synthetic Case Generator

Produces the business-to-business conditional-payment population used as input
to both the ProofRail engine and the modeled bank workflow.

Generation is deterministic: a fixed seed reproduces an identical population,
which is what makes the benchmark inputs auditable rather than hand-curated.
The seed and parameters used for the published population are recorded in
`../benchmark/data/generation_profile.json`.

```bash
# Performance-evaluation input.
python3 settlesim_generator.py --seed 42 --n 75 --out-dir /tmp/regenerated-75

# ProofRail input used by the KNIME characterization workflows.
python3 settlesim_generator.py --seed 42 --n 5000 --out-dir /tmp/regenerated-5000
```

The frozen copies are `../benchmark/data/validation_cases.csv` and
`../benchmark/data/proofrail_synthetic_n5000_seed42.csv`. Run
`python3 ../scripts/check_generator_reproducibility.py` to regenerate and hash
both automatically.

Key options: `--n` (case count), `--seed` (random seed), `--out-dir` (output
directory), `--amount-floor` / `--amount-cap` (amount bounds). Run with
`--help` for the full list.

Each generated case carries a ground-truth `expected_outcome`, so engine
decisions can be scored for conformance rather than merely inspected. Column
definitions are in [`../docs/schema.md`](../docs/schema.md).

Note that the conformance test confirms the implementation matches the
specification; it does not establish that the specification is the correct
design. This limitation is recorded in the generation profile itself.
