from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "hypothesis_tests", ROOT / "metrics" / "hypothesis_tests.py"
)
assert SPEC and SPEC.loader
STATS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STATS)


class HypothesisStatisticsTest(unittest.TestCase):
    def test_mann_whitney_complete_separation(self) -> None:
        result = STATS.mann_whitney_u([1.0, 2.0, 3.0], [10.0, 11.0, 12.0])
        self.assertEqual(result["u_statistic"], 0.0)
        self.assertEqual(result["rank_biserial_effect_size"], 1.0)
        self.assertLess(result["p_value_one_tailed"], 0.05)

    def test_paired_sign_test_matches_trace_ids(self) -> None:
        rows = []
        for index in range(3):
            trace = f"t{index}"
            rows.append(
                {
                    "trace_id": trace,
                    "system_type": STATS.PROOFRAIL,
                    "metric": str(index),
                }
            )
            rows.append(
                {
                    "trace_id": trace,
                    "system_type": STATS.BANK,
                    "metric": str(index + 10),
                }
            )
        result = STATS.paired_sign_test(rows, "metric")
        self.assertEqual(result["matched_pairs"], 3)
        self.assertEqual(result["proofrail_lower"], 3)
        self.assertEqual(result["p_value_one_tailed"], 0.125)


if __name__ == "__main__":
    unittest.main()
