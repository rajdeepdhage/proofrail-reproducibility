# KNIME Workflows

The comparison analysis is implemented in [KNIME Analytics Platform](https://www.knime.com/)
(free, open source) rather than in author-written code, so that the analysis
instrument is independent of the artifact under evaluation and can be inspected
node by node by a reader who does not program.

## The four comparisons

Each workflow runs the same three-way comparison, holding the bank and ProofRail
legs constant and varying only the blockchain comparator. All four use
**n = 5,000 records per system, seed 42**.

| Workflow | Comparison | Nodes |
|---|---|---|
| `workflows/01_bank_proofrail_usdc/` | Bank vs. ProofRail vs. USDC stablecoin | 43 |
| `workflows/02_bank_proofrail_bitcoin/` | Bank vs. ProofRail vs. Bitcoin | 44 |
| `workflows/03_bank_proofrail_ethereum/` | Bank vs. ProofRail vs. Ethereum | 43 |
| `workflows/04_bank_proofrail_smartcontract/` | Bank vs. ProofRail vs. smart-contract events | 48 |

Rendered workflow graphs are in `figures/` as SVG (exported by KNIME), and are
the images used as figures in the thesis.

## Opening a workflow

Each directory is a KNIME workflow folder. Copy it into your KNIME workspace and
open it from the KNIME Explorer, or use `File > Import KNIME Workflow...` and
select the directory.

Node settings are preserved, so every parameter — sampling seeds, filters,
formulas, aggregations — is inspectable without running anything. To re-execute,
obtain the source datasets first (see [`../DATA_ACCESS.md`](../DATA_ACCESS.md))
and repoint the `CSV Reader` nodes at your local copies.

## Structure

Every comparison workflow follows the same shape:

1. **Ingest** — one `CSV Reader` per source file (three banking files, one
   ProofRail file, one blockchain file).
2. **Harmonize** — `Column Renamer` maps each source to the shared schema;
   `Constant Value Column Appender` tags `system_type`, `source_dataset`, and
   `provenance`.
3. **Convert** — the USDC branch applies a `Math Formula` node dividing
   `token_amount` by 1,000,000 (USDC uses six decimal places).
4. **Combine** — `Concatenate` merges the harmonized branches.
5. **Balance** — `Row Filter` then `Row Sampler` draws n = 5,000 per system with
   a fixed seed, so the large banking source does not dominate.
6. **Compare** — `GroupBy` and `Rule Engine` produce the amount comparison,
   exception rate, and dataset inventory tables.
7. **Export** — `CSV Writer` nodes emit the tables reproduced under
   `../benchmark/results/knime/`.

The frozen ProofRail source for these workflows is
`../benchmark/data/proofrail_synthetic_n5000_seed42.csv`. H4 additionally needs
the sampled bank and ProofRail rows exported before `GroupBy`; the exact file
contract is in `../benchmark/row_level/README.md`.

## Verifying the design without KNIME

The structural claim that the bank and ProofRail legs are constant across all
four workflows can be checked directly from the exported tables, with no KNIME
installation:

```bash
python3 ../metrics/check_comparison_invariants.py
```

## Interpreting the outputs

See [`../docs/comparison_results.md`](../docs/comparison_results.md). Read the
exception-rate section before citing those figures — the numbers are easy to
misread as a performance ranking when they are actually evidence about which
terminal states each analyzed extract records.
