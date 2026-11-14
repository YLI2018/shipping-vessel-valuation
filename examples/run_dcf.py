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

# figure: value and sale price against the long-run TCE
xs = list(range(10000, 24001, 500))
vals = [value(replace(p, tce_long_run=x)) for x in xs]
fig, ax = plt.subplots(figsize=(7.5, 3.5))
ax.plot(xs, [v.value for v in vals], color="#0B3D5C", lw=2, label="DCF value (sale from earnings)")
ax.plot(xs, [v.sale for v in vals], color="#B87927", lw=1.6, label=f"Sale price at age {p.ship_age + p.hold}")
ax.axhline(p.price_tested, color="black", ls="--", lw=1)
ax.text(xs[0] + 100, p.price_tested + 0.6, f"price tested ${p.price_tested:.2f}m", fontsize=8)
m1_sale = sale_from_curve(p, curve)
ax.axhline(m1_sale, color="#8A93A0", ls=":", lw=1)
ax.text(xs[0] + 100, m1_sale + 0.6, f"M1 curve at age {p.ship_age + p.hold}: ${m1_sale:.2f}m", fontsize=8, color="#8A93A0")
for x_, lab, c in [(p.tce_long_run, f"used: {p.tce_long_run:,.0f}", "#087F82"), (be, f"price needs: {be:,.0f}", "#B03A2E")]:
    ax.axvline(x_, color=c, lw=1)
    ax.text(x_ + 120, 2, lab, fontsize=8, color=c, rotation=90, va="bottom")
ax.set_xlabel("Long-run TCE, year 4 onwards ($/day)")
ax.set_ylabel("$m")
ax.set_title("The long-run TCE sets both the later earnings and the sale price", fontsize=9.5, color="#0B3D5C")
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
out = ROOT / "docs" / "methodology" / "figures" / "dcf_longrun_tce"
for ext in ("pdf", "png"):
    fig.savefig(f"{out}.{ext}", dpi=200, bbox_inches="tight")
print(f"\nFigure written: {out}.png")
