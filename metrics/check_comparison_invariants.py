#!/usr/bin/env python3
"""
Verify the four-comparison design invariants from the KNIME result tables.

The comparison design in Chapter 2 makes a structural claim: the same three-way
comparison is run four times, holding the bank and ProofRail legs constant while
only the blockchain comparator varies. If that claim is true, the bank and
ProofRail figures must be *identical* across all four workflows, and only the
blockchain figures may differ.

This script checks that claim against the published KNIME outputs rather than
taking it on trust. It also reports the per-system figures side by side so a
reader can see all four comparisons at once.

Usage:
    python check_comparison_invariants.py
    python check_comparison_invariants.py --json out.json

Exit codes: 0 = invariants hold, 1 = a constant leg varied, 2 = inputs missing.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
KNIME_RESULTS = ROOT / "benchmark" / "results" / "knime"

# Legs that the design requires to be identical across all four comparisons.
CONSTANT_SYSTEMS = ("banking", "proofrail")
VARYING_SYSTEM = "blockchain"

# Numeric agreement tolerance for "identical".
TOLERANCE = 1e-6

COMPARISON_LABELS = {
    "01_bank_proofrail_usdc": "Bank vs. ProofRail vs. USDC stablecoin",
    "02_bank_proofrail_bitcoin": "Bank vs. ProofRail vs. Bitcoin",
    "03_bank_proofrail_ethereum": "Bank vs. ProofRail vs. Ethereum",
    "04_bank_proofrail_smartcontract": "Bank vs. ProofRail vs. smart-contract events",
}


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def as_float(value: str) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def find_column(row: Dict[str, str], *candidates: str) -> str | None:
    """KNIME writes aggregation columns like 'Mean(amount_usd)'."""
    for candidate in candidates:
        if candidate in row:
            return candidate
    return None


def collect() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """{metric: {system: {comparison: value}}}"""
    collected: Dict[str, Dict[str, Dict[str, Any]]] = {
        "mean_amount_usd": {},
        "exception_rate": {},
        "case_count": {},
    }

    for directory in sorted(KNIME_RESULTS.iterdir()):
        if not directory.is_dir():
            continue
        comparison = directory.name

        for path in directory.glob("amount_comparison*.csv"):
            for row in read_csv(path):
                system = row.get("system_type", "").strip()
                col = find_column(row, "Mean(amount_usd)")
                if system and col:
                    value = as_float(row[col])
                    if value is not None:
                        collected["mean_amount_usd"].setdefault(system, {})[comparison] = value

        for path in directory.glob("exception*.csv"):
            for row in read_csv(path):
                system = row.get("system_type", "").strip()
                col = find_column(row, "Mean(exception_int)")
                count_col = find_column(row, "Count(transaction_id)")
                if system and col:
                    value = as_float(row[col])
                    if value is not None:
                        collected["exception_rate"].setdefault(system, {})[comparison] = value
                if system and count_col:
                    value = as_float(row[count_col])
                    if value is not None:
                        collected["case_count"].setdefault(system, {})[comparison] = value

    return collected


def check(collected: Dict[str, Dict[str, Dict[str, Any]]]) -> List[str]:
    problems: List[str] = []
    expected = set(COMPARISON_LABELS)
    for comparison in sorted(expected):
        if not (KNIME_RESULTS / comparison).is_dir():
            problems.append(f"missing comparison directory: {comparison}")

    for metric, systems in collected.items():
        for system in CONSTANT_SYSTEMS:
            values = systems.get(system, {})
            if not values:
                problems.append(f"{system}.{metric}: no values found")
                continue
            missing = expected - set(values)
            if missing:
                problems.append(
                    f"{system}.{metric}: missing comparison(s): "
                    + ", ".join(sorted(missing))
                )
            spread = max(values.values()) - min(values.values())
            if spread > TOLERANCE:
                detail = ", ".join(
                    f"{comparison}={value}" for comparison, value in sorted(values.items())
                )
                problems.append(
                    f"{system}.{metric} is not constant across comparisons "
                    f"(spread {spread}): {detail}"
                )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--json", metavar="PATH", help="write results to a JSON file")
    args = ap.parse_args()

    if not KNIME_RESULTS.exists():
        print(f"error: missing KNIME results directory: {KNIME_RESULTS}")
        return 2

    collected = collect()
    if not collected["mean_amount_usd"]:
        print(f"error: no result tables found under {KNIME_RESULTS}")
        return 2

    print("Four-comparison design check\n")
    print("The design holds the bank and ProofRail legs constant and varies only")
    print("the blockchain comparator. Verifying that against the published tables.\n")

    for metric in ("mean_amount_usd", "exception_rate"):
        print(f"--- {metric} ---")
        for system in sorted(collected[metric]):
            values = collected[metric][system]
            distinct = sorted({round(v, 6) for v in values.values()})
            expected_constant = system in CONSTANT_SYSTEMS
            is_constant = len(distinct) == 1
            if expected_constant:
                verdict = "CONSTANT (as designed)" if is_constant else "VARIES — DESIGN VIOLATION"
            else:
                verdict = "varies by system (as designed)"
            print(f"  {system:<12} {verdict}")
            print(f"    across {len(values)} comparison(s): {distinct}")
        print()

    print("--- per comparison, blockchain leg ---")
    for comparison, label in COMPARISON_LABELS.items():
        amount = collected["mean_amount_usd"].get(VARYING_SYSTEM, {}).get(comparison)
        exception = collected["exception_rate"].get(VARYING_SYSTEM, {}).get(comparison)
        amount_text = f"{amount:,.2f}" if amount is not None else "n/a (non-monetary)"
        exception_text = (
            f"{exception:.4f}" if exception is not None else "n/a (no status field)"
        )
        print(f"  {label}")
        print(f"    mean amount USD  {amount_text}")
        print(f"    exception rate   {exception_text}")
    print()

    problems = check(collected)
    if args.json:
        Path(args.json).write_text(
            json.dumps({"collected": collected, "problems": problems}, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(f"wrote {args.json}")

    if problems:
        print("CHECK FAILED — the design invariants do not hold:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("CHECK PASSED — bank and ProofRail legs are identical across all")
    print("comparisons; only the blockchain comparator varies, as the design requires.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
