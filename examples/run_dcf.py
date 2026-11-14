"""Value Target Ship 1 with the M2 DCF: cash year by year, the sale price at the end (two bases), what the price is
betting on, and the sensitivity to the long-run TCE. Draws one figure.

Run from the repository root:  python3 examples/run_dcf.py
Reads data/sample/dcf_inputs.json and data/sample/comparables.csv (for the M1 curve);
writes docs/methodology/figures/dcf_longrun_tce (PDF and PNG).
"""
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shipping_valuation.data.ingest import load_comparables  # noqa: E402
from shipping_valuation.models.age_curve import fit_age_curve  # noqa: E402
from shipping_valuation.models.dcf import load_inputs, value, breakeven_long_run_tce, sale_from_curve  # noqa: E402

p = load_inputs(ROOT / "data" / "sample" / "dcf_inputs.json")
_, ages, prices = load_comparables(ROOT / "data" / "sample" / "comparables.csv")
curve = fit_age_curve(ages, prices)

print(f"Step 1  Discount rate: Ke = {p.risk_free:.2%} + {p.beta:.2f} x {p.erp:.2%} = {p.cost_of_equity:.2%}; "
      f"WACC = {1 - p.debt_share:.1%} x {p.cost_of_equity:.2%} + {p.debt_share:.1%} x {p.cost_of_debt:.2%} = {p.wacc:.2%}")

base = value(p)
print("\nStep 2  Cash year by year ($m), sale priced from the earnings left")
print(" year age    TCE  days revenue   opex drydock   cash   sale     DF     PV")
for r in base.rows:
    print(f"{r.year:5d} {r.age:3d} {r.tce:6,.0f} {r.days:5.0f} {r.revenue:7.3f} {r.opex:6.3f} {r.drydock:7.3f} "
          f"{r.cash:6.3f} {r.sale:6.3f} {r.discount_factor:.4f} {r.present_value:6.3f}")

market = value(replace(p, exit_basis="market"), curve=curve)
print(f"\nStep 3  Sale at age {p.ship_age + p.hold}: from earnings ${base.sale:.2f}m | today's market (M1 curve) "
      f"${sale_from_curve(p, curve):.2f}m")
print(f"        DCF value: ${base.value:.2f}m (earnings) | ${market.value:.2f}m (today's market)")

print(f"\nStep 4  Price tested ${p.price_tested:.2f}m: gap {base.value - p.price_tested:+.2f} $m; IRR {base.irr:.2%} vs WACC {p.wacc:.2%}")
print(f"        Average TCE assumed ${base.avg_tce:,.0f}/day; implied TCE at the price ${base.implied_tce:,.0f}/day (sale held)")
be = breakeven_long_run_tce(p)
print(f"        Long-run TCE at which value = price: ${be:,.0f}/day (model uses ${p.tce_long_run:,.0f})")

print("\nStep 5  Holding period does not change the value with the earnings-based sale:")
for h in (3, 5, 7):
    print(f"        hold {h} years: ${value(replace(p, hold=h)).value:.2f}m")

# figure: what the ship is worth today for each level of long-run daily earnings
xs = list(range(10000, 24001, 500))
vals = [value(replace(p, tce_long_run=x)) for x in xs]
sale_age = p.ship_age + p.hold
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(xs, [v.value for v in vals], color="#0B3D5C", lw=2.2, label="Ship's worth today (DCF value)")
ax.plot(xs, [v.sale for v in vals], color="#B87927", lw=1.8, label=f"Price the ship sells for at age {sale_age}, in {p.hold} years")
ax.axhline(p.price_tested, color="black", ls="--", lw=1, label=f"Price actually paid for the ship: ${p.price_tested:.2f}m")
m1_sale = sale_from_curve(p, curve)
ax.axhline(m1_sale, color="#8A93A0", ls=":", lw=1.2,
           label=f"Today's market price of a {sale_age}-year-old ship (M1): ${m1_sale:.2f}m")
base = value(p)
ax.plot([p.tce_long_run], [base.value], "o", color="#0B3D5C")
ax.annotate(f"Assumed: ${p.tce_long_run:,.0f}/day\nworth ${base.value:.2f}m", (p.tce_long_run, base.value),
            xytext=(11800, 24.2), fontsize=8.5, color="#0B3D5C",
            arrowprops=dict(arrowstyle="->", color="#0B3D5C", lw=0.8))
ax.plot([be], [p.price_tested], "o", color="#B03A2E")
ax.annotate(f"Needed to justify the price paid:\n${be:,.0f}/day", (be, p.price_tested),
            xytext=(20200, 9.5), fontsize=8.5, color="#B03A2E",
            arrowprops=dict(arrowstyle="->", color="#B03A2E", lw=0.8))
ax.set_xlabel(f"Ship's earnings per day from age {p.ship_age + 4} to {p.life} (long-run TCE, $/day)")
ax.set_ylabel("$ million")
ax.set_title(f"What the ship is worth today, depending on its daily earnings from age {p.ship_age + 4}",
             fontsize=10, color="#0B3D5C")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.set_ylim(0, 40)
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
out = ROOT / "docs" / "methodology" / "figures" / "dcf_longrun_tce"
for ext in ("pdf", "png"):
    fig.savefig(f"{out}.{ext}", dpi=200, bbox_inches="tight")
print(f"\nFigure written: {out}.png")
