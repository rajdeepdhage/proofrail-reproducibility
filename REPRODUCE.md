# Reproducing the Results

Three levels of reproduction are possible, in increasing order of effort and
of what they establish.

---

## Level 1 — Verify the published results (no external data needed)

Confirms that the reported numbers follow from the published traces, and that
the audit-integrity claim holds. Requires only Python 3.9+.

```bash
# Recompute every headline metric from per-transaction traces and diff
# against the published summary tables.
python3 metrics/compute_metrics.py --check

# Independently recompute the hash chain of the sample audit log.
python3 verifier/verify_audit_chain.py verifier/sample_audit_chain.db

# Verify the four-comparison design invariants from the KNIME outputs.
python3 metrics/check_comparison_invariants.py

# Confirm no artifact in the repository has been modified.
bash scripts/verify.sh
```

Expected: `CHECK PASSED`, `CHAIN VERIFIED  440 entries`, the invariant check
confirming the bank and ProofRail legs are constant across all four comparisons,
and a clean manifest.

**Negative control.** The verifier should *fail* on a modified chain. To
confirm it is actually checking something:

```bash
cp verifier/sample_audit_chain.db /tmp/tampered.db
python3 - <<'PY'
import sqlite3
con = sqlite3.connect("/tmp/tampered.db")
row = con.execute("SELECT rowid FROM audit_log ORDER BY rowid LIMIT 1 OFFSET 3").fetchone()
con.execute("UPDATE audit_log SET details_json=? WHERE rowid=?", ('{"tampered":true}', row[0]))
con.commit(); con.close()
PY
python3 verifier/verify_audit_chain.py /tmp/tampered.db   # exits 1, names the entry
```

## Level 2 — Regenerate both ProofRail input populations

Confirms the case population is reproducible rather than hand-curated.

```bash
python3 generator/settlesim_generator.py --seed 42 --n 75 --out-dir /tmp/regenerated-75
python3 generator/settlesim_generator.py --seed 42 --n 5000 --out-dir /tmp/regenerated-5000

# Performs both comparisons automatically.
python3 scripts/check_generator_reproducibility.py
```

The seed and parameters used for the published population are recorded in
`benchmark/data/generation_profile.json`. The 75-case performance input is
`benchmark/data/validation_cases.csv`; the KNIME ProofRail input is
`benchmark/data/proofrail_synthetic_n5000_seed42.csv`. The automated check
requires both regenerated files to be byte-identical to their frozen copies.

## Level 3 — Re-run the full comparison

Requires the external datasets described in `DATA_ACCESS.md` and
[KNIME Analytics Platform](https://www.knime.com/) (free, open source).

1. Obtain the banking and blockchain datasets and place them at the paths in
   `DATA_ACCESS.md`.
2. Import the workflows from `knime/workflows/` into your KNIME workspace
   (`File > Import KNIME Workflow...`, selecting the workflow directory). See
   `knime/README.md`.
3. Repoint each `CSV Reader` node at your local copies of the source data. All
   other node settings — sampling seed, filters, formulas, aggregations — are
   preserved and should not need changing.
4. Execute each of the four comparison workflows:
   - `01_bank_proofrail_usdc`
   - `02_bank_proofrail_bitcoin`
   - `03_bank_proofrail_ethereum`
   - `04_bank_proofrail_smartcontract`
5. Exported tables should match those under `benchmark/results/knime/`. The
   bank and ProofRail figures must be identical across all four runs; if they
   are not, the sampling seed has changed.
6. For H4, also attach `CSV Writer` nodes to the final sampled bank and
   ProofRail branches before `GroupBy`. Export the two files named in
   `benchmark/row_level/README.md`, then run
   `python3 metrics/h4_distribution_test.py --json
   benchmark/results/h4_distribution_test.json`.

Even without re-executing, every node parameter can be inspected in KNIME, and
the design invariants can be checked from the exported tables alone with
`python3 metrics/check_comparison_invariants.py`.

Note that Level 3 re-runs the *data-characterization* layer. Re-running the
*performance-evaluation* layer (replaying cases through the engine) requires
the engine core, which is available to reviewers and committee members on
request — see the README.

---

## Environment

Results were produced with Python 3.11 and KNIME Analytics Platform 5.x.
The Level 1 and Level 2 scripts use only the Python standard library, so no
dependency pinning is required. Any Python 3.9 or later should reproduce them
exactly; the metrics are deterministic and involve no floating-point
parallelism.

Run `make release-check` before a DOI-bearing release. It is expected to fail
while H4 and permanent repository metadata are pending.
