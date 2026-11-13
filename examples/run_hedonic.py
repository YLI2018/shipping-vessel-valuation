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
from shipping_valuation.evaluation.backtesting import leave_one_out, leave_one_out_formula, time_ordered_formula
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

print("Step 6  Same-sales validation: M1, model A and model B scored on M1's 43 comparables")
comps = pd.read_csv(ROOT / "data" / "sample" / "comparables.csv")
test = sales[sales["m1_sale"].notna()]
test = test.loc[test["m1_sale"].map({s: i for i, s in enumerate(comps["sale"])}).sort_values().index]
price_22may = test["m1_sale"].map(comps.set_index("sale")["adjusted_price_musd"])   # M1's price moved to 22 May
rows = []
for name, deals in (("Test 1  leave one sale out", None), ("Test 2  leave one DEAL out", "deal")):
    for label, quarter, observed in (("prices at 22 May", "2026Q2", price_22may), ("prices at report date", None, None)):
        a = leave_one_out_formula(FORMULA_A, sales, test.index, deals, quarter, observed)
        b = leave_one_out_formula(FORMULA_B, mr, test.index, deals, quarter, observed)
        m1 = leave_one_out(comps["age"], comps["adjusted_price_musd"], comps["deal"] if deals else None)
        rows.append((f"{name}, {label}", m1, a, b))
# Test 3: earlier report weeks only; start once there are >= 10 earlier M1 comparables, >= 20 earlier MR sales and
# >= 60 earlier sales, and the ship's yard country has been seen among earlier MR sales
eligible = [i for i in test.index
            if (comps["report_week"] < sales.at[i, "report_week"]).sum() >= 10
            and (mr["report_week"] < sales.at[i, "report_week"]).sum() >= 20
            and (sales["report_week"] < sales.at[i, "report_week"]).sum() >= 60
            and sales.at[i, "yard"] in set(mr.loc[mr["report_week"] < sales.at[i, "report_week"], "yard"])]
rows.append((f"Test 3  earlier report weeks only ({len(eligible)} sales)", None,
             time_ordered_formula(FORMULA_A, sales, eligible), time_ordered_formula(FORMULA_B, mr, eligible)))
for name, m1, a, b in rows:
    m1_text = f"M1 {m1.average_miss:5.1%} ({m1.bias:+.1%})" if m1 is not None else "M1 needs the broker benchmark (private)"
    print(f"        {name:<52} {m1_text}   A {a.average_miss:5.1%} ({a.bias:+.1%})   B {b.average_miss:5.1%} ({b.bias:+.1%})")
print("        average miss (bias); Test 3 for M1 is run privately because it needs the licensed broker benchmark")
