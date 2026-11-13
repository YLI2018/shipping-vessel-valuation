"""M1+ hedonic model, step by step: fit models A and B, value Target Ship 1, leave-one-out validation on MR sales, draw the charts.

Run from the repository root:  python3 examples/run_hedonic.py
Reads data/sample/hedonic_sales.csv (anonymised; sales reported on or before 22 May 2026).
Writes docs/methodology/figures/hedonic_effects and hedonic_backtest, as PDF and PNG.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shipping_valuation.models.hedonic import FORMULA_A, FORMULA_B, prepare, fit, solve_by_hand, terms_for, value, effects
from shipping_valuation.evaluation.backtesting import leave_one_out_formula
from shipping_valuation.reporting.figures import hedonic_effects_chart, hedonic_backtest_chart

# Target Ship 1 on 22 May 2026: MR, built 2012 in Korea, 51,768 dwt, survey due within 12 months
TARGET = pd.DataFrame([dict(segment="MR", type="Tanker", tanker=1, age=13.889117, dwt=51768, yard="Korea", survey_due_12m=1,
                            survey_unknown=0, scrubber=0, eco=0, en_bloc_sale=0, quarter="2026Q2")])
KNOWN_PRICE, M1_VALUE, M1_MISS = 28.45, 29.67, 0.07452

print("Step 1  Read the sales")
sales = prepare(pd.read_csv(ROOT / "data" / "sample" / "hedonic_sales.csv"))
mr = sales[sales["segment"] == "MR"]
target = prepare(TARGET)
print(f"        model A: {len(sales)} tanker and bulker sales; model B: {len(mr)} MR sales")

print("Step 2  Fit both models by OLS, and check the coefficients by hand: b = (X'X)^-1 X'y")
mA, mB = fit(FORMULA_A, sales), fit(FORMULA_B, mr)
for name, m in (("A", mA), ("B", mB)):
    diff = np.max(np.abs(solve_by_hand(m) - m.params.values))
    print(f"        model {name}: n = {int(m.nobs)}, R² = {m.rsquared:.3f}, by hand vs library: largest difference {diff:.1e}")

print("Step 3  What moves the price (model A)")
print(effects(mA)[["term", "b", "p", "effect", "reliable"]].round(4).to_string(index=False))

print("Step 4  Value Target Ship 1, term by term (model B shown)")
print(terms_for(mB, target).round(5).to_string(index=False))
vA, vB = value(mA, target), value(mB, target)
for name, v in (("A", vA), ("B", vB)):
    print(f"        model {name}: e^{v.ln_price:.4f} x smearing {v.smearing:.4f} = ${v.value:.2f}m "
          f"(68% range ${v.low:.2f}m – ${v.high:.2f}m); reported ${KNOWN_PRICE}m is {KNOWN_PRICE / v.value - 1:+.1%}")
print(f"        M1 age curve: ${M1_VALUE}m")

print("Step 5  Leave-one-out validation on MR sales (not a historical forecasting test)")
btA = leave_one_out_formula(FORMULA_A, sales, mr.index)
btB = leave_one_out_formula(FORMULA_B, mr, mr.index)
for name, bt in (("A", btA), ("B", btB)):
    print(f"        model {name}: average miss {bt.average_miss:.1%}, bias {bt.bias:+.1%}")
print(f"        M1 age curve: average miss {M1_MISS:.1%}, bias +0.8%")

out = ROOT / "docs" / "methodology" / "figures"
out.mkdir(parents=True, exist_ok=True)
for ext in ("pdf", "png"):
    hedonic_effects_chart(effects(mA), out / f"hedonic_effects.{ext}")
    hedonic_backtest_chart(mr["age"].values, btA, btB, out / f"hedonic_backtest.{ext}")
print("Charts written to docs/methodology/figures/")
