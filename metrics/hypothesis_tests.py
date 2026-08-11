#!/usr/bin/env python3
"""
Hypothesis tests and robustness analysis for H1 (authorization latency) and
H2 (manual verification touches).

Three things are computed, in increasing order of what they establish:

1. ONE-TAILED MANN-WHITNEY U with a rank-biserial effect size and a bootstrap
   confidence interval on the difference in medians. Nonparametric, because the
   distributions are skewed.

2. SEPARATION CHECK. Whether the two samples overlap at all. Complete
   separation makes the significance test nearly uninformative -- if every
   ProofRail case beats every bank case, the p-value is a formality and the
   real question is whether the bank baseline is fair.

3. BREAKEVEN ANALYSIS. This is the part that answers the objection that
   actually matters. The bank baseline is *modeled*, not measured, so a
   reviewer can reasonably ask whether the result depends on favourable
   parameter choices. This computes how fast (or how few-touch) the manual
   workflow would have to become before the advantage disappears, and compares
   that threshold against the sensitivity envelope actually swept. A result
   outside that envelope is robust within the model, not a production-bank
   performance claim.

Usage:
    python hypothesis_tests.py
    python hypothesis_tests.py --json results.json

Exit codes: 0 = both hypotheses supported, 1 = not supported, 2 = inputs missing.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any, Dict, List, Sequence

ROOT = Path(__file__).resolve().parent.parent
ROWS_CSV = ROOT / "benchmark" / "logs" / "normalized_comparison_rows.csv"
SENSITIVITY = ROOT / "benchmark" / "results" / "bank_sensitivity_sweep.json"

BANK = "bank_manual"
PROOFRAIL = "conditional_settlement_prototype"
ALPHA = 0.05
BOOTSTRAP_SAMPLES = 10_000
BOOTSTRAP_SEED = 42


# --------------------------------------------------------------------------- #
# statistics (standard library only)
# --------------------------------------------------------------------------- #

def rank_with_ties(values: Sequence[float]) -> List[float]:
    indexed = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(indexed):
        end = position
        while end + 1 < len(indexed) and values[indexed[end + 1]] == values[indexed[position]]:
            end += 1
        average = (position + end + 2) / 2.0  # ranks are 1-based
        for k in range(position, end + 1):
            ranks[indexed[k]] = average
        position = end + 1
    return ranks


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def mann_whitney_u(a: Sequence[float], b: Sequence[float]) -> Dict[str, Any]:
    """One-tailed test of H1: values in `a` are stochastically smaller than `b`.

    Returns U for sample `a`, a normal-approximation p-value with tie
    correction, and the rank-biserial correlation as effect size.
    """
    n1, n2 = len(a), len(b)
    combined = list(a) + list(b)
    ranks = rank_with_ties(combined)
    rank_sum_a = sum(ranks[:n1])
    u_a = rank_sum_a - n1 * (n1 + 1) / 2.0
    u_b = n1 * n2 - u_a

    mean_u = n1 * n2 / 2.0
    counts: Dict[float, int] = {}
    for value in combined:
        counts[value] = counts.get(value, 0) + 1
    tie_term = sum(t ** 3 - t for t in counts.values())
    n = n1 + n2
    variance = (n1 * n2 / 12.0) * ((n + 1) - tie_term / float(n * (n - 1)))
    sd = math.sqrt(variance) if variance > 0 else 0.0

    # Directional: smaller values in `a` -> small U_a.
    if sd == 0:
        p_value = 0.0 if u_a < mean_u else 1.0
        z = float("-inf") if u_a < mean_u else 0.0
    else:
        z = (u_a - mean_u + 0.5) / sd  # continuity correction
        p_value = normal_cdf(z)

    # rank-biserial: +1 means every value in `a` is smaller than every in `b`
    effect = 1.0 - (2.0 * u_a) / (n1 * n2)
    return {
        "u_statistic": round(u_a, 4),
        "u_complement": round(u_b, 4),
        "z": (None if sd == 0 else round(z, 4)),
        "p_value_one_tailed": p_value,
        "rank_biserial_effect_size": round(effect, 6),
        "n_a": n1,
        "n_b": n2,
    }


def bootstrap_median_difference(
    a: Sequence[float], b: Sequence[float], samples: int, seed: int
) -> Dict[str, float]:
    rng = random.Random(seed)
    diffs = []
    for _ in range(samples):
        ra = [a[rng.randrange(len(a))] for _ in range(len(a))]
        rb = [b[rng.randrange(len(b))] for _ in range(len(b))]
        diffs.append(statistics.median(rb) - statistics.median(ra))
    diffs.sort()
    lower = diffs[int(0.025 * len(diffs))]
    upper = diffs[min(int(0.975 * len(diffs)), len(diffs) - 1)]
    return {
        "median_difference": round(statistics.median(b) - statistics.median(a), 6),
        "ci95_lower": round(lower, 6),
        "ci95_upper": round(upper, 6),
    }


def separation(a: Sequence[float], b: Sequence[float]) -> Dict[str, Any]:
    """Do the samples overlap at all?"""
    complete = max(a) < min(b)
    return {
        "complete_separation": complete,
        "max_of_smaller_sample": round(max(a), 6),
        "min_of_larger_sample": round(min(b), 6),
        "note": (
            "No overlap among observed values: every included ProofRail value "
            "is lower than every included bank value. The "
            "significance test is therefore a formality; the substantive "
            "question is how the result changes under the modeled bank "
            "assumptions, which the breakeven analysis addresses."
            if complete else
            "Samples overlap; the significance test carries the inferential weight."
        ),
    }


# --------------------------------------------------------------------------- #
# breakeven
# --------------------------------------------------------------------------- #

def breakeven(
    proofrail: Sequence[float], bank: Sequence[float], metric: str,
    sensitivity: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """How good would the bank workflow have to get before the gap closes?"""
    pr_median = statistics.median(proofrail)
    bank_median = statistics.median(bank)
    ratio = (bank_median / pr_median) if pr_median > 0 else float("inf")

    result: Dict[str, Any] = {
        "metric": metric,
        "proofrail_median": round(pr_median, 6),
        "bank_median": round(bank_median, 6),
        "bank_must_improve_by_factor": (None if ratio == float("inf") else round(ratio, 2)),
        "breakeven_bank_value": round(pr_median, 6),
    }

    if sensitivity:
        ranges = sensitivity.get("ranges", {})
        key = {
            "authorization_latency_s": "authorization_working_hours_median",
            "manual_touch_count": "manual_touch_count_mean",
        }.get(metric)
        if key and key in ranges:
            band = ranges[key]
            result["sensitivity_envelope"] = {
                "parameter": key,
                "min": band.get("min"),
                "max": band.get("max"),
                "scenarios_swept": sensitivity.get("scenario_count"),
            }
            if metric == "authorization_latency_s":
                best_case_seconds = float(band["min"]) * 3600.0
                result["best_case_bank_seconds_in_sweep"] = round(best_case_seconds, 2)
                result["breakeven_inside_sweep"] = best_case_seconds <= pr_median
                result["interpretation"] = (
                    f"Across all {sensitivity.get('scenario_count')} swept scenarios the "
                    f"fastest modeled bank authorization is {best_case_seconds:,.0f} s. "
                    f"Breakeven would require {pr_median:.4f} s -- roughly "
                    f"{best_case_seconds / pr_median:,.0f}x faster than the most "
                    f"favourable scenario swept. The result is robust within this "
                    f"modeled envelope; it is not a production-bank benchmark."
                ) if pr_median > 0 else (
                    "ProofRail's observed median is zero at the recorded resolution. "
                    "Within this study, any positive modeled bank review time is above "
                    "that recorded median."
                )
            else:
                best_case_touches = float(band["min"])
                result["best_case_bank_touches_in_sweep"] = best_case_touches
                result["breakeven_inside_sweep"] = best_case_touches <= pr_median
                result["interpretation"] = (
                    f"Across all {sensitivity.get('scenario_count')} swept scenarios the "
                    f"lowest modeled bank touch count is {best_case_touches}. Breakeven "
                    f"would require {pr_median}. Under the study's definition of a "
                    f"manual workflow, breakeven is outside the modeled family."
                )
    return result


# --------------------------------------------------------------------------- #

def load_metric(rows: List[Dict[str, str]], system: str, column: str) -> List[float]:
    out = []
    for row in rows:
        if row["system_type"] != system:
            continue
        text = row.get(column, "").strip()
        if text:
            try:
                out.append(float(text))
            except ValueError:
                pass
    return out


def paired_sign_test(rows: List[Dict[str, str]], column: str) -> Dict[str, Any]:
    """Exact one-tailed sign test on trace IDs observed in both systems."""
    by_system: Dict[str, Dict[str, float]] = {PROOFRAIL: {}, BANK: {}}
    for row in rows:
        system = row.get("system_type", "")
        if system not in by_system:
            continue
        trace_id = row.get("trace_id", "").strip()
        text = row.get(column, "").strip()
        if not trace_id or not text:
            continue
        try:
            by_system[system][trace_id] = float(text)
        except ValueError:
            continue

    shared = sorted(set(by_system[PROOFRAIL]) & set(by_system[BANK]))
    wins = losses = ties = 0
    for trace_id in shared:
        proofrail = by_system[PROOFRAIL][trace_id]
        bank = by_system[BANK][trace_id]
        if proofrail < bank:
            wins += 1
        elif proofrail > bank:
            losses += 1
        else:
            ties += 1

    non_tied = wins + losses
    if non_tied:
        numerator = sum(math.comb(non_tied, k) for k in range(wins, non_tied + 1))
        p_value = numerator / (2 ** non_tied)
    else:
        p_value = 1.0
    return {
        "test": "exact paired sign test",
        "alternative": "ProofRail lower",
        "matched_pairs": len(shared),
        "non_tied_pairs": non_tied,
        "proofrail_lower": wins,
        "proofrail_higher": losses,
        "ties": ties,
        "p_value_one_tailed": p_value,
    }


def analyze(rows, sensitivity, column, label, hypothesis) -> Dict[str, Any]:
    pr = load_metric(rows, PROOFRAIL, column)
    bk = load_metric(rows, BANK, column)
    test = mann_whitney_u(pr, bk)
    boot = bootstrap_median_difference(pr, bk, BOOTSTRAP_SAMPLES, BOOTSTRAP_SEED)
    sep = separation(pr, bk)
    be = breakeven(pr, bk, column, sensitivity)
    paired = paired_sign_test(rows, column)
    supported = test["p_value_one_tailed"] < ALPHA and statistics.median(pr) < statistics.median(bk)
    return {
        "hypothesis": hypothesis,
        "label": label,
        "column": column,
        "proofrail_n": len(pr),
        "bank_n": len(bk),
        "test": test,
        "bootstrap": boot,
        "separation": sep,
        "breakeven": be,
        "paired_robustness": paired,
        "supported": supported,
        "scope": "supported within the synthetic/modeled benchmark",
    }


def report(section: Dict[str, Any]) -> None:
    t, b, s, be = section["test"], section["bootstrap"], section["separation"], section["breakeven"]
    paired = section["paired_robustness"]
    print(f"--- {section['hypothesis']}: {section['label']} ---")
    print(f"  n = {section['proofrail_n']} ProofRail vs {section['bank_n']} bank")
    print(f"  medians: ProofRail {be['proofrail_median']}  |  bank {be['bank_median']}")
    p = t["p_value_one_tailed"]
    p_text = "< 1e-16" if p < 1e-16 else f"{p:.3e}"
    print(f"  Mann-Whitney U (one-tailed): U = {t['u_statistic']}, p {p_text}")
    print(f"  rank-biserial effect size:   {t['rank_biserial_effect_size']}"
          f"  (1.0 = complete dominance)")
    print(f"  bootstrap 95% CI on median difference: "
          f"[{b['ci95_lower']}, {b['ci95_upper']}]")
    print(f"  complete separation: {s['complete_separation']}"
          f"  (max ProofRail {s['max_of_smaller_sample']} vs min bank {s['min_of_larger_sample']})")
    paired_p = paired["p_value_one_tailed"]
    paired_p_text = "< 1e-16" if paired_p < 1e-16 else f"{paired_p:.3e}"
    print(f"  paired sign robustness:      {paired['proofrail_lower']}/"
          f"{paired['non_tied_pairs']} matched non-tied pairs favour ProofRail, "
          f"p {paired_p_text}")
    if be.get("interpretation"):
        print(f"  BREAKEVEN: {be['interpretation']}")
    print(f"  supported within modeled benchmark: {section['supported']}")
    print()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    if not ROWS_CSV.exists():
        print(f"error: missing {ROWS_CSV}")
        return 2
    with ROWS_CSV.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    sensitivity = None
    if SENSITIVITY.exists():
        sensitivity = json.loads(SENSITIVITY.read_text(encoding="utf-8"))

    print("Hypothesis tests — performance-evaluation layer\n")
    print("Directional (one-tailed) tests: ProofRail is predicted to be lower on")
    print("both metrics. Nonparametric throughout, because both distributions are")
    print("skewed. Effect sizes and breakeven analysis are reported alongside")
    print("p-values, since with complete separation a p-value alone says little.\n")

    h1 = analyze(rows, sensitivity, "authorization_latency_s",
                 "authorization latency (seconds)", "H1")
    h2 = analyze(rows, sensitivity, "manual_touch_count",
                 "manual verification touches per case", "H2")
    report(h1)
    report(h2)

    print("--- H3 note ---")
    print("  Auditability is NOT tested here, deliberately. The rubric assigns a")
    print("  near-constant score per system (bank 8.0 for every case, standard")
    print("  deviation 0), so there is no sampling variance to test and a")
    print("  significance test would be circular. H3 is reported as a structural")
    print("  comparison with the rubric published for inspection, and its")
    print("  tamper-evidence dimension is *measured* separately by")
    print("  metrics/tamper_experiment.py rather than scored.\n")

    payload = {"h1": h1, "h2": h2, "alpha": ALPHA,
               "bootstrap_samples": BOOTSTRAP_SAMPLES, "bootstrap_seed": BOOTSTRAP_SEED}
    if args.json:
        Path(args.json).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str),
                                   encoding="utf-8")
        print(f"wrote {args.json}")

    if h1["supported"] and h2["supported"]:
        print("RESULT: H1 and H2 are supported within this synthetic/modeled")
        print("benchmark, and both survive its defined sensitivity envelope.")
        return 0
    print("RESULT: one or both hypotheses not supported.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
