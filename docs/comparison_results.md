# Four-Comparison Results (KNIME Data-Characterization Layer)

Results of the four three-way comparisons described in Chapter 2. Each holds the
bank and ProofRail legs constant and varies only the blockchain comparator, so
that ProofRail's position is tested against every major blockchain settlement
model rather than against a blended "crypto" average.

All four runs use **n = 5,000 records per system, seed 42**. Raw outputs are in
`../benchmark/results/knime/`; the workflows that produced them are in
`../knime/workflows/`.

---

## Design verification

The structural claim — bank and ProofRail held constant, blockchain varying — is
checked automatically rather than asserted:

```bash
python3 metrics/check_comparison_invariants.py
```

Result: the banking leg reports a mean of 70,763.32 USD and an exception rate of
0.1236 in **all four** workflows, and the ProofRail leg reports 4,692.25 USD and
0.2792 in **all four**, to within 1e-6. Only the blockchain figures differ. The
repeated-comparison design therefore does what it claims.

---

## Amount distributions

| Comparison | Blockchain mean (USD) | Blockchain median (USD) |
|---|---|---|
| USDC stablecoin | 29,441.11 | — |
| Bitcoin | 184,841.76 | — |
| Ethereum | 4,504.63 | 73.56 |
| Smart-contract events | n/a — non-monetary | n/a |

Constant legs: banking mean 70,763.32 (median 673.35); ProofRail mean 4,692.25
(median 2,509.34).

**Reading these figures.**

- **Means are not comparable across systems at face value.** The banking mean
  (70,763.32) sits two orders of magnitude above its own median (673.35), because
  the banking family is dominated by a small number of very large AML-dataset
  records: within the banking sample, `jpm_aml` averages 142,576.56 while
  `jpm_fraud_payment` averages 493.65. This is why the thesis compares
  distributional *shape* on a logarithmic scale rather than raw magnitude.
- **The blockchain spread is itself a finding.** Bitcoin's mean (184,841.76) and
  Ethereum's (4,504.63) differ by a factor of forty. Collapsing these into one
  "crypto" category — the approach this design deliberately rejects — would have
  produced an average describing none of them.
- **ProofRail's distribution is bank-realistic by construction**, since the
  population is calibrated to the consolidated banking data. Agreement here is a
  calibration check, not an independent finding.
- **Smart-contract events carry no monetary amount.** The comparison table for
  that workflow is restricted to the monetary systems, and contract activity is
  characterized separately by topic count (below). Excluding a non-monetary
  system from a monetary comparison is a deliberate choice, not a gap.

### Smart-contract event structure

| `topic_count` | Records |
|---|---|
| 1 | 675 |
| 2 | 715 |
| 3 | 3,063 |
| 4 | 547 |

Contract events are logged with indexed topics rather than transfer amounts,
which is precisely why they cannot be placed on a monetary axis alongside the
other systems.

---

## Exception rates — read this section before citing the numbers

| System | Exception rate | What an "exception" is in that system |
|---|---|---|
| Banking | 0.1236 | Fraud/AML-flagged records |
| ProofRail | 0.2792 | Cases **held or disputed** — value withheld pending evidence |
| USDC | 0.0000 | No exception state exists in transfer data |
| Ethereum | 0.0050 | Failed execution (`receipt_status`), *not* dispute or reversal |
| Bitcoin | not reported | No status field exists to compute one |
| Smart-contract | not reported | No status field exists to compute one |

**A naive reading of this table is wrong, and the thesis must pre-empt it.**
ProofRail shows the *highest* exception rate and the blockchain systems show the
lowest. Read as a performance ranking, that says ProofRail is the worst system
and Bitcoin the best. That reading inverts what the numbers mean.

- ProofRail's 27.9% is **the reversibility mechanism operating as designed**.
  Those are cases where required evidence was absent or a dispute was raised, so
  value was held rather than released. A held case is a payment that did *not*
  complete incorrectly.
- USDC's 0.0% and Bitcoin's and smart-contract's blanks are **not clean
  performance**. The analyzed extracts do not encode a held, disputed, or
  reversed state, so there is no commensurate event for this column to count.
- Ethereum's 0.5% is **failed execution**, not recourse. A transaction that
  reverts is not a payment held pending evidence; the distinction matters and
  should not be blurred by placing the two numbers in the same column without
  comment.

This is descriptive evidence for hypothesis **H5**: terminal-state coding
differs across the analyzed extracts. It is not proof that every blockchain
protocol or smart-contract design lacks recourse. The paper should distinguish
an absent field in an extract from a protocol-level impossibility claim.

**Recommended presentation.** Do not report exception rate as a single ranked
column. Report terminal-state *composition* per dataset and state explicitly
which states the extract records. A blank is more honest than a zero where a
commensurate field does not exist.

---

## Dataset inventory and provenance

Every workflow emits a provenance table. Composition of the banking sample
(5,000 records, consistent across all four runs):

| Source dataset | System | Provenance | Records |
|---|---|---|---|
| `jpm_fraud_payment` | banking | synthetic_research | 2,481 |
| `jpm_aml` | banking | synthetic_research | 2,473 |
| `jpm_customer_journey` | banking | synthetic_research | 46 |
| `proofrail_synthetic` | proofrail | synthetic_research | 5,000 |
| blockchain source | blockchain | crypto_onchain | 5,000 |

Two provenance notes that belong in any write-up of these figures:

1. **`provenance` distinguishes the data's origin, not its quality.** Both the
   banking and ProofRail rows are `synthetic_research`; only the blockchain rows
   are `crypto_onchain` (real). The banking comparator is as synthetic as the
   ProofRail comparator, and the study is a systems comparison under controlled
   data conditions.
2. **The 46 customer-journey records carry no monetary amount** (mean 0), since
   that dataset records channel events rather than transfers. They are a small
   fraction of the banking sample but do slightly depress the banking amount
   statistics; the effect is disclosed rather than silently corrected.

---

## What this layer does and does not establish

These results are the **data-characterization layer**: they describe what each
sample looks like and which terminal states each extract records. They provide
descriptive H5 evidence. H4 remains pending until the row-level bank and
ProofRail exports are tested.

They do **not** measure authorization latency, verification burden, or
auditability. Those are the performance-evaluation layer (H1–H3), produced by
replaying the case population through the prototype and the modeled baselines,
and reported in `../benchmark/results/comparison_summary_by_system.csv`.
Keeping the two layers separate is what keeps the instrument that characterizes
the data (KNIME) independent of the artifact under evaluation.
