# Metric Definitions

Every number reported in the thesis and in this repository's README is computed
from the per-transaction traces in `benchmark/logs/` using the definitions
below. `metrics/compute_metrics.py` implements them and diffs its output
against the published summary tables.

---

## Authorization latency

**Definition.** Elapsed seconds from the arrival of the final required piece of
evidence to the settlement decision.

**Why it is defined narrowly.** Total settlement time is dominated by the
payment rail (ACH, FedNow, Fedwire, or block inclusion). Holding the rail
constant and measuring only the decision layer is what makes the comparison
about conditional settlement rather than about rail throughput.

**Per system:**

| System | Basis |
|---|---|
| Manual bank workflow | modeled time for verification and approval once required information is available |
| ProofRail | final required event received -> rules decision -> ledger update |
| Blockchain systems | block-inclusion time, reported as an on-chain recording reference; *not* a manual-workflow-equivalent latency and not the object of the directional test |

**Reported as.** Mean, p50, and p90. Percentiles use linear interpolation
between the nearest ranks. Distributions are skewed, so the median and p90 are
reported alongside the mean rather than the mean alone.

**Source column.** `authorization_latency_s` in
`benchmark/logs/normalized_comparison_rows.csv`, with
`authorization_latency_basis` recording how each value was derived.

**Missing outcome note.** All 75 bank rows have a value; 70 released ProofRail
rows have a value. Five held/disputed ProofRail rows do not have a
release-authorization latency under this definition. Report valid n with every
H1 estimate. The paired robustness check uses the 70 trace IDs observed in both
systems.

---

## Verification burden (manual touches)

**Definition.** Count of distinct human or operational review steps required per
case before completion.

**What counts as a touch.** In the modeled bank workflow: customer review,
account review, fraud screening, AML review, sanctions review, document review,
supervisor approval, and exception handling. In ProofRail: any step requiring
human intervention, counted directly from the simulated lifecycle.

**Interpretation caveat.** The blockchain systems show near-zero *observable*
touches because public on-chain data record token movement, not off-chain
review. This does not mean no off-chain burden exists — only that these data
cannot evidence it. The metric is therefore compared primarily between the bank
workflow and ProofRail.

**Source column.** `manual_touch_count`. The complementary
`automated_check_count` records machine-performed checks, and the two together
show substitution rather than mere elimination.

---

## Auditability

**Definition.** A derived rubric scoring the transaction record on four
dimensions, each scored independently and summed into a rollup:

| Dimension | Question |
|---|---|
| Tamper-evidence | Would alteration of the record be detectable? |
| Completeness | Are identifiers, timestamps, parties, amount, status, and event history present? |
| Independent verifiability | Could another party confirm the record using cryptographic or external evidence? |
| Non-repudiation | Can the record be attributed to its originator and reconstructed? |

**Expected profile.** Banking data score well on internal completeness but
poorly on externally visible tamper-evidence. Blockchain data score well on
independent verifiability but poorly on off-chain condition evidence. ProofRail
is designed to score on both lifecycle completeness and tamper-evidence.

**This is a researcher-constructed rubric,** not a standard instrument. It is
published in full here so that a reader who disagrees with the weighting can
recompute it from the component columns: `tamper_evidence`, `completeness`,
`independent_verifiability`, and `non_repudiation`. `compute_metrics.py`
independently re-derives the rollup from these four components and reports a
failure if the stored rollup disagrees with their sum.

---

## Statistical treatment

Amounts and timings are skewed, so the completed H1/H2 analysis uses one-tailed
Mann-Whitney U, rank-biserial effect size, bootstrap intervals, and an exact
paired sign robustness check. H3's rubric is descriptive; only its tamper
detection dimension is experimentally mutated and measured. H4's planned
two-sample KS check on log-transformed row-level amounts is pending those
exports. H5's chi-square table is exploratory because the available status
fields do not encode equivalent constructs across systems. Effect sizes,
observation counts, model scope, and practical magnitudes are emphasized over
p-values alone.

The comparison design runs the same three-way comparison four times, holding the
bank and ProofRail legs constant while varying the blockchain comparator. The
bank-versus-ProofRail contrasts are computed once and are identical across the
four runs; only the blockchain-dependent contrasts are re-evaluated per system,
and those are reported per system rather than pooled, so repetition does not
inflate significance.
