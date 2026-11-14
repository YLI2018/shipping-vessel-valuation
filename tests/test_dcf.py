"""Checks that the M2 DCF results stay as published, and that the model behaves as described.

Run from the repository root:  python3 -m unittest discover -s tests
"""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shipping_valuation.data.ingest import load_comparables
from shipping_valuation.models.age_curve import fit_age_curve
from shipping_valuation.models.dcf import load_inputs, value, breakeven_long_run_tce, sale_from_curve


class PublishedResults(unittest.TestCase):
    """The figures on the M2 page (the same as the M2 v4 workbook, recalculated in Excel)."""

    @classmethod
    def setUpClass(cls):
        cls.p = load_inputs(ROOT / "data" / "sample" / "dcf_inputs.json")
        _, ages, prices = load_comparables(ROOT / "data" / "sample" / "comparables.csv")
        cls.curve = fit_age_curve(ages, prices)
        cls.base = value(cls.p)

    def test_discount_rate(self):
        self.assertAlmostEqual(self.p.cost_of_equity, 0.0774, places=6)
        self.assertAlmostEqual(self.p.wacc, 0.0730, places=4)

    def test_value_and_sale(self):
        self.assertAlmostEqual(self.base.value, 26.875, places=3)
        self.assertAlmostEqual(self.base.sale, 11.490, places=3)

    def test_today_market_basis(self):
        m = value(replace(self.p, exit_basis="market"), curve=self.curve)
        self.assertAlmostEqual(sale_from_curve(self.p, self.curve), 19.132, places=3)
        self.assertAlmostEqual(m.value, 32.247, places=3)

    def test_price_tests(self):
        self.assertAlmostEqual(self.base.avg_tce, 22597, delta=1)
        self.assertAlmostEqual(self.base.implied_tce, 23690, delta=1)
        self.assertAlmostEqual(self.base.irr, 0.0544, places=4)
        self.assertAlmostEqual(breakeven_long_run_tce(self.p), 16925, delta=2)


class Behaviour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = load_inputs(ROOT / "data" / "sample" / "dcf_inputs.json")

    def test_holding_period_does_not_change_value(self):
        """With the earnings-based sale the ship is worth its cash to the end of life, whoever owns it."""
        v = [value(replace(self.p, hold=h)).value for h in range(1, self.p.life - self.p.ship_age + 1)]
        self.assertAlmostEqual(min(v), max(v), places=9)

    def test_hold_beyond_economic_life_is_rejected(self):
        with self.assertRaises(ValueError):
            value(replace(self.p, hold=self.p.life - self.p.ship_age + 1))

    def test_commission_over_whole_life(self):
        """2.5% commission off the hire in every year, the sale price included."""
        self.assertAlmostEqual(value(replace(self.p, commission=0.025)).value, 25.589, places=3)

    def test_implied_tce_closes_the_gap(self):
        """Paying the implied TCE in every year of the hold (sale held) makes the value equal the price."""
        b = value(self.p)
        shift = b.implied_tce - b.avg_tce
        v = b.value + shift * b.converter
        self.assertAlmostEqual(v, self.p.price_tested, places=9)

    def test_value_rises_with_long_run_tce(self):
        lo = value(replace(self.p, tce_long_run=15000)).value
        hi = value(replace(self.p, tce_long_run=17000)).value
        self.assertLess(lo, value(self.p).value)
        self.assertLess(value(self.p).value, hi)

    def test_relevered_debt_share(self):
        q = self.p.relevered(0.6)
        self.assertAlmostEqual(q.beta, 1.60, places=6)
        self.assertAlmostEqual(q.wacc, 0.0775, places=4)


if __name__ == "__main__":
    unittest.main()
