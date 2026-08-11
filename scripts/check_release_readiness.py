#!/usr/bin/env python3
"""Fail when known journal-release placeholders or evidence gaps remain."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    problems = []
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if "repository-code:" not in citation:
        problems.append("add the final GitHub URL as repository-code in CITATION.cff")
    if "doi:" not in citation:
        problems.append("add the version DOI to CITATION.cff after archiving the release")

    h4 = ROOT / "benchmark" / "results" / "h4_distribution_test.json"
    if not h4.exists():
        problems.append("run H4 from the two row-level exports and save its JSON result")
    else:
        try:
            result = json.loads(h4.read_text(encoding="utf-8"))
            if not {"ks_d", "p_value_asymptotic", "bank_n", "proofrail_n"} <= result.keys():
                problems.append("H4 JSON is missing required result fields")
        except (OSError, json.JSONDecodeError):
            problems.append("H4 JSON cannot be read")

    if problems:
        print("NOT READY FOR A DOI/JOURNAL RELEASE")
        for problem in problems:
            print(f"  - {problem}")
        print("The repository is still suitable as a transparent work-in-progress draft.")
        return 1

    print("RELEASE METADATA AND REQUIRED EVIDENCE ARE PRESENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
