# How ProofRail Works (In Principle)

This document describes the mechanism at the level needed to evaluate the
results. It is a design description, not an implementation guide; the engine
core is not published here (see the README for why, and for reviewer access).

## The problem

Payment rails in the United States are fast and reliable, but *conditionality*
— payment that completes only when defined real-world events have been verified,
and that can be held or reversed if they have not — is not a native capability
of the settlement layer. It is supplied manually: staff review documents,
approve releases, and handle disputes as procedure rather than as data. That
manual verification is expensive per transaction, and its cost falls hardest on
customers whose accounts generate the least revenue.

Tokenized settlement offers programmability but changes the trade-off. Base
ledger finality normally prevents unilateral rollback of a confirmed transfer;
recourse can still be implemented through application contracts, governance,
custodial controls, or a compensating transfer. The analyzed extracts do not
encode those mechanisms as terminal states comparable to ProofRail holds.

## The mechanism

ProofRail places conditionality inside the settlement record while leaving the
payment rail unchanged.

**1. Book-entry position.** Funds and ownership claims are recorded as
electronic accounting entries on the ledgers of regulated deposit institutions —
the same legal mechanism by which securities are held — not as tokens. Distinct
account structures separate held, released, and disputed balances. Because
settlement occurs by book entry rather than on-chain finality, a disputed
payment remains reversible.

**2. Typed evidence requirements.** Each settlement case declares the set of
event types that must be verified before release (for example, invoice approved
*and* delivery confirmed). Conditionality is therefore a property of the record,
expressed in data, rather than a workflow performed around it.

**3. Authenticated event intake.** Evidence arrives as messages from authorized
external sources — a logistics provider, an invoicing system — each authenticated
with HMAC-SHA256, a keyed hash that confirms both message integrity and sender
identity without requiring a distributed ledger or consensus. Authentication
establishes that a message genuinely originates from the declared source; it
does not, and cannot, establish that the real-world event asserted actually
occurred. This limit is stated explicitly in the thesis and is not claimed away.

**4. Deterministic rules evaluation.** When evidence arrives, a rules engine
evaluates whether the declared requirements are satisfied and produces one of
four outcomes: release, hold, dispute, or escalate. The decision is a function
of the recorded evidence, so the same inputs always yield the same outcome and
the reason is inspectable rather than discretionary.

**5. Hash-linked audit.** Every state change — hold opened, event received,
rules evaluated, funds released or reversed, condition expired, dispute raised —
is written to an append-only audit log in which each entry contains the
cryptographic hash of the previous entry:

```
entry_hash = SHA256(prev_hash | audit_id | settlement_id
                    | action | details_json | created_at_ms)
```

Altering any earlier record invalidates that record's hash and every hash after
it, which is what makes tampering evident rather than merely prohibited. The
verifier in this repository recomputes exactly this chain.

**6. Reversal as forward entry.** A reversal is recorded as a new, linked entry
rather than as an edit to a prior one. The chain is never rewritten, so
reversibility and tamper-evidence coexist. In this benchmark, that differs from
the on-chain transfer extracts, which record finality but not a comparable
recourse state, and from the modeled manual bank baseline, which does not include
ProofRail's independently verifiable hash-linked record.

## Case lifecycle

```
Case created
  -> value placed under conditional control (book entry)
  -> required event types declared
  -> event message received
  -> message authenticated (HMAC-SHA256)
  -> rules evaluated against declared requirements
  -> ledger updated, or case held / reversed / disputed
  -> hash-linked audit entry written
```

## What the benchmark measures

Three metrics, defined precisely in [`metrics.md`](metrics.md):

- **Authorization latency** — time from the final required piece of evidence to
  the settlement decision, with the payment rail held constant, so the
  comparison isolates the decision layer rather than rail throughput.
- **Verification burden** — manual review touches per case before completion.
- **Auditability** — a derived rubric over tamper-evidence, completeness,
  independent verifiability, and non-repudiation.

## Stated limitations

- Both the banking baseline and the ProofRail population are **synthetic**; only
  the blockchain comparison data are real. The distinguishing feature between
  the banking and ProofRail families is the settlement system each represents,
  not whether the data are synthetic.
- The bank workflow is **modeled**, because the source banking datasets do not
  expose internal approval, clearing, and reconciliation timestamps. Sensitivity
  ranges over the modeled assumptions are published alongside the point
  estimates.
- The ProofRail population is **calibrated** to the consolidated banking data.
  Distributional agreement between them is therefore a calibration check, not an
  independent finding.
- Improved auditability does not automatically reduce compliance cost, and no
  U.S. banking regulator has recognized cryptographic audit logs as satisfying
  compliance-documentation requirements.
- All results are **simulation-based demonstration evidence**, not measured
  production performance.
