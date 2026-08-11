#!/usr/bin/env python3
"""
ProofRail standalone audit-chain verifier (read-only).

Independently recomputes the hash chain of a ProofRail audit log and reports
whether it is intact. This tool contains no settlement logic and never writes
to the database: it exists so that a reviewer can confirm the tamper-evidence
claims in the thesis without trusting -- or having access to -- the engine
that produced the chain.

Chain construction (as verified here):

    entry_hash = SHA256( prev_hash | audit_id | settlement_id
                         | action | details_json | created_at_ms )

with the first entry's prev_hash fixed to the literal string "GENESIS", and
each subsequent entry's prev_hash equal to the previous entry's entry_hash.
Any modification to a record therefore invalidates that record's hash and
every hash after it.

Usage:
    python verify_audit_chain.py sample_audit_chain.db
    python verify_audit_chain.py sample_audit_chain.db --json
    python verify_audit_chain.py backup.json          # audit backup snapshot

Exit codes:  0 = chain verified,  1 = chain broken,  2 = could not read input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List

GENESIS = "GENESIS"
COLUMNS = (
    "rowid, audit_id, settlement_id, action, details_json, "
    "created_at_ms, prev_hash, entry_hash"
)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def entry_material(row: Dict[str, Any]) -> str:
    """Exact preimage used to compute an entry hash."""
    return (
        f"{row['prev_hash']}|{row['audit_id']}|{row['settlement_id']}|"
        f"{row['action']}|{row['details_json']}|{row['created_at_ms']}"
    )


def load_from_sqlite(path: Path) -> List[Dict[str, Any]]:
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            f"SELECT {COLUMNS} FROM audit_log ORDER BY rowid ASC"
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "rowid": int(r["rowid"]),
            "audit_id": str(r["audit_id"]),
            "settlement_id": str(r["settlement_id"] or ""),
            "action": str(r["action"]),
            "details_json": str(r["details_json"]),
            "created_at_ms": int(r["created_at_ms"]),
            "prev_hash": str(r["prev_hash"]),
            "entry_hash": str(r["entry_hash"]),
        }
        for r in rows
    ]


def load_from_json(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise ValueError("JSON input does not contain an 'entries' list")
    return entries


def verify(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Recompute the chain. Returns a result dict; never raises on bad data."""
    prev = GENESIS
    for index, row in enumerate(entries):
        try:
            if row["prev_hash"] != prev:
                return {
                    "ok": False,
                    "entries_total": len(entries),
                    "entries_verified": index,
                    "failed_at_index": index,
                    "failed_audit_id": row.get("audit_id", "?"),
                    "error": (
                        f"Broken chain at {row.get('audit_id', '?')}: "
                        f"prev_hash mismatch"
                    ),
                }
            recomputed = sha256_hex(entry_material(row))
            if recomputed != row["entry_hash"]:
                return {
                    "ok": False,
                    "entries_total": len(entries),
                    "entries_verified": index,
                    "failed_at_index": index,
                    "failed_audit_id": row.get("audit_id", "?"),
                    "expected_hash": recomputed,
                    "stored_hash": row["entry_hash"],
                    "error": f"Hash mismatch at {row.get('audit_id', '?')}",
                }
            prev = row["entry_hash"]
        except KeyError as exc:
            return {
                "ok": False,
                "entries_total": len(entries),
                "entries_verified": index,
                "error": f"Entry {index} is missing required field {exc}",
            }
    return {
        "ok": True,
        "entries_total": len(entries),
        "entries_verified": len(entries),
        "head_hash": prev,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="SQLite .db or audit-backup .json file")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"error: no such file: {path}", file=sys.stderr)
        return 2
    try:
        entries = (load_from_json(path) if path.suffix.lower() == ".json"
                   else load_from_sqlite(path))
    except Exception as exc:
        print(f"error: could not read audit log: {exc}", file=sys.stderr)
        return 2

    result = verify(entries)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["ok"]:
        print(f"CHAIN VERIFIED  {result['entries_verified']} entries")
        print(f"head hash       {result['head_hash']}")
        print(f"source          {path}")
    else:
        print("CHAIN VERIFICATION FAILED")
        print(f"  {result['error']}")
        print(f"  verified {result['entries_verified']} of "
              f"{result['entries_total']} entries before failure")
        if "expected_hash" in result:
            print(f"  expected {result['expected_hash']}")
            print(f"  stored   {result['stored_hash']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
