"""M3 acquisition and finance for Target Ship 1: owners' return, bank tests, maximum bid, sensitivities.

Run from the repository root:  python3 examples/run_acquisition.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shipping_valuation.models.dcf import load_inputs
from shipping_valuation.models.acquisition import load_finance, deal, max_bid, sensitivity

p = load_inputs(ROOT / "data" / "sample" / "dcf_inputs.json")
f = load_finance(ROOT / "data" / "sample" / "acquisition_inputs.json")
d = deal(p, f)

print(f"Price tested ${d.price:.2f}m, loan ${d.loan:.2f}m, equity put in ${d.equity_in:.2f}m")
print("Owners' cash, years 0-5 ($m):", ", ".join(f"{x:.3f}" for x in d.owners))
print(f"Equity IRR {d.equity_irr:.1%} vs cost of equity {d.cost_of_equity:.2%}; NPV ${d.equity_npv:.2f}m; "
      f"money multiple {d.multiple:.2f}x; project IRR {d.project_irr:.1%} (WACC {p.wacc:.2%})")
print("Debt service cover, years 1-5:", ", ".join(f"{x:.2f}" for x in d.dscr), f"(minimum {f.min_dscr:.2f}x)")
print(f"Value-rule headroom {d.min_headroom:.1%}; value can fall {d.max_fall:.1%}")
m = max_bid(p, f)
print(f"Bids: return {m.return_bid:.2f}, value rule {m.value_rule_bid:.1f}, debt service {m.dscr_bid:.1f} "
      f"-> MAXIMUM BID ${m.max_bid:.2f}m (limited by {m.binding})")

print("\nEquity IRR: hire change (rows) x sale value change (columns)")
cols = (-0.4, -0.2, 0.0, 0.2, 0.4)
print("        " + "".join(f"{c:>9.0%}" for c in cols))
for t in (-4000, -2000, 0, 2000, 4000):
    cells = [sensitivity(p, f, tce_change=t, sale_change=c).equity_irr for c in cols]
    print(f"{t:>+7,}" + "".join("      n/a" if x != x else f"{x:>9.1%}" for x in cells))
