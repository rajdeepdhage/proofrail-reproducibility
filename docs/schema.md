# Data Dictionary

Column definitions for every file published in this repository. Column names
are reproduced exactly as they appear in the files.

---

## `benchmark/data/validation_cases.csv` — the frozen input population

The synthetic business-to-business conditional-payment cases that both the
ProofRail engine and the modeled bank workflow process. 22 columns.

### Case identity and value

| Column | Type | Meaning |
|---|---|---|
| `transaction_id` | string | Unique case identifier; the join key to every trace |
| `payer_id` | string | Paying counterparty |
| `payee_id` | string | Receiving counterparty |
| `amount_usd` | float | Case value in U.S. dollars |
| `currency` | string | Currency code (USD throughout this population) |
| `created_offset_s` | integer | Arrival time in seconds from population start |

### Conditionality — fields with no equivalent in the comparator families

| Column | Type | Meaning |
|---|---|---|
| `transaction_type` | enum | `INVOICE_PAYMENT`, `MILESTONE_PAYMENT`, conditional goods hold, or `SERVICE_RETAINER` |
| `required_events` | pipe-separated list | Evidence event types that must be verified before release (e.g. `INVOICE_APPROVED\|DELIVERY_CONFIRMED`). **This is the variable that makes a payment conditional rather than immediate.** |
| `scenario` | enum | Generative condition: `normal`, `delayed`, `disputed`, or `exception` |
| `expected_outcome` | enum | **Ground-truth oracle**: `RELEASED`, `HELD`, or `DISPUTED`. Because every case carries its correct terminal state, engine decisions can be scored for conformance. |

### Bank-realism fields (mirroring the banking schema for calibration)

| Column | Type | Meaning |
|---|---|---|
| `internal_case_id` | string | Institution-side case reference |
| `payment_instruction_id` | string | Payment instruction reference |
| `bank_channel` | string | Origination channel |
| `bank_product` | string | Product classification |
| `sender_country` / `bene_country` | string | Originator and beneficiary jurisdictions |
| `sender_sector` | string | Originator industry sector |
| `sender_lob` | string | Originator line of business |
| `risk_score` | float | Modeled risk score |
| `risk_band` | enum | Banded risk classification |
| `bank_label` | string | Bank-side outcome label, comparable to the fraud dataset's `Label` |
| `manual_review_expected` | boolean | Whether the modeled bank workflow routes this case to manual review |

---

## `benchmark/logs/normalized_comparison_rows.csv` — per-case outcomes

One row per case per system: the direct evidence base for every reported metric.

| Column | Meaning |
|---|---|
| `trace_id` | Case identifier, joins to `transaction_id` |
| `architecture` | `bank` or `prototype` |
| `system_type` | `bank_manual` or `conditional_settlement_prototype` |
| `status` | Terminal state reached |
| `amount_usd` | Case value |
| `authorization_latency_s` | **H1 metric.** Seconds from final required evidence to settlement decision |
| `authorization_latency_basis` | How that value was derived for this system (modeled, measured, or block-inclusion reference) |
| `end_to_end_time_s` | Full elapsed time including rail effects (context, not the headline metric) |
| `chain_finality_s` | On-chain finality time where applicable |
| `manual_touch_count` | **H2 metric.** Human/operational review steps required |
| `automated_check_count` | Machine-performed checks — shows substitution, not mere elimination |
| `tamper_evidence` | **H3 component.** Would alteration be detectable? |
| `completeness` | **H3 component.** Are all record fields present? |
| `independent_verifiability` | **H3 component.** Could a third party confirm the record? |
| `non_repudiation` | **H3 component.** Is the record attributable and reconstructable? |
| `auditability_rollup` | Sum of the four components above |
| `auditability_score` | Reported auditability figure |
| `irreversible_dispute` | Study-coded indicator that a dispute was not reversed in that modeled trace; do not generalize it to protocol-wide capability (H5) |
| `settlement_time_s` | Time to settlement |
| `verification_burden` | Reported verification-burden figure |
| `audit_evidence_available` | Whether audit evidence exists for this case |
| `event_count` | Number of evidence events received |
| `metric_basis` | Whether values are measured from execution or modeled |
| `source_file` | Contributing source file, preserving decomposability |

---

## `benchmark/logs/combined_step_log.csv` — per-step traces

One row per lifecycle *step*, so a reviewer can see how each case-level number
was accumulated rather than only its total.

| Column | Meaning |
|---|---|
| `source_file` | Contributing log |
| `trace_id` | Case identifier |
| `architecture` / `system_type` | System that executed the step |
| `step_name` | The step performed |
| `step_category` | `initiation`, `verification`, `decision`, `settlement`, or `audit` |
| `timestamp` / `timestamp_epoch_s` | Step time, human-readable and epoch seconds |
| `amount_usd` | Case value |
| `verification_required` | Whether this step required verification |
| `manual_review_flag` | Whether this step was a manual touch (summing these yields `manual_touch_count`) |
| `exception_flag` | Whether an exception occurred |
| `manual_touch_count` / `automated_check_count` | Running counts |
| `tamper_evidence`, `completeness`, `independent_verifiability`, `non_repudiation` | Rubric components at this step |
| `auditability_rollup` / `auditability_score` | Rubric totals |
| `final_outcome` | Terminal state of the case |

`benchmark/logs/prototype_step_log.csv` and `bank_manual_step_log.csv` are the
per-system sources that `combined_step_log.csv` consolidates.

---

## `benchmark/results/` — published outputs

| File | Contents |
|---|---|
| `comparison_summary_by_system.csv` | Headline table: metrics aggregated per system |
| `comparison_summary_by_architecture.csv` | Same, aggregated per architecture |
| `dataset_inventory.csv` | Every dataset used, with family, path, row count, and column count |
| `analysis_report.json` | Full analysis output |
| `bank_sensitivity_sweep.json` | Sensitivity ranges over the modeled bank-workflow assumptions — read alongside the point estimates |
| `PROVENANCE.json` | Generator kind and version, seed, scope notice, sensitivity result ranges |

---

## `verifier/sample_audit_chain.db` — audit log

SQLite. Table `audit_log`, 440 entries.

| Column | Meaning |
|---|---|
| `rowid` | Chain position (ascending) |
| `audit_id` | Unique entry identifier |
| `settlement_id` | Case the entry concerns |
| `action` | State change recorded |
| `details_json` | Entry payload |
| `created_at_ms` | Entry time, epoch milliseconds |
| `prev_hash` | Hash of the preceding entry; `GENESIS` for the first |
| `entry_hash` | `SHA256(prev_hash \| audit_id \| settlement_id \| action \| details_json \| created_at_ms)` |

---

## `benchmark/results/knime/` — four-comparison outputs

One directory per comparison, each containing tables exported by that KNIME
workflow. All runs use n = 5,000 records per system, seed 42.

### `amount_comparison_*.csv`

| Column | Meaning |
|---|---|
| `system_type` | `banking`, `blockchain`, or `proofrail` |
| `First(transaction_id)` or `Count(transaction_id)` | Sample identifier or record count |
| `Mean(amount_usd)` | Mean transaction value |
| `Min*(amount_usd)` / `Max*(amount_usd)` | Range |
| `Median(amount_usd)` | Median value (present in comparisons 3 and 4) |

Means and medians diverge sharply for the banking family; compare distributional
shape on a logarithmic scale rather than raw magnitude.

### `exception_rate_*.csv`

| Column | Meaning |
|---|---|
| `system_type` | System |
| `Count(transaction_id)` | Records evaluated |
| `Mean(exception_int)` | Proportion flagged as exceptions |
| `Sum(exception_int)` | Count flagged |

An "exception" means something different in each system: fraud/AML flag in
banking, held-or-disputed case in ProofRail, failed execution in Ethereum. Where
a system has no status field, no row is emitted rather than a zero. See
[`comparison_results.md`](comparison_results.md) before citing these figures.

### `dataset_inventory_*.csv`

| Column | Meaning |
|---|---|
| `source_dataset` | Contributing file (`jpm_fraud_payment`, `jpm_aml`, `jpm_customer_journey`, `proofrail_synthetic`, blockchain source) |
| `system_type` | Family the source belongs to |
| `provenance` | `synthetic_research` or `crypto_onchain` — origin of the data, not a quality judgement |
| `Count(transaction_id)` | Records contributed |
| `Mean(amount_usd)` | Mean value where applicable |

### `smart_contract_topic_distribution_*.csv`

| Column | Meaning |
|---|---|
| `topic_count` | Number of indexed event topics logged by the contract call |
| `Count(transaction_id)` | Records with that topic count |

Contract events carry no monetary amount, so they are characterized by event
structure rather than value.
