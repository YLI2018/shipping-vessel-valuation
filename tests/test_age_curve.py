"""Checks that the M1 results stay as published, and that bad input is refused.

Run from the repository root:  python3 -m unittest discover -s tests
"""
import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shipping_valuation.data.ingest import load_comparables
from shipping_valuation.models.age_curve import fit_age_curve
from shipping_valuation.evaluation.backtesting import leave_one_out


class PublishedResults(unittest.TestCase):
    """The figures in the README and the technical note (version 1.1, 43 sales)."""

    @classmethod
    def setUpClass(cls):
        _, cls.ages, cls.prices = load_comparables(ROOT / "data" / "sample" / "comparables.csv")
        cls.curve = fit_age_curve(cls.ages, cls.prices)

    def test_curve(self):
        self.assertEqual(self.curve.n, 43)
        self.assertAlmostEqual(self.curve.a, 101.32, places=2)
        self.assertAlmostEqual(self.curve.b, -0.08773, places=5)
        self.assertAlmostEqual(self.curve.loss_per_year, 0.0840, places=4)
        self.assertAlmostEqual(self.curve.r_squared, 0.911, places=3)

    def test_value_and_range(self):
        self.assertAlmostEqual(self.curve.value(14), 29.67, places=2)
        low, high = self.curve.value_range(14)
        self.assertAlmostEqual(low, 26.27, places=2)
        self.assertAlmostEqual(high, 33.06, places=2)

    def test_backtest(self):
        bt = leave_one_out(self.ages, self.prices)
        self.assertAlmostEqual(bt.average_miss, 0.0745, places=4)
        self.assertAlmostEqual(bt.bias, 0.0082, places=4)

    def test_backtest_whole_deals_held_out(self):
        deals = pd.read_csv(ROOT / "data" / "sample" / "comparables.csv")["deal"]
        bt = leave_one_out(self.ages, self.prices, deals)
        self.assertAlmostEqual(bt.average_miss, 0.0749, places=4)


class Method(unittest.TestCase):
    def test_exact_curve_is_recovered(self):
        ages = np.array([5, 10, 15, 20], float)
        prices = 80 * np.exp(-0.07 * ages)
        c = fit_age_curve(ages, prices)
        self.assertAlmostEqual(c.a, 80, places=9)
        self.assertAlmostEqual(c.b, -0.07, places=12)
        self.assertAlmostEqual(c.r_squared, 1.0, places=12)
        self.assertAlmostEqual(c.r, math.exp(-0.07), places=12)

    def test_bad_input_is_refused(self):
        with self.assertRaises(ValueError):
            fit_age_curve([5, 10], [40, 30])                 # too few sales
        with self.assertRaises(ValueError):
            fit_age_curve([5, 10, 15], [40, 0, 20])          # price not above 0
        with self.assertRaises(ValueError):
            fit_age_curve([10, 10, 10], [40, 30, 20])        # one age only


if __name__ == "__main__":
    unittest.main()
