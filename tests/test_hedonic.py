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

from shipping_valuation.models.hedonic import FORMULA_A, FORMULA_B, prepare, fit, solve_by_hand, value
from shipping_valuation.evaluation.backtesting import leave_one_out_formula, time_ordered_formula

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
        self.assertEqual(int(self.mA.nobs), 297)
        self.assertEqual(int(self.mB.nobs), 45)

    def test_by_hand_equals_library(self):
        for m in (self.mA, self.mB):
            self.assertLess(np.max(np.abs(solve_by_hand(m) - m.params.values)), 1e-8)

    def test_values(self):
        self.assertAlmostEqual(value(self.mA, self.target).value, 29.22, places=2)
        self.assertAlmostEqual(value(self.mB, self.target).value, 26.29, places=2)

    def test_key_effects(self):
        b = self.mA.params
        self.assertAlmostEqual(np.exp(b["C(yard, Treatment('China'))[T.Japan]"]) - 1, 0.215, places=3)
        self.assertAlmostEqual(np.exp(b["scrubber"]) - 1, 0.089, places=3)

    def test_backtest(self):
        bt = leave_one_out_formula(FORMULA_B, self.mr, self.mr.index)
        self.assertAlmostEqual(bt.average_miss, 0.087, places=3)

    def test_same_sales_validation(self):
        test = self.sales[self.sales["m1_sale"].notna()]
        self.assertEqual(len(test), 43)
        one = leave_one_out_formula(FORMULA_B, self.mr, test.index)
        deal = leave_one_out_formula(FORMULA_B, self.mr, test.index, deal_col="deal")
        self.assertAlmostEqual(one.average_miss, 0.0853, places=4)
        self.assertAlmostEqual(deal.average_miss, 0.0913, places=4)
        self.assertGreater(deal.average_miss, one.average_miss)   # holding out whole deals removes the twin's help

    def test_time_ordered(self):
        s, mr = self.sales, self.mr
        comps = pd.read_csv(ROOT / "data" / "sample" / "comparables.csv")
        test = s[s["m1_sale"].notna()]
        eligible = [i for i in test.index
                    if (comps["report_week"] < s.at[i, "report_week"]).sum() >= 10
                    and (mr["report_week"] < s.at[i, "report_week"]).sum() >= 20
                    and (s["report_week"] < s.at[i, "report_week"]).sum() >= 60
                    and s.at[i, "yard"] in set(mr.loc[mr["report_week"] < s.at[i, "report_week"], "yard"])]
        self.assertEqual(len(eligible), 24)
        self.assertAlmostEqual(time_ordered_formula(FORMULA_A, s, eligible).average_miss, 0.0811, places=4)
        self.assertAlmostEqual(time_ordered_formula(FORMULA_B, mr, eligible).average_miss, 0.0710, places=4)


if __name__ == "__main__":
    unittest.main()
