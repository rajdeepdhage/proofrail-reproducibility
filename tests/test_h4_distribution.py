from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "h4_distribution_test", ROOT / "metrics" / "h4_distribution_test.py"
)
assert SPEC and SPEC.loader
H4 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(H4)


class DistributionTest(unittest.TestCase):
    def test_identical_samples_have_zero_distance(self) -> None:
        values = [0.0, 1.0, 1.0, 2.0, 5.0]
        self.assertEqual(H4.ks_statistic(values, values), 0.0)
        self.assertEqual(H4.asymptotic_two_sided_p(0.0, 5, 5), 1.0)

    def test_separated_samples_have_maximum_distance(self) -> None:
        d = H4.ks_statistic([0.0, 1.0, 2.0], [10.0, 11.0, 12.0])
        self.assertEqual(d, 1.0)
        self.assertLess(H4.asymptotic_two_sided_p(d, 3, 3), 0.05)


if __name__ == "__main__":
    unittest.main()
