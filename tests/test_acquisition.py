"""Checks that the M3 acquisition and finance results stay as published (the M3 v3 workbook, recalculated in Excel).

Run from the repository root:  python3 -m unittest discover -s tests
"""
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shipping_valuation.models.dcf import load_inputs
from shipping_valuation.models.acquisition import load_finance, deal, max_bid, sensitivity


class PublishedResults(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p = load_inputs(ROOT / "data" / "sample" / "dcf_inputs.json")
        cls.f = load_finance(ROOT / "data" / "sample" / "acquisition_inputs.json")
        cls.d = deal(cls.p, cls.f)

    def test_loan_and_equity(self):
        self.assertAlmostEqual(self.d.loan, 17.07, places=6)
        self.assertAlmostEqual(self.d.equity_in, 12.69295, places=5)
        self.assertAlmostEqual(self.d.cost_of_equity, 0.11047, places=5)

    def test_owners_cash_and_returns(self):
        for got, want in zip(self.d.owners, [-12.69295, 2.836045, 1.424617, 0.880109, 0.332419, 4.161885]):
            self.assertAlmostEqual(got, want, places=3)   # M2's opex growth is stored to 6 decimals
        self.assertAlmostEqual(self.d.equity_irr, -0.08039, places=4)
        self.assertAlmostEqual(self.d.equity_npv, -5.658, places=3)
        self.assertAlmostEqual(self.d.multiple, 0.759, places=3)
        self.assertAlmostEqual(self.d.project_irr, 0.00717, places=4)

    def test_bank_tests(self):
        for got, want in zip(self.d.dscr, [2.082359, 1.56333, 1.361056, 1.14168, 1.14255]):
            self.assertAlmostEqual(got, want, places=4)
        self.assertEqual(sum(x < self.f.min_dscr for x in self.d.dscr), 2)       # years 4 and 5 below 1.20x
        self.assertAlmostEqual(self.d.min_headroom, 0.33686, places=5)
        self.assertAlmostEqual(self.d.max_fall, 0.25198, places=5)

    def test_max_bid(self):
        m = max_bid(self.p, self.f)
        self.assertAlmostEqual(m.return_bid, 22.216, places=3)
        self.assertEqual(m.value_rule_bid, 38.0)
        self.assertEqual(m.dscr_bid, 27.0)
        self.assertAlmostEqual(m.max_bid, 22.216, places=3)
        self.assertEqual(m.binding, "return")

    def test_sensitivities(self):
        """Boxes of the workbook's Sensitivities sheet (Excel data tables)."""
        s = lambda **k: sensitivity(self.p, self.f, **k)  # noqa: E731
        self.assertAlmostEqual(s(tce_change=-2000).equity_irr, -0.1848, places=4)
        self.assertAlmostEqual(s(sale_change=-0.2).equity_irr, -0.1738, places=4)
        self.assertAlmostEqual(s(tce_change=2000, sale_change=0.2).equity_irr, 0.0613, places=4)
        self.assertTrue(math.isnan(s(sale_change=-0.4).equity_irr))              # n/a in the workbook
        self.assertAlmostEqual(s(tce_change=-2000, rate_change=0.01).min_dscr, 0.7875, places=4)
        self.assertAlmostEqual(s(rate_change=-0.01).min_dscr, 1.1969, places=4)


if __name__ == "__main__":
    unittest.main()
