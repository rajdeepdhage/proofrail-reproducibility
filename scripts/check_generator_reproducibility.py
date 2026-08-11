#!/usr/bin/env python3
"""Regenerate the frozen 75- and 5,000-row inputs and compare exact bytes."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERATOR = ROOT / "generator" / "settlesim_generator.py"
PROFILE = ROOT / "benchmark" / "data" / "generation_profile.json"
FROZEN = {
    75: ROOT / "benchmark" / "data" / "validation_cases.csv",
    5000: ROOT / "benchmark" / "data" / "proofrail_synthetic_n5000_seed42.csv",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    if not PROFILE.exists():
        print(f"missing generation profile: {PROFILE}")
        return 2
    seed = int(json.loads(PROFILE.read_text(encoding="utf-8"))["seed"])

    for count, frozen in FROZEN.items():
        if not frozen.exists():
            print(f"missing frozen input: {frozen}")
            return 2
        with tempfile.TemporaryDirectory(prefix=f"proofrail-n{count}-") as directory:
            command = [
                sys.executable,
                str(GENERATOR),
                "--seed",
                str(seed),
                "--n",
                str(count),
                "--out-dir",
                directory,
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                print(completed.stdout)
                print(completed.stderr)
                return completed.returncode
            regenerated = Path(directory) / "validation_cases.csv"
            expected_hash = digest(frozen)
            actual_hash = digest(regenerated)
            if expected_hash != actual_hash:
                print(
                    f"n={count}: mismatch\n"
                    f"  frozen      {expected_hash}\n"
                    f"  regenerated {actual_hash}"
                )
                return 1
            print(f"n={count}: byte-identical ({actual_hash})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
