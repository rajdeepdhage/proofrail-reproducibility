#!/usr/bin/env python3
"""Run the planned H4 two-sample KS comparison on row-level amounts.

The comparison uses log1p(amount_usd), which retains zero-valued records while
reducing the influence of the long right tail. The reported p-value uses the
standard asymptotic two-sided approximation. With rounded or repeated amounts,
that p-value is approximate; the KS statistic D should always be reported too.

Failure to reject the KS null is not proof that two distributions are
equivalent. H4 should be interpreted as a calibration check and accompanied by
the sampling design, sample sizes, D, and the limitations stated in the output.

Usage:
    python3 metrics/h4_distribution_test.py \
        --bank benchmark/row_level/bank_random_n5000_seed42.csv \
        --proofrail benchmark/row_level/proofrail_random_n5000_seed42.csv \
        --json benchmark/results/h4_distribution_test.json

Exit codes: 0 = computed, 2 = input/schema problem.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BANK = ROOT / "benchmark" / "row_level" / "bank_random_n5000_seed42.csv"
DEFAULT_PROOFRAIL = (
    ROOT / "benchmark" / "row_level" / "proofrail_random_n5000_seed42.csv"
)


def read_amounts(path: Path, column: str) -> Tuple[List[float], Dict[str, int]]:
    if not path.exists():
        raise ValueError(f"missing input: {path}")

    values: List[float] = []
    counts = {"rows": 0, "missing": 0, "invalid": 0, "negative": 0}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or column not in reader.fieldnames:
            fields = ", ".join(reader.fieldnames or [])
            raise ValueError(
                f"{path}: required column {column!r} not found; columns: {fields}"
            )
        for row in reader:
            counts["rows"] += 1
            text = str(row.get(column, "")).strip().replace(",", "")
            if not text:
                counts["missing"] += 1
                continue
            try:
                value = float(text)
            except ValueError:
                counts["invalid"] += 1
                continue
            if value < 0:
                counts["negative"] += 1
                continue
            values.append(math.log1p(value))

    if not values:
        raise ValueError(f"{path}: no usable nonnegative values in {column!r}")
    return values, counts


def ks_statistic(a: Sequence[float], b: Sequence[float]) -> float:
    """Return the two-sample Kolmogorov-Smirnov D statistic."""
    left = sorted(a)
    right = sorted(b)
    i = j = 0
    d = 0.0
    while i < len(left) or j < len(right):
        if j >= len(right) or (i < len(left) and left[i] <= right[j]):
            value = left[i]
        else:
            value = right[j]
        while i < len(left) and left[i] <= value:
            i += 1
        while j < len(right) and right[j] <= value:
            j += 1
        d = max(d, abs(i / len(left) - j / len(right)))
    return d


def asymptotic_two_sided_p(d: float, n1: int, n2: int) -> float:
    """Approximate the two-sided p-value from the Kolmogorov distribution."""
    if d <= 0:
        return 1.0
    effective_n = math.sqrt((n1 * n2) / (n1 + n2))
    scaled = (effective_n + 0.12 + 0.11 / effective_n) * d
    total = 0.0
    for k in range(1, 201):
        term = 2.0 * ((-1.0) ** (k - 1)) * math.exp(-2.0 * k * k * scaled * scaled)
        total += term
        if abs(term) < 1e-14:
            break
    return min(1.0, max(0.0, total))


def analyze(bank: Sequence[float], proofrail: Sequence[float]) -> Dict[str, Any]:
    d = ks_statistic(bank, proofrail)
    p_value = asymptotic_two_sided_p(d, len(bank), len(proofrail))
    return {
        "test": "two-sample Kolmogorov-Smirnov",
        "alternative": "two-sided",
        "transform": "natural log1p(amount_usd)",
        "bank_n": len(bank),
        "proofrail_n": len(proofrail),
        "ks_d": round(d, 8),
        "p_value_asymptotic": p_value,
        "interpretation_guardrail": (
            "A large p-value is failure to detect a difference, not evidence of "
            "equivalence. Report D, sample sizes, the fixed-seed sampling design, "
            "and that calibration is partly by construction."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--proofrail", type=Path, default=DEFAULT_PROOFRAIL)
    parser.add_argument("--column", default="amount_usd")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    try:
        bank, bank_counts = read_amounts(args.bank, args.column)
        proofrail, proofrail_counts = read_amounts(args.proofrail, args.column)
    except ValueError as exc:
        print(f"H4 NOT RUN: {exc}")
        return 2

    result = analyze(bank, proofrail)
    result["inputs"] = {
        "bank": str(args.bank),
        "proofrail": str(args.proofrail),
        "column": args.column,
        "bank_row_accounting": bank_counts,
        "proofrail_row_accounting": proofrail_counts,
    }

    print("H4 distributional calibration check")
    print(f"  transform:     {result['transform']}")
    print(f"  observations:  bank {result['bank_n']} | ProofRail {result['proofrail_n']}")
    print(f"  KS D:          {result['ks_d']}")
    print(f"  p (two-sided): {result['p_value_asymptotic']:.6g}  [asymptotic]")
    print(f"  caution:       {result['interpretation_guardrail']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
