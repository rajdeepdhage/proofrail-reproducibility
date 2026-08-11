# Data Access

Two categories of source data used in the study are **not redistributed** in
this repository. This file gives a replicator everything needed to obtain
equivalent data and place it where the workflows expect it.

---

## 1. J.P. Morgan AI Research synthetic banking datasets

These datasets are published by J.P. Morgan AI Research and made available to
researchers **on request**. They may not be redistributed by third parties, so
they are not included here.

**How to obtain:** request access from J.P. Morgan AI Research at
`airdata.requests@jpmorgan.com`, referencing the synthetic-data program:
<https://www.jpmorganchase.com/about/technology/research/ai/synthetic-data>

**Required attribution.** Any publication using these datasets must include:

> This publication includes or references synthetic data provided by J.P. Morgan.

**Datasets used, and their role in the study:**

| Dataset | Role | Key columns used |
|---|---|---|
| Payments Data for Fraud Protection | Primary banking comparator; amount distribution and terminal states | `Transaction_Id`, `Sender_Id`, `Sender_Account`, `Sender_Country`, `Sender_Sector`, `Sender_Job`, `Bene_Id`, `Bene_Account`, `Bene_Country`, `USD_amount`, `Transaction_Type`, `Label` |
| Anti-Money Laundering (AML) | Compliance-risk context | time step, label (`GOOD`/`BAD`), action and arguments |
| Customer Journey Event | Event-sequence template for the manual-touch model | `Time step`, `Label`, `Event`, `Customer id` |

**Expected local placement** (matches `benchmark/results/dataset_inventory.csv`):

```
data/bank/fraud_payment_data.csv
data/bank/aml_syn_data.csv
data/bank/customer_journey_data.csv
```

Column names in a newly requested copy should be confirmed against the
dictionary in `docs/schema.md` before running the workflows; if the publisher
has revised the schema, update the KNIME `Column Renamer` nodes accordingly.

---

## 2. Blockchain transaction data

Public on-chain data were extracted for four settlement systems. Extraction
specifications are given here rather than redistributing the extracts, whose
onward-distribution terms depend on the source used.

| System | Role in the study | Fields required |
|---|---|---|
| Bitcoin | Non-programmable UTXO settlement baseline | `tx_hash`, `block_timestamp`, `input_count`, `output_count`, `input_value`, `output_value`, `fee` |
| Ethereum | Programmable account-model settlement | `tx_hash`, `block_timestamp`, `block_number`, `from_address`, `to_address`, `value`, `gas`, `receipt_gas_used`, `receipt_status` |
| Smart-contract events | Conditional on-chain logic and its logging | `transaction_hash`, `block_timestamp`, `contract_address`, `topic_count` |
| USDC stablecoin transfers | Dollar-denominated token settlement | `transaction_hash`, `block_timestamp`, `block_number`, `from_address`, `to_address`, `token_amount`, `token_address` |

**Notes for replicators:**

- `token_amount` for USDC is an integer in the token's base units. USDC uses six
  decimal places, so divide by 1,000,000 to obtain dollar units. This conversion
  is performed by a `Math Formula` node in the comparison workflow.
- `block_timestamp` is the time of *block inclusion*, not transaction
  initiation. Timestamps are compared within a system, never across systems.
- The analyzed blockchain extracts do not contain a field directly comparable
  to ProofRail's held or disputed state. This is a property of the supplied
  schemas, not proof that every blockchain protocol or smart contract is unable
  to implement recourse. H5 must be written with that boundary.

**Expected local placement:**

```
data/crypto/bitcoin_transactions.csv
data/crypto/ethereum_transactions.csv
data/crypto/smart_contract_events.csv
data/crypto/usdc_transfers.csv
```

---

## 3. Data that *is* included here

The synthetic case population generated for this study (`benchmark/data/`), all
execution traces (`benchmark/logs/`), and all result tables
(`benchmark/results/`) are included under CC BY 4.0 and require no external
request. The population can also be regenerated from its seed — see
`REPRODUCE.md`.
