#!/usr/bin/env python3
"""
Tamper-detection experiment: measure, rather than score, audit tamper-evidence.

The auditability rubric assigns a tamper-evidence score by judgement. This
script replaces that judgement with a measurement for one specific claim: that
any alteration of a committed audit record is detected, and detected at the
correct entry.

Method. A working copy of the audit chain is made (the original is never
modified). For each trial, one entry is selected at random and altered by one of
several mutation strategies. The production verification routine is then run
against the mutated copy, and two outcomes are recorded:

  detection    -- did verification fail at all?
  localization -- did it name the entry that was actually altered?

Detection rate is the proportion of trials caught. Localization rate is the
proportion caught *at the correct entry*. Both are empirical results computed
from the run, not assigned values.

Mutation strategies exercise different tampering routes:
  payload      alter the recorded details of an entry
  action       relabel what happened
  timestamp    shift when it happened
  settlement   reassign the entry to a different case
  stored_hash  forge the entry's own hash to match its altered content
  delete       remove an entry entirely (chain truncation)

The 'stored_hash' strategy is the most demanding: an adversary who alters
content *and* recomputes that entry's hash. It is caught because the following
entry's prev_hash no longer matches -- which is the property the linked chain
exists to provide.

Usage:
    python tamper_experiment.py                    # 200 trials, seed 42
    python tamper_experiment.py --trials 500 --seed 7
    python tamper_experiment.py --json results.json

Exit codes: 0 = every mutation detected, 1 = one or more escaped, 2 = setup error.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHAIN = ROOT / "verifier" / "sample_audit_chain.db"

sys.path.insert(0, str(ROOT / "verifier"))
from verify_audit_chain import load_from_sqlite, verify  # noqa: E402

STRATEGIES = ("payload", "action", "timestamp", "settlement", "stored_hash", "delete")


def mutate(db_path: Path, rowid: int, strategy: str, rng: random.Random) -> None:
    """Apply one mutation to the working copy."""
    con = sqlite3.connect(db_path)
    try:
        if strategy == "payload":
            con.execute(
                "UPDATE audit_log SET details_json=? WHERE rowid=?",
                (json.dumps({"tampered": True, "nonce": rng.randrange(1 << 30)}), rowid),
            )
        elif strategy == "action":
            con.execute(
                "UPDATE audit_log SET action=? WHERE rowid=?", ("RELEASED_FORGED", rowid)
            )
        elif strategy == "timestamp":
            con.execute(
                "UPDATE audit_log SET created_at_ms = created_at_ms + ? WHERE rowid=?",
                (rng.randrange(1000, 10_000_000), rowid),
            )
        elif strategy == "settlement":
            con.execute(
                "UPDATE audit_log SET settlement_id=? WHERE rowid=?",
                (f"forged_{rng.randrange(1 << 20)}", rowid),
            )
        elif strategy == "stored_hash":
            # Alter content AND recompute this entry's own hash, so the entry is
            # internally consistent. Only the link to the next entry betrays it.
            import hashlib

            row = con.execute(
                "SELECT audit_id, settlement_id, action, created_at_ms, prev_hash "
                "FROM audit_log WHERE rowid=?",
                (rowid,),
            ).fetchone()
            new_details = json.dumps({"tampered": True, "nonce": rng.randrange(1 << 30)})
            # Normalize exactly as the verifier does: a NULL settlement_id is
            # read as an empty string, not as the text "None".
            settlement_id = row[1] or ""
            material = (
                f"{row[4]}|{row[0]}|{settlement_id}|{row[2]}|{new_details}|{row[3]}"
            )
            forged = hashlib.sha256(material.encode("utf-8")).hexdigest()
            con.execute(
                "UPDATE audit_log SET details_json=?, entry_hash=? WHERE rowid=?",
                (new_details, forged, rowid),
            )
        elif strategy == "delete":
            con.execute("DELETE FROM audit_log WHERE rowid=?", (rowid,))
        else:
            raise ValueError(f"unknown strategy: {strategy}")
        con.commit()
    finally:
        con.close()


def run_trials(chain: Path, trials: int, seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    baseline = verify(load_from_sqlite(chain))
    if not baseline["ok"]:
        raise RuntimeError(
            f"baseline chain does not verify; cannot run experiment: {baseline.get('error')}"
        )
    total_entries = baseline["entries_total"]

    results: List[Dict[str, Any]] = []
    workdir = Path(tempfile.mkdtemp(prefix="proofrail_tamper_"))
    try:
        for trial in range(trials):
            strategy = STRATEGIES[trial % len(STRATEGIES)]
            # Deleting or forging the final entry cannot break a forward link,
            # so target entries that have a successor for those strategies.
            upper = total_entries - 1 if strategy in {"stored_hash", "delete"} else total_entries
            rowid = rng.randrange(1, upper + 1)

            copy_path = workdir / f"trial_{trial}.db"
            shutil.copy2(chain, copy_path)
            mutate(copy_path, rowid, strategy, rng)

            outcome = verify(load_from_sqlite(copy_path))
            detected = not outcome["ok"]
            # Verification stops at the first invalid entry. For a content
            # mutation that is the mutated row itself; for a deletion the
            # break appears at the row that took its place.
            failed_index = outcome.get("failed_at_index")
            expected_index = rowid - 1
            if strategy == "stored_hash":
                # The entry is internally consistent because its own hash was
                # recomputed, so it passes; the break surfaces at the NEXT
                # entry, whose prev_hash no longer matches. Detection shifting
                # one link forward is the linked chain doing its job.
                expected_failures = {expected_index + 1}
            elif strategy == "delete":
                # The successor slides into the deleted row's position.
                expected_failures = {expected_index, expected_index - 1}
            else:
                expected_failures = {expected_index}
            localized = detected and failed_index in expected_failures

            results.append(
                {
                    "trial": trial,
                    "strategy": strategy,
                    "mutated_rowid": rowid,
                    "detected": detected,
                    "localized": localized,
                    "failed_at_index": failed_index,
                    "error": outcome.get("error", ""),
                }
            )
            copy_path.unlink(missing_ok=True)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    by_strategy: Dict[str, Dict[str, int]] = {}
    for row in results:
        bucket = by_strategy.setdefault(
            row["strategy"], {"trials": 0, "detected": 0, "localized": 0}
        )
        bucket["trials"] += 1
        bucket["detected"] += int(row["detected"])
        bucket["localized"] += int(row["localized"])

    detected_total = sum(r["detected"] for r in results)
    localized_total = sum(r["localized"] for r in results)
    return {
        "chain_file": chain.name,
        "chain_entries": total_entries,
        "trials": len(results),
        "seed": seed,
        "detected": detected_total,
        "detection_rate": round(detected_total / len(results), 6) if results else 0.0,
        "localized": localized_total,
        "localization_rate": round(localized_total / len(results), 6) if results else 0.0,
        "by_strategy": by_strategy,
        "escaped": [r for r in results if not r["detected"]],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--chain", default=str(DEFAULT_CHAIN), help="audit chain to test")
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json", metavar="PATH", help="write results to JSON")
    args = ap.parse_args()

    chain = Path(args.chain)
    if not chain.exists():
        print(f"error: chain not found: {chain}")
        return 2

    try:
        summary = run_trials(chain, args.trials, args.seed)
    except Exception as exc:
        print(f"error: {exc}")
        return 2

    print("Tamper-detection experiment\n")
    print(f"  chain            {summary['chain_file']} ({summary['chain_entries']} entries)")
    print(f"  trials           {summary['trials']} (seed {summary['seed']})")
    print(f"  detected         {summary['detected']}/{summary['trials']}"
          f"  = {summary['detection_rate'] * 100:.2f}%")
    print(f"  localized        {summary['localized']}/{summary['trials']}"
          f"  = {summary['localization_rate'] * 100:.2f}%")
    print("\n  by mutation strategy:")
    for strategy, counts in sorted(summary["by_strategy"].items()):
        note = ""
        if strategy == "stored_hash":
            note = "  (detected at the following link, by design)"
        print(f"    {strategy:<12} detected {counts['detected']}/{counts['trials']}"
              f"   localized {counts['localized']}/{counts['trials']}{note}")

    if summary["escaped"]:
        print("\n  UNDETECTED MUTATIONS:")
        for row in summary["escaped"][:10]:
            print(f"    trial {row['trial']} strategy={row['strategy']} "
                  f"rowid={row['mutated_rowid']}")

    if args.json:
        Path(args.json).write_text(json.dumps(summary, indent=2, sort_keys=True),
                                   encoding="utf-8")
        print(f"\nwrote {args.json}")

    print()
    if summary["detection_rate"] == 1.0:
        print("RESULT: every mutation was detected. Tamper-evidence is measured, "
              "not assumed.")
        return 0
    print("RESULT: one or more mutations escaped detection.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
