#!/usr/bin/env python3
"""
Recompute the reported benchmark metrics from the published step-level logs.

This script exists so that a reviewer does not have to trust the summary
tables. It reads the per-transaction traces in ../benchmark/logs/, recomputes
the three headline metrics from scratch, and (optionally) diffs the results
against the published summary in ../benchmark/results/. Any discrepancy is
reported as a failure.

Metrics recomputed (definitions match Chapter 2 of the thesis):

  Authorization latency  seconds from the final required piece of evidence to
                         the settlement decision, payment rail held constant.
                         Reported as mean, median (p50), and p90.

  Verification burden    count of manual review touches per case before
                         completion (mean).

  Auditability           derived rubric: tamper-evidence + completeness +
                         independent verifiability + non-repudiation,
                         reported as the rollup mean.

Usage:
    python compute_metrics.py                 # recompute and print
    python compute_metrics.py --check         # also diff vs published summary
    python compute_metrics.py --json out.json # write machine-readable results
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
ROWS_CSV = ROOT / "benchmark" / "logs" / "normalized_comparison_rows.csv"
SUMMARY_CSV = ROOT / "benchmark" / "results" / "comparison_summary_by_system.csv"

# Numeric agreement tolerance when checking against the published summary.
TOLERANCE = 0.01

RUBRIC_PARTS = (
    "tamper_evidence",
    "completeness",
    "independent_verifiability",
    "non_repudiation",
)


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def as_float(value: str) -> float | None:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def percentile(values: List[float], q: float) -> float:
    """Nearest-rank percentile, matching the reporting convention used."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 4)
    position = q * (len(ordered) - 1)
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    weight = position - low
    return round(ordered[low] * (1 - weight) + ordered[high] * weight, 4)


def summarize(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    by_system: Dict[str, List[Dict[str, str]]] = {}
    for row in rows:
        by_system.setdefault(row["system_type"], []).append(row)

    out: Dict[str, Dict[str, Any]] = {}
    for system, group in sorted(by_system.items()):
        latency = [v for v in (as_float(r["authorization_latency_s"]) for r in group)
                   if v is not None]
        touches = [v for v in (as_float(r["manual_touch_count"]) for r in group)
                   if v is not None]
        auto = [v for v in (as_float(r["automated_check_count"]) for r in group)
                if v is not None]
        rollup = [v for v in (as_float(r["auditability_rollup"]) for r in group)
                  if v is not None]

        # Recompute the rubric rollup from its four components as a
        # cross-check that the published rollup is internally consistent.
        recomputed_rollup: List[float] = []
        for r in group:
            parts = [as_float(r[p]) for p in RUBRIC_PARTS]
            if all(p is not None for p in parts):
                recomputed_rollup.append(sum(parts))  # type: ignore[arg-type]

        statuses: Dict[str, int] = {}
        for r in group:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1

        out[system] = {
            "architecture": group[0]["architecture"],
            "n_cases": len(group),
            "status_counts": statuses,
            "authorization_latency_s": {
                "n": len(latency),
                "mean": round(statistics.fmean(latency), 4) if latency else 0.0,
                "p50": percentile(latency, 0.50),
                "p90": percentile(latency, 0.90),
            },
            "manual_touch_count_n": len(touches),
            "manual_touch_count_mean": (
                round(statistics.fmean(touches), 4) if touches else 0.0
            ),
            "automated_check_count_mean": (
                round(statistics.fmean(auto), 4) if auto else 0.0
            ),
            "auditability_rollup_mean": (
                round(statistics.fmean(rollup), 4) if rollup else 0.0
            ),
            "auditability_rollup_mean_recomputed_from_parts": (
                round(statistics.fmean(recomputed_rollup), 4)
                if recomputed_rollup else 0.0
            ),
            "irreversible_dispute_cases": sum(
                1 for r in group
                if str(r.get("irreversible_dispute", "")).strip().lower()
                in {"true", "1", "yes"}
            ),
        }
    return out


def check_against_published(computed: Dict[str, Dict[str, Any]]) -> List[str]:
    """Diff recomputed values against the published summary table."""
    if not SUMMARY_CSV.exists():
        return [f"published summary not found: {SUMMARY_CSV}"]

    problems: List[str] = []
    published = {r["system_type"]: r for r in read_rows(SUMMARY_CSV)}

    for system, values in computed.items():
        if system not in published:
            problems.append(f"{system}: absent from published summary")
            continue
        row = published[system]
        comparisons = [
            ("authorization_latency_s_mean",
             values["authorization_latency_s"]["mean"]),
            ("authorization_latency_s_p50",
             values["authorization_latency_s"]["p50"]),
            ("authorization_latency_s_p90",
             values["authorization_latency_s"]["p90"]),
            ("manual_touch_count_mean", values["manual_touch_count_mean"]),
            ("automated_check_count_mean", values["automated_check_count_mean"]),
            ("auditability_rollup_mean", values["auditability_rollup_mean"]),
        ]
        for column, mine in comparisons:
            theirs = as_float(row.get(column, ""))
            if theirs is None:
                problems.append(f"{system}.{column}: missing in published summary")
            elif abs(theirs - mine) > TOLERANCE:
                problems.append(
                    f"{system}.{column}: recomputed {mine} vs published {theirs}"
                )

        n_published = as_float(row.get("n_cases", ""))
        if n_published is not None and int(n_published) != values["n_cases"]:
            problems.append(
                f"{system}.n_cases: recomputed {values['n_cases']} "
                f"vs published {int(n_published)}"
            )

        # Internal consistency: rollup should equal the sum of its four parts.
        drift = abs(values["auditability_rollup_mean"]
                    - values["auditability_rollup_mean_recomputed_from_parts"])
        if drift > TOLERANCE:
            problems.append(
                f"{system}.auditability_rollup: stored rollup disagrees with "
                f"the sum of its four components by {round(drift, 4)}"
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="diff recomputed metrics against the published summary")
    ap.add_argument("--json", metavar="PATH",
                    help="write recomputed metrics to a JSON file")
    args = ap.parse_args()

    if not ROWS_CSV.exists():
        print(f"error: missing input log: {ROWS_CSV}")
        return 2

    rows = read_rows(ROWS_CSV)
    computed = summarize(rows)

    print(f"Recomputed from {ROWS_CSV.relative_to(ROOT)}  "
          f"({len(rows)} case rows)\n")
    for system, values in computed.items():
        lat = values["authorization_latency_s"]
        print(f"  {system}  [{values['architecture']}]  n={values['n_cases']}")
        print(f"    authorization latency (s)   n {lat['n']}  mean {lat['mean']}  "
              f"p50 {lat['p50']}  p90 {lat['p90']}")
        print(f"    manual touches / case       n {values['manual_touch_count_n']}  "
              f"mean {values['manual_touch_count_mean']}")
        print(f"    automated checks / case     {values['automated_check_count_mean']}")
        print(f"    auditability rollup         {values['auditability_rollup_mean']}")
        print(f"    irreversible disputes       {values['irreversible_dispute_cases']}")
        print(f"    status counts               {values['status_counts']}")
        print()

    if args.json:
        Path(args.json).write_text(
            json.dumps(computed, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(f"wrote {args.json}")

    if args.check:
        problems = check_against_published(computed)
        if problems:
            print("CHECK FAILED — recomputed metrics disagree with published summary:")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print("CHECK PASSED — recomputed metrics match the published summary "
              f"within +/-{TOLERANCE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
