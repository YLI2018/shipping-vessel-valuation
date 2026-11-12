"""Checks that the M1+ hedonic results stay as published (technical note version 1.0).

Run from the repository root:  python3 -m unittest discover -s tests
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vessel_valuation.models.hedonic import FORMULA_A, FORMULA_B, prepare, fit, solve_by_hand, value
from vessel_valuation.analytics.backtest import leave_one_out_formula

TARGET = pd.DataFrame([dict(segment="MR", type="Tanker", tanker=1, age=13.889117, dwt=51768, yard="Korea", survey_due_12m=1,
                            survey_unknown=0, scrubber=0, eco=0, en_bloc_sale=0, quarter="2026Q2")])


class PublishedHedonicResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sales = prepare(pd.read_csv(ROOT / "data" / "sample" / "hedonic_sales.csv"))
        cls.mr = cls.sales[cls.sales["segment"] == "MR"]
        cls.mA, cls.mB = fit(FORMULA_A, cls.sales), fit(FORMULA_B, cls.mr)
        cls.target = prepare(TARGET)

    def test_samples(self):
        self.assertEqual(int(self.mA.nobs), 298)
        self.assertEqual(int(self.mB.nobs), 46)

    def test_by_hand_equals_library(self):
        for m in (self.mA, self.mB):
            self.assertLess(np.max(np.abs(solve_by_hand(m) - m.params.values)), 1e-8)

    def test_values(self):
        self.assertAlmostEqual(value(self.mA, self.target).value, 29.34, places=2)
        self.assertAlmostEqual(value(self.mB, self.target).value, 26.31, places=2)

    def test_key_effects(self):
        b = self.mA.params
        self.assertAlmostEqual(np.exp(b["C(yard, Treatment('China'))[T.Japan]"]) - 1, 0.216, places=3)
        self.assertAlmostEqual(np.exp(b["scrubber"]) - 1, 0.088, places=3)

    def test_backtest(self):
        bt = leave_one_out_formula(FORMULA_B, self.mr, self.mr.index)
        self.assertAlmostEqual(bt.average_miss, 0.087, places=3)


if __name__ == "__main__":
    unittest.main()
