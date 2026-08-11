"""
Bank-internal synthetic validation-data generator.

Purpose
-------
Generate synthetic data that looks like a bank's internal payment/case records
while still validating the conditional-settlement prototype.

This generator intentionally does NOT:

- read or copy external settlement-rail rows
- emit network/transaction-hash fields
- emit source_family/provenance labels
- treat outside reference datasets as source populations

It creates one population of conditional payments, writes it in a bank-internal
shape, and writes `validation_cases.csv` for `proofrail_app.py replay`.

Outputs
-------
validation_cases.csv
    The replay contract for the prototype. Extra bank-like columns are included,
    but the required fields are transaction_id, amount_usd, transaction_type,
    required_events, scenario, created_offset_s, payer_id, and payee_id.

bank_internal_ledger.csv
    Synthetic bank operations records: case creation, KYC, payment instruction,
    condition checks, review/exception/dispute, and ledger posting.

bank_customer_journey.csv
    Synthetic channel journey events for the customer/case.

bank_validation_event_log.csv
    Step-level bank validation log in a comparison-friendly schema. It is not
    an outside settlement rail; it is a bank-internal operational view of the same cases.

generation_profile.json
    Design notes, population summary, output paths, and next commands.

Optional:
    --run-replay runs the prototype against validation_cases.csv.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


T0 = datetime(2026, 1, 5, 9, 0, 0)
DEFAULT_CURRENCY = "USD"
GENERATOR_VERSION = "proofrail_bank_internal_v2"
SCOPE_NOTICE = "Demonstration study — synthetic/modeled data, not measured production data."
CONFORMANCE_NOTE = (
    "Conformance test: expected_outcome and the prototype both derive from the scenario field, "
    "so this confirms the implementation matches the specification — it does not establish "
    "that the specification is the correct design."
)
SENSITIVITY_PARAMETER_RANGES = {
    "staff_scale": [0.75, 1.0, 1.5],
    "manual_review_rate": [0.06, 0.12, 0.24],
    "condition_wait_scale": [0.5, 1.0, 2.0],
}

REQUIRED_EVENTS: Dict[str, List[str]] = {
    "INVOICE_PAYMENT": ["INVOICE_APPROVED", "DELIVERY_CONFIRMED"],
    "GOODS_SETTLEMENT": ["DELIVERY_CONFIRMED", "INSPECTION_PASSED"],
    "MILESTONE_PAYMENT": ["MILESTONE_REACHED", "INSPECTION_PASSED"],
    "SERVICE_RETAINER": ["SERVICE_COMPLETED", "INVOICE_APPROVED"],
}

TRANSACTION_TYPE_WEIGHTS = {
    "INVOICE_PAYMENT": 0.42,
    "GOODS_SETTLEMENT": 0.26,
    "MILESTONE_PAYMENT": 0.22,
    "SERVICE_RETAINER": 0.10,
}

SCENARIO_WEIGHTS = {
    "normal": 0.72,
    "delayed": 0.16,
    "disputed": 0.08,
    "exception": 0.04,
}

EXPECTED_OUTCOME_BY_SCENARIO = {
    "normal": "RELEASED",
    "delayed": "RELEASED",
    "disputed": "DISPUTED",
    "exception": "HELD",
}

CHANNEL_WEIGHTS = {
    "treasury_portal": 0.42,
    "relationship_manager": 0.22,
    "api_instruction": 0.20,
    "branch_ops": 0.10,
    "secure_email": 0.06,
}

PRODUCT_WEIGHTS = {
    "commercial_settlement": 0.38,
    "invoice_settlement": 0.26,
    "goods_trade_settlement": 0.22,
    "service_retainage": 0.14,
}

COUNTRY_WEIGHTS = {
    "USA": 0.82,
    "CANADA": 0.08,
    "UNITED-KINGDOM": 0.03,
    "MEXICO": 0.03,
    "GERMANY": 0.02,
    "SINGAPORE": 0.02,
}

SECTOR_WEIGHTS = {
    "manufacturing": 0.24,
    "professional_services": 0.22,
    "logistics": 0.18,
    "software": 0.16,
    "construction": 0.12,
    "wholesale": 0.08,
}

LOB_WEIGHTS = {
    "commercial_banking": 0.54,
    "transaction_banking": 0.28,
    "trade_finance": 0.18,
}

AMOUNT_LOG_MU = math.log(2_500.0)
AMOUNT_LOG_SIGMA = 1.10
MEAN_INTERARRIVAL_S = 90


def weighted_choice(rng: random.Random, weights: Dict[str, float]) -> str:
    total = sum(max(0.0, value) for value in weights.values())
    if total <= 0:
        return next(iter(weights))
    point = rng.random() * total
    running = 0.0
    for key, weight in weights.items():
        running += max(0.0, weight)
        if point <= running:
            return key
    return next(reversed(weights))


def stable_hash(text: str, length: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def timestamp(offset_s: int) -> str:
    return (T0 + timedelta(seconds=offset_s)).isoformat(timespec="seconds")


def timestamp_epoch_s(offset_s: int) -> int:
    return int((T0 + timedelta(seconds=offset_s)).timestamp())


def bank_account(customer_id: str) -> str:
    return f"ACCT-{stable_hash(customer_id, 10).upper()}"


def draw_amount(rng: random.Random, floor: float, cap: float) -> float:
    amount = math.exp(rng.normalvariate(AMOUNT_LOG_MU, AMOUNT_LOG_SIGMA))
    return round(max(floor, min(cap, amount)), 2)


def risk_score_for(scenario: str, amount: float, rng: random.Random) -> int:
    if scenario == "exception":
        base = rng.randint(76, 94)
    elif scenario == "disputed":
        base = rng.randint(68, 90)
    elif scenario == "delayed":
        base = rng.randint(42, 70)
    else:
        base = rng.randint(12, 48)
    if amount >= 50_000:
        base += 8
    elif amount >= 15_000:
        base += 4
    return max(1, min(99, base))


def risk_band(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def bank_label(scenario: str, score: int) -> str:
    if scenario in {"disputed", "exception"} or score >= 75:
        return "BAD"
    if scenario == "delayed" or score >= 45:
        return "REVIEW"
    return "GOOD"


def rail_for(amount: float, rng: random.Random) -> str:
    if amount >= 25_000:
        return weighted_choice(rng, {"WIRE": 0.72, "BOOK-TRANSFER": 0.18, "ACH": 0.10})
    if amount >= 5_000:
        return weighted_choice(rng, {"ACH": 0.44, "WIRE": 0.34, "BOOK-TRANSFER": 0.22})
    return weighted_choice(rng, {"ACH": 0.52, "BOOK-TRANSFER": 0.30, "CARD-SETTLEMENT": 0.18})


def manual_review_expected(scenario: str, score: int, amount: float) -> bool:
    return scenario != "normal" or score >= 70 or amount >= 25_000


def generate_cases(n: int, seed: int, floor: float, cap: float) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    rows: List[Dict[str, Any]] = []
    offset = 0
    for idx in range(1, n + 1):
        transaction_type = weighted_choice(rng, TRANSACTION_TYPE_WEIGHTS)
        scenario = weighted_choice(rng, SCENARIO_WEIGHTS)
        amount = draw_amount(rng, floor, cap)
        score = risk_score_for(scenario, amount, rng)
        band = risk_band(score)
        offset += max(1, int(rng.expovariate(1.0 / MEAN_INTERARRIVAL_S)))

        payer_id = f"cust_payer_{rng.randint(1, 99999):05d}"
        payee_id = f"cust_payee_{rng.randint(1, 99999):05d}"
        trace_id = f"txn_{idx:07d}"
        channel = weighted_choice(rng, CHANNEL_WEIGHTS)
        product = weighted_choice(rng, PRODUCT_WEIGHTS)

        rows.append({
            "transaction_id": trace_id,
            "payer_id": payer_id,
            "payee_id": payee_id,
            "amount_usd": amount,
            "transaction_type": transaction_type,
            "required_events": "|".join(REQUIRED_EVENTS[transaction_type]),
            "scenario": scenario,
            "expected_outcome": EXPECTED_OUTCOME_BY_SCENARIO[scenario],
            "created_offset_s": offset,
            "currency": DEFAULT_CURRENCY,
            "internal_case_id": f"CASE-{stable_hash(trace_id, 8).upper()}",
            "payment_instruction_id": f"PMT-{stable_hash(trace_id + ':pmt', 10).upper()}",
            "bank_channel": channel,
            "bank_product": product,
            "sender_country": weighted_choice(rng, COUNTRY_WEIGHTS),
            "bene_country": weighted_choice(rng, COUNTRY_WEIGHTS),
            "sender_sector": weighted_choice(rng, SECTOR_WEIGHTS),
            "sender_lob": weighted_choice(rng, LOB_WEIGHTS),
            "risk_score": score,
            "risk_band": band,
            "bank_label": bank_label(scenario, score),
            "manual_review_expected": manual_review_expected(scenario, score, amount),
        })
    return rows


def bank_row(
    case: Dict[str, Any],
    offset_s: int,
    amount: float,
    transaction_type: str,
    stage: str,
    *,
    condition_type: str = "",
    manual_review: bool = False,
    exception: bool = False,
) -> Dict[str, Any]:
    label = case["bank_label"]
    return {
        "Time_step": timestamp(offset_s).replace("T", " "),
        "Label": label,
        "Transaction_Id": f"{transaction_type}-{case['transaction_id']}",
        "Sender_Id": case["payer_id"],
        "Sender_Account": bank_account(case["payer_id"]),
        "Sender_Institution": "SYNTHBANK",
        "Sender_Country": case["sender_country"],
        "Sender_Sector": case["sender_sector"],
        "Sender_lob": case["sender_lob"],
        "Bene_Id": case["payee_id"],
        "Bene_Account": bank_account(case["payee_id"]),
        "Bene_Institution": "SYNTHBANK",
        "Bene_Country": case["bene_country"],
        "USD_amount": round(amount, 2),
        "Transaction_Type": transaction_type,
        "trace_id": case["transaction_id"],
        "internal_case_id": case["internal_case_id"],
        "validation_stage": stage,
        "condition_type": condition_type,
        "bank_channel": case["bank_channel"],
        "bank_product": case["bank_product"],
        "risk_score": case["risk_score"],
        "risk_band": case["risk_band"],
        "manual_review_flag": manual_review,
        "exception_flag": exception,
        "scenario": case["scenario"],
    }


def generate_bank_internal_ledger(cases: List[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    rng = random.Random(seed + 101)
    rows: List[Dict[str, Any]] = []
    for case in cases:
        base = int(case["created_offset_s"])
        amount = float(case["amount_usd"])
        rail = rail_for(amount, rng)
        rows.append(bank_row(case, base, 0.0, "CASE-OPENED", "case_opened"))
        rows.append(bank_row(case, base + 30, 0.0, "KYC-SCREENING", "kyc_screening"))
        rows.append(bank_row(case, base + 60, amount, rail, "payment_instruction"))

        if case["manual_review_expected"]:
            rows.append(bank_row(
                case,
                base + 300,
                amount,
                "MANUAL-REVIEW",
                "manual_review",
                manual_review=True,
            ))

        if case["scenario"] == "disputed":
            rows.append(bank_row(
                case,
                base + 900,
                amount,
                "DISPUTE-RAISED",
                "dispute",
                manual_review=True,
                exception=True,
            ))
            continue

        if case["scenario"] == "exception":
            rows.append(bank_row(
                case,
                base + 1800,
                amount,
                "CONDITION-EXCEPTION",
                "exception_hold",
                manual_review=True,
                exception=True,
            ))
            continue

        condition_base = base + (900 if case["scenario"] == "delayed" else 180)
        for i, condition in enumerate(str(case["required_events"]).split("|"), start=1):
            rows.append(bank_row(
                case,
                condition_base + i * 120,
                amount,
                "CONDITION-VERIFIED",
                "condition_verified",
                condition_type=condition,
            ))

        rows.append(bank_row(case, condition_base + 420, amount, "LEDGER-POSTED", "ledger_settled"))
    return rows


def generate_customer_journey(cases: List[Dict[str, Any]], seed: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for case in cases:
        base = int(case["created_offset_s"])
        channel = case["bank_channel"]
        events = [
            (0, f"{channel}:login", "case_start"),
            (45, f"{channel}:payment_instruction_created", "instruction"),
            (120, f"{channel}:supporting_document_uploaded", "documentation"),
        ]
        if case["scenario"] == "disputed":
            events.extend([
                (600, "operations:dispute_notice_received", "dispute"),
                (900, "operations:case_paused_for_review", "dispute"),
            ])
        elif case["scenario"] == "exception":
            events.extend([
                (600, "operations:condition_exception_detected", "exception"),
                (1200, "operations:customer_follow_up_required", "exception"),
            ])
        else:
            events.append((600 if case["scenario"] == "delayed" else 240, f"{channel}:settlement_confirmation_viewed", "settlement"))
        events.append((1500 if case["scenario"] in {"disputed", "exception"} else 480, f"{channel}:logout", "close"))

        for offset_delta, event, stage in events:
            rows.append({
                "Time step": timestamp(base + offset_delta).replace("T", " "),
                "Label": "STANDARD-NO-FAILURE-MIXED" if case["scenario"] == "normal" else "STANDARD-EXCEPTION-MIXED",
                "Event": event,
                "Customer id": case["payer_id"],
                "trace_id": case["transaction_id"],
                "internal_case_id": case["internal_case_id"],
                "bank_channel": channel,
                "case_stage": stage,
                "scenario": case["scenario"],
            })
    return rows


def bank_validation_step(
    case: Dict[str, Any],
    offset_s: int,
    step_name: str,
    category: str,
    *,
    verification: bool,
    manual_review: bool,
    exception: bool,
    outcome: str,
) -> Dict[str, Any]:
    amount = round(float(case["amount_usd"]), 2)
    return {
        "architecture": "bank",
        "system_type": "synthetic_bank_internal",
        "trace_id": case["transaction_id"],
        "step_name": step_name,
        "step_category": category,
        "timestamp": timestamp(offset_s),
        "timestamp_epoch_s": timestamp_epoch_s(offset_s),
        "amount_usd": amount,
        "verification_required": verification,
        "manual_review_flag": manual_review,
        "exception_flag": exception,
        "risk_score": case["risk_score"],
        "risk_band": case["risk_band"],
        "final_outcome": outcome,
    }


def generate_bank_validation_event_log(cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for case in cases:
        base = int(case["created_offset_s"])
        scenario = case["scenario"]
        outcome = "pending"
        rows.append(bank_validation_step(case, base, "CASE_OPENED", "init", verification=False, manual_review=False, exception=False, outcome=outcome))
        rows.append(bank_validation_step(case, base + 30, "KYC_SCREENED", "verification", verification=True, manual_review=False, exception=False, outcome=outcome))
        rows.append(bank_validation_step(case, base + 60, "PAYMENT_INSTRUCTION_ACCEPTED", "instruction", verification=True, manual_review=False, exception=False, outcome=outcome))
        if case["manual_review_expected"]:
            rows.append(bank_validation_step(case, base + 300, "MANUAL_REVIEW", "verification", verification=True, manual_review=True, exception=False, outcome=outcome))
        if scenario == "disputed":
            rows.append(bank_validation_step(case, base + 900, "DISPUTE_RAISED", "exception", verification=True, manual_review=True, exception=True, outcome="disputed"))
            continue
        if scenario == "exception":
            rows.append(bank_validation_step(case, base + 1800, "CONDITION_EXCEPTION", "exception", verification=True, manual_review=True, exception=True, outcome="unresolved"))
            continue
        condition_base = base + (900 if scenario == "delayed" else 180)
        for i, condition in enumerate(str(case["required_events"]).split("|"), start=1):
            rows.append(bank_validation_step(case, condition_base + i * 120, f"CONDITION_VERIFIED:{condition}", "attestation", verification=True, manual_review=False, exception=False, outcome=outcome))
        rows.append(bank_validation_step(case, condition_base + 420, "LEDGER_POSTED", "settlement", verification=False, manual_review=False, exception=False, outcome="completed"))
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def public_path(path: Path, base: Optional[Path] = None) -> str:
    base = (base or Path.cwd()).resolve()
    try:
        return path.resolve().relative_to(base).as_posix()
    except (OSError, ValueError):
        return path.name if path.is_absolute() else path.as_posix()


def public_text(text: str) -> str:
    base = Path.cwd().resolve().as_posix()
    return str(text or "").replace(base + "/", "")


def summarize_cases(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    amounts = [float(row["amount_usd"]) for row in cases]
    return {
        "cases": len(cases),
        "scenarios": dict(Counter(row["scenario"] for row in cases)),
        "transaction_types": dict(Counter(row["transaction_type"] for row in cases)),
        "risk_bands": dict(Counter(row["risk_band"] for row in cases)),
        "channels": dict(Counter(row["bank_channel"] for row in cases)),
        "amount_usd_min": min(amounts) if amounts else None,
        "amount_usd_max": max(amounts) if amounts else None,
        "amount_usd_mean": round(sum(amounts) / len(amounts), 2) if amounts else None,
    }


def run_replay(proofrail_app: Path, db_path: Path, cases_csv: Path, summary_csv: Path, steps_csv: Path) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(proofrail_app),
        "--db",
        str(db_path),
        "replay",
        "--input",
        str(cases_csv),
        "--metrics-csv",
        str(summary_csv),
        "--steps-csv",
        str(steps_csv),
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    display_cmd = [
        "python3",
        public_path(proofrail_app),
        "--db",
        public_path(db_path),
        "replay",
        "--input",
        public_path(cases_csv),
        "--metrics-csv",
        public_path(summary_csv),
        "--steps-csv",
        public_path(steps_csv),
    ]
    return {
        "command": display_cmd,
        "returncode": completed.returncode,
        "stdout": public_text(completed.stdout),
        "stderr": public_text(completed.stderr),
    }


def replay_oracle_report(cases: List[Dict[str, Any]], summary_csv: Path) -> Dict[str, Any]:
    if not summary_csv.exists():
        return {"ok": False, "reason": "prototype_summary_missing"}
    actual_by_trace: Dict[str, str] = {}
    with summary_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            trace_id = str(row.get("trace_id") or "").strip()
            status = str(row.get("status") or "").strip().upper()
            if trace_id:
                actual_by_trace[trace_id] = status
    matrix: Dict[str, Dict[str, int]] = {}
    mismatches: List[Dict[str, str]] = []
    passed = 0
    for case in cases:
        trace_id = str(case["transaction_id"])
        expected = str(case["expected_outcome"]).upper()
        actual = actual_by_trace.get(trace_id, "MISSING")
        matrix.setdefault(expected, {})
        matrix[expected][actual] = matrix[expected].get(actual, 0) + 1
        if expected == actual:
            passed += 1
        elif len(mismatches) < 25:
            mismatches.append({
                "trace_id": trace_id,
                "scenario": str(case["scenario"]),
                "expected_outcome": expected,
                "actual_outcome": actual,
            })
    total = len(cases)
    return {
        "ok": passed == total,
        "cases": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 4) if total else None,
        "confusion_matrix": matrix,
        "sample_mismatches": mismatches,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate bank-internal synthetic validation data")
    parser.add_argument("--n", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="outputs/bank_internal_validation")
    parser.add_argument("--amount-floor", type=float, default=25.0)
    parser.add_argument("--amount-cap", type=float, default=150_000.0)
    parser.add_argument("--run-replay", action="store_true")
    parser.add_argument("--proofrail-app", default="proofrail_app.py")
    parser.add_argument("--db", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = generate_cases(args.n, args.seed, args.amount_floor, args.amount_cap)
    ledger_rows = generate_bank_internal_ledger(cases, args.seed)
    journey_rows = generate_customer_journey(cases, args.seed)
    validation_log_rows = generate_bank_validation_event_log(cases)

    paths = {
        "validation_cases": out_dir / "validation_cases.csv",
        "bank_internal_ledger": out_dir / "bank_internal_ledger.csv",
        "bank_customer_journey": out_dir / "bank_customer_journey.csv",
        "bank_validation_event_log": out_dir / "bank_validation_event_log.csv",
        "profile": out_dir / "generation_profile.json",
    }

    write_csv(paths["validation_cases"], cases)
    write_csv(paths["bank_internal_ledger"], ledger_rows)
    write_csv(paths["bank_customer_journey"], journey_rows)
    write_csv(paths["bank_validation_event_log"], validation_log_rows)

    report: Dict[str, Any] = {
        "generator_kind": "bank_internal_validation_synthetic",
        "generator_version": GENERATOR_VERSION,
        "design": (
            "Synthetic bank-internal validation data only. No external settlement-rail rows, "
            "no provenance labels, and no raw external row copying."
        ),
        "seed": args.seed,
        "summary": summarize_cases(cases),
        "provenance": {
            "synthetic": True,
            "seed": args.seed,
            "generator_kind": "bank_internal_validation_synthetic",
            "generator_version": GENERATOR_VERSION,
            "scope_notice": SCOPE_NOTICE,
            "swept_parameter_ranges": SENSITIVITY_PARAMETER_RANGES,
        },
        "outputs": {key: public_path(value) for key, value in paths.items()},
        "validation_contract": {
            "prototype_replay_input": "validation_cases.csv",
            "required_fields": [
                "transaction_id",
                "payer_id",
                "payee_id",
                "amount_usd",
                "transaction_type",
                "required_events",
                "scenario",
                "expected_outcome",
                "created_offset_s",
            ],
            "extra_fields_are_bank_internal_context": True,
        },
        "next_steps": {
            "prototype_replay": [
                "python3",
                public_path(Path(args.proofrail_app)),
                "--db",
                public_path(out_dir / "prototype_validation.db"),
                "replay",
                "--input",
                public_path(paths["validation_cases"]),
                "--metrics-csv",
                public_path(out_dir / "prototype_summary.csv"),
                "--steps-csv",
                public_path(out_dir / "prototype_step_log.csv"),
            ],
            "manual_bank_sim": [
                "PYTHONPATH=work/vendor",
                "python3",
                "simulate_manual_bank.py",
                "--input",
                public_path(paths["validation_cases"]),
                "--steps-csv",
                public_path(out_dir / "bank_manual_step_log.csv"),
                "--summary-csv",
                public_path(out_dir / "bank_manual_summary.csv"),
                "--seed",
                str(args.seed),
                "--sensitivity-sweep",
                "--sensitivity-json",
                public_path(out_dir / "bank_sensitivity_sweep.json"),
            ],
        },
    }

    if args.run_replay:
        db_path = Path(args.db) if args.db else out_dir / "prototype_validation.db"
        if not args.db and db_path.exists():
            db_path.unlink()
        replay_summary = out_dir / "prototype_summary.csv"
        replay_steps = out_dir / "prototype_step_log.csv"
        report["prototype_replay"] = run_replay(
            Path(args.proofrail_app),
            db_path,
            paths["validation_cases"],
            replay_summary,
            replay_steps,
        )
        report["outputs"]["prototype_summary"] = public_path(replay_summary)
        report["outputs"]["prototype_step_log"] = public_path(replay_steps)
        conformance = replay_oracle_report(cases, replay_summary)
        conformance["note"] = CONFORMANCE_NOTE
        report["conformance_test"] = conformance

    paths["profile"].write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "generator_kind": report["generator_kind"],
        "cases": len(cases),
        "bank_internal_ledger_rows": len(ledger_rows),
        "bank_customer_journey_rows": len(journey_rows),
        "bank_validation_event_log_rows": len(validation_log_rows),
        "out_dir": str(out_dir),
        "prototype_replay": report.get("prototype_replay", {}).get("returncode", "skipped"),
    }, indent=2))
    return 0 if report.get("prototype_replay", {}).get("returncode", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
