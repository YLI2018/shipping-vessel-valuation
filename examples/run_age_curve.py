"""Value Target Ship 1 with the M1 age curve, run the leave-one-out back-test and draw the two figures.

Run from the repository root:  python3 examples/run_age_curve.py
Reads data/sample/comparables.csv; writes docs/figures/age_curve and backtest, as PDF and PNG.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))   # use the code in src/ without installing it

from vessel_valuation.data.load import load_comparables
from vessel_valuation.models.age_curve import fit_age_curve
from vessel_valuation.analytics.backtest import leave_one_out
from vessel_valuation.reporting.figures import age_curve_chart, backtest_chart

TARGET_AGE, KNOWN_PRICE = 14, 28.45      # Target Ship 1 on 22 May 2026

_, ages, prices = load_comparables(ROOT / "data" / "sample" / "comparables.csv")
curve = fit_age_curve(ages, prices)
bt = leave_one_out(ages, prices)
value = curve.value(TARGET_AGE)
low, high = curve.value_range(TARGET_AGE)

out = ROOT / "docs" / "figures"
out.mkdir(parents=True, exist_ok=True)
for ext in ("pdf", "png"):   # PDF for the technical note, PNG for the GitHub pages
    age_curve_chart(curve, ages, prices, TARGET_AGE, KNOWN_PRICE, out / f"age_curve.{ext}")
    backtest_chart(ages, bt, out / f"backtest.{ext}")

print(f"Comparables            {curve.n}")
print(f"a (level at age 0)     {curve.a:.2f}")
print(f"b (per year)           {curve.b:.5f}")
print(f"Value lost per year    {curve.loss_per_year:.1%}")
print(f"R² on log price        {curve.r_squared:.3f}")
print(f"Value at age {TARGET_AGE}        ${value:.2f}m  (range ${low:.2f}m – ${high:.2f}m)")
print(f"Reported price         ${KNOWN_PRICE:.2f}m  ({KNOWN_PRICE / value - 1:+.1%})")
print(f"Back-test average miss {bt.average_miss:.1%}   bias {bt.bias:+.1%}")
