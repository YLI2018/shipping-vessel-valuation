"""M3 acquisition and finance: is a purchase at a given price good for the owners, can it be funded, and what is
the most we should pay?

Builds on the M2 DCF (same ship cash, same earnings-based sale price) and adds the price paid, a bank loan and the
owners' cash. Year 0 = purchase day; years 1 .. hold, cash at each year end; the ship is sold and the loan repaid at
the end of the hold.

    loan        = loan-to-value x min(price, value today from the M1 curve)
    repayment   = loan / repayment profile (years) each year; the rest (balloon) is repaid from the sale
    interest_t  = loan at the start of year t x (SOFR + SOFR step x (t - 1) + margin)
    owners_0    = - price x (1 + acquisition costs) - working capital + loan - arrangement fee x loan
    owners_t    = ship cash_t - interest_t - repayment_t  (+ sale x (1 - commission) + working capital - balloon at the end)
    project_t   = the same without the loan (ship cash only)
    cost of equity = risk-free + beta at our loan x ERP, beta at our loan = beta without debt / (1 - loan-to-value)

Bank tests:
    value rule       ship value_t >= minimum value clause x what we owe_t, every year 0 .. hold
    debt service     ship cash_t / (interest_t + scheduled repayment_t) >= minimum, every year (balloon excluded)
Maximum bid = lowest of: the return bid (price where equity IRR = cost of equity, interpolated on the grid),
the highest grid price keeping the value rule, the highest grid price keeping the debt service cover.
"""
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

from .dcf import DCFInputs, _year, irr, sale_from_earnings


@dataclass(frozen=True)
class FinanceInputs:
    acquisition_costs: float     # share of price
    working_capital: float       # $m, put in on day 1, back at the sale
    sale_commission: float       # share of the sale price
    ltv: float                   # loan-to-value
    repayment_years: float       # repayment profile
    sofr: float
    sofr_step: float             # change per year
    margin: float
    fee: float                   # arrangement fee, share of the loan
    min_value_clause: float      # value must be at least this x what we owe
    min_dscr: float
    curve_a: float               # M1 curve: value = a x exp(b x age)
    curve_b: float
    grid_start: float = 18.0
    grid_step: float = 0.5
    grid_n: int = 41


def load_finance(path) -> FinanceInputs:
    j = json.loads(Path(path).read_text())
    v = lambda k: j[k]["value"]  # noqa: E731
    return FinanceInputs(acquisition_costs=v("acquisition_costs"), working_capital=v("working_capital_musd"),
                         sale_commission=v("sale_commission"), ltv=v("loan_to_value"),
                         repayment_years=v("repayment_profile_years"), sofr=v("sofr"), sofr_step=v("sofr_step"),
                         margin=v("loan_margin"), fee=v("arrangement_fee"), min_value_clause=v("min_value_clause"),
                         min_dscr=v("min_dscr"), curve_a=v("m1_curve_a"), curve_b=v("m1_curve_b"),
                         grid_start=v("grid_start_musd"), grid_step=v("grid_step_musd"))


@dataclass
class DealResult:
    price: float
    loan: float
    equity_in: float
    owners: list           # owners' cash, years 0 .. hold
    project: list          # ship cash with no loan, years 0 .. hold
    dscr: list             # years 1 .. hold
    headroom: list         # value rule, years 0 .. hold: (value / owed) / clause - 1
    max_fall: float        # lowest 1 - owed x clause / value
    cost_of_equity: float
    equity_irr: float
    equity_npv: float
    multiple: float
    project_irr: float
    sale_net: float

    @property
    def min_dscr(self) -> float:
        return min(self.dscr)

    @property
    def min_headroom(self) -> float:
        return min(self.headroom)


def _value(f: FinanceInputs, age: float) -> float:
    return f.curve_a * math.exp(f.curve_b * age)


def cost_of_equity(p: DCFInputs, f: FinanceInputs) -> float:
    """CAPM at our loan: beta without debt (no tax) / (1 - loan-to-value). 0.61 / 0.4 = 1.53 -> 11.05%."""
    return p.risk_free + p.beta_without_debt / (1 - f.ltv) * p.erp


def deal(p: DCFInputs, f: FinanceInputs, price: float = None) -> DealResult:
    """Owners' cash, returns and bank tests at one price (default: the price tested)."""
    price = p.price_tested if price is None else price
    hold = p.hold
    loan = f.ltv * min(price, _value(f, p.ship_age))
    repay = loan / f.repayment_years
    sale_net = sale_from_earnings(p, p.wacc) * (1 - f.sale_commission)
    owners = [-price * (1 + f.acquisition_costs) - f.working_capital + loan - f.fee * loan]
    project = [-price * (1 + f.acquisition_costs) - f.working_capital]
    dscr, owed = [], [loan]
    bal = loan
    for t in range(1, hold + 1):
        cash = _year(p, t)[4]
        rate = f.sofr + f.sofr_step * (t - 1) + f.margin
        interest, rep = bal * rate, min(bal, repay)
        balloon = bal - rep if t == hold else 0.0
        end = sale_net + f.working_capital if t == hold else 0.0
        owners.append(cash - interest - rep - balloon + end)
        project.append(cash + end)
        dscr.append(cash / (interest + rep))
        owed.append(bal - rep)          # what we owe at the year end (the balloon is still owed in the sale year)
        bal = bal - rep - balloon
    head, falls = [], []
    for t, o in enumerate(owed):
        val = _value(f, p.ship_age + t)
        head.append(val / o / f.min_value_clause - 1)
        falls.append(1 - o * f.min_value_clause / val)
    ke = cost_of_equity(p, f)
    npv = owners[0] + sum(c / (1 + ke) ** t for t, c in enumerate(owners) if t > 0)
    back = sum(c for c in owners[1:] if c > 0)
    out = -owners[0] - sum(c for c in owners[1:] if c < 0)
    return DealResult(price=price, loan=loan, equity_in=-owners[0], owners=owners, project=project, dscr=dscr,
                      headroom=head, max_fall=min(falls), cost_of_equity=ke, equity_irr=irr(owners), equity_npv=npv,
                      multiple=back / out, project_irr=irr(project), sale_net=sale_net)


@dataclass
class MaxBid:
    return_bid: float      # price where equity IRR = cost of equity (interpolated)
    value_rule_bid: float  # highest grid price keeping the value rule every year (None = none)
    dscr_bid: float        # highest grid price keeping the debt service cover every year (None = none)
    max_bid: float
    binding: str


def max_bid(p: DCFInputs, f: FinanceInputs) -> MaxBid:
    """Repeat the deal at grid prices (18, 18.5 .. 38) and take the lowest of the three bids, as the workbook does."""
    grid = [f.grid_start + i * f.grid_step for i in range(f.grid_n)]
    deals = [deal(p, f, x) for x in grid]
    ke = deals[0].cost_of_equity
    k = sum(1 for d in deals if d.equity_irr >= ke)        # IRR falls as the price rises
    if k == 0:
        rb = None
    elif k == len(grid):
        rb = grid[-1]
    else:
        a, b = deals[k - 1].equity_irr, deals[k].equity_irr
        rb = grid[k - 1] + (a - ke) / (a - b) * f.grid_step
    ok_cov = [d.price for d in deals if d.min_headroom >= 0]
    ok_dscr = [d.price for d in deals if d.min_dscr >= f.min_dscr]
    vb, db = (max(ok_cov) if ok_cov else None), (max(ok_dscr) if ok_dscr else None)
    if rb is None or vb is None or db is None:
        return MaxBid(rb, vb, db, None, "no price passes " + ("the return" if rb is None else
                                                               "the value rule" if vb is None else "debt service"))
    m = min(rb, vb, db)
    binding = "return" if m == rb else "value rule" if m == vb else "debt service cover"
    return MaxBid(rb, vb, db, m, binding)


def sensitivity(p: DCFInputs, f: FinanceInputs, tce_change: float = 0.0, sale_change: float = 0.0,
                rate_change: float = 0.0) -> DealResult:
    """The deal with hire changed by tce_change $/day in every year owned, the net sale price x (1 + sale_change)
    and the interest rate + rate_change, as the workbook's Sensitivities sheet (what-if cells)."""
    q = replace(p, tce=tuple(x + tce_change for x in p.tce), tce_long_run=p.tce_long_run + tce_change) \
        if tce_change else p
    g = replace(f, sofr=f.sofr + rate_change) if rate_change else f
    d = deal(q, g)
    if tce_change:          # hire change applies to the years owned only; the sale price stays at the base case
        base_sale = deal(p, f).sale_net
        d = _with_sale(q, g, base_sale)
    if sale_change:
        d = _with_sale(q, g, (d.sale_net) * (1 + sale_change))
    return d


def _with_sale(p: DCFInputs, f: FinanceInputs, sale_net: float) -> DealResult:
    d = deal(p, f)
    diff = sale_net - d.sale_net
    owners = d.owners[:-1] + [d.owners[-1] + diff]
    project = d.project[:-1] + [d.project[-1] + diff]
    ke = d.cost_of_equity
    npv = owners[0] + sum(c / (1 + ke) ** t for t, c in enumerate(owners) if t > 0)
    back = sum(c for c in owners[1:] if c > 0)
    out = -owners[0] - sum(c for c in owners[1:] if c < 0)
    eq_irr = irr(owners)
    if eq_irr <= -0.8999:   # no rate in range sets the NPV to 0: shown as n/a, as in the workbook
        eq_irr = float("nan")
    return replace(d, owners=owners, project=project, equity_irr=eq_irr, equity_npv=npv, multiple=back / out,
                   project_irr=irr(project), sale_net=sale_net)
