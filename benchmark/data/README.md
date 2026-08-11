# Frozen ProofRail Inputs

| File | Rows | Role |
|---|---:|---|
| `validation_cases.csv` | 75 | Performance evaluation for H1-H3 |
| `proofrail_synthetic_n5000_seed42.csv` | 5,000 | ProofRail leg of the KNIME characterization workflows |
| `generation_profile.json` | n/a | Seed, generator version, provenance, assumptions, and 75-case replay metadata |

Both CSV files are produced by `generator/settlesim_generator.py` with seed 42
and the indicated `--n` value. `scripts/check_generator_reproducibility.py`
regenerates both in temporary directories and requires byte-identical output.

The 5,000-row file is a generated workflow input, not a measured production
dataset. The generation profile's replay and conformance sections refer to the
75-case performance run.
