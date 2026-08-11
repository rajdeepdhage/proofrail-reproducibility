# Standalone Audit-Chain Verifier

Read-only tool that independently recomputes the hash chain of a ProofRail audit
log. It contains no settlement logic, shares no code with the engine that wrote
the chain, and never writes to the database.

```bash
python3 verify_audit_chain.py sample_audit_chain.db
python3 verify_audit_chain.py sample_audit_chain.db --json
```

Exit codes: `0` chain verified, `1` chain broken, `2` input unreadable.

Chain construction:

```
entry_hash = SHA256(prev_hash | audit_id | settlement_id
                    | action | details_json | created_at_ms)
```

with the first entry's `prev_hash` fixed to `GENESIS`. Altering any record
invalidates its hash and every hash after it.

`sample_audit_chain.db` contains 440 real entries from the published run. To
confirm the verifier is genuinely checking, run the negative control in
[`../REPRODUCE.md`](../REPRODUCE.md): mutate a copy and observe the failure,
which names the first invalid entry.
