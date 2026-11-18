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
Maximum bid = lowest of: the return bid (price where the owners' NPV at the cost of equity is zero, i.e. equity
IRR = cost of equity), the highest grid price keeping the value rule, the highest grid price keeping the debt
service cover. The deal is re-run at the maximum bid to confirm all three tests pass. A test that still passes at
the top of the grid is flagged: no limit was found inside the grid. Monthly liquidity is not part of the bid.
"""
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

from .dcf import DCFInputs, _year, irr, irr_note, sale_from_earnings


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
    dscr: list             # years 1 .. hold; None in a year with no debt service (no loan left)
    headroom: list         # value rule, years 0 .. hold: (value / owed) / clause - 1; None when nothing is owed
    max_fall: float        # lowest 1 - owed x clause / value; None if nothing is ever owed
    cost_of_equity: float
    equity_irr: float
    equity_npv: float
    multiple: float
    project_irr: float
    sale_net: float
    equity_irr_note: str = ""   # why equity_irr is NaN: no IRR exists, or several IRRs exist

    @property
    def min_dscr(self):
        """Lowest debt service cover over the years with debt service; None if there is no loan."""
        x = [v for v in self.dscr if v is not None]
        return min(x) if x else None

    @property
    def min_headroom(self):
        """Lowest value-rule headroom over the years a loan is owed; None if there is no loan."""
        x = [v for v in self.headroom if v is not None]
        return min(x) if x else None


def _value(f: FinanceInputs, age: float) -> float:
    return f.curve_a * math.exp(f.curve_b * age)


def cost_of_equity(p: DCFInputs, f: FinanceInputs) -> float:
    """CAPM at our loan: beta without debt (no tax) / (1 - loan-to-value). 0.61 / 0.4 = 1.53 -> 11.05%."""
    return p.risk_free + p.beta_without_debt / (1 - f.ltv) * p.erp


def validate(p: DCFInputs, f: FinanceInputs, price: float = None) -> None:
    """Stop with a clear message before calculating if an input is outside its allowed range (as the workbook's
    range checks on the Inputs sheet)."""
    price = p.price_tested if price is None else price
    life_left = p.life - p.ship_age
    rules = [
        (price > 0, f"price must be above 0 (got {price})"),
        (isinstance(p.hold, int) and 1 <= p.hold <= 10, f"holding period must be a whole number of 1 to 10 years "
                                                        f"(got {p.hold})"),
        (p.hold <= life_left, f"holding period {p.hold} years goes past the economic life: the ship is "
                              f"{p.ship_age} years old and the life is {p.life} years, so at most {life_left}"),
        (0 <= f.ltv <= 0.9, f"loan-to-value must be 0% to 90% (got {f.ltv:.0%})"),
        (f.repayment_years >= 1, f"repayment profile must be at least 1 year (got {f.repayment_years})"),
        (0 <= f.acquisition_costs <= 0.1, f"acquisition costs must be 0% to 10% (got {f.acquisition_costs})"),
        (f.working_capital >= 0, f"working capital must be 0 or more (got {f.working_capital})"),
        (0 <= f.sale_commission <= 0.1, f"sale commission must be 0% to 10% (got {f.sale_commission})"),
        (0 <= f.fee <= 0.05, f"arrangement fee must be 0% to 5% (got {f.fee})"),
        (1 <= f.min_value_clause <= 2, f"minimum value clause must be 1.00 to 2.00 x the loan "
                                       f"(got {f.min_value_clause})"),
        (1 <= f.min_dscr <= 3, f"minimum debt service cover must be 1.00 to 3.00 x (got {f.min_dscr})"),
        (f.grid_start > 0, f"price grid must start above 0 (got {f.grid_start})"),
        (f.grid_step > 0, f"price grid step must be above 0 (got {f.grid_step})"),
        (isinstance(f.grid_n, int) and f.grid_n >= 2, f"price grid needs at least 2 prices (got {f.grid_n})"),
    ]
    errors = [msg for ok, msg in rules if not ok]
    if errors:
        raise ValueError("M3 inputs outside their allowed range: " + "; ".join(errors))


def deal(p: DCFInputs, f: FinanceInputs, price: float = None) -> DealResult:
    """Owners' cash, returns and bank tests at one price (default: the price tested)."""
    validate(p, f, price)
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
        dscr.append(cash / (interest + rep) if interest + rep > 0 else None)   # no loan left: not applicable
        owed.append(bal - rep)          # what we owe at the year end (the balloon is still owed in the sale year)
        bal = bal - rep - balloon
    head, falls = [], []
    for t, o in enumerate(owed):
        val = _value(f, p.ship_age + t)
        if o <= 1e-12:                   # nothing owed this year: the bank's value rule does not apply
            head.append(None)
            continue
        head.append(val / o / f.min_value_clause - 1)
        falls.append(1 - o * f.min_value_clause / val)
    ke = cost_of_equity(p, f)
    npv = owners[0] + sum(c / (1 + ke) ** t for t, c in enumerate(owners) if t > 0)
    back = sum(c for c in owners[1:] if c > 0)
    out = -owners[0] - sum(c for c in owners[1:] if c < 0)
    return DealResult(price=price, loan=loan, equity_in=-owners[0], owners=owners, project=project, dscr=dscr,
                      headroom=head, max_fall=min(falls) if falls else None, cost_of_equity=ke, equity_irr=irr(owners), equity_npv=npv,
                      multiple=back / out, project_irr=irr(project), sale_net=sale_net,
                      equity_irr_note=irr_note(owners))


@dataclass
class MaxBid:
    return_bid: float      # price where the owners' NPV at the cost of equity = 0 (equity IRR = cost of equity)
    value_rule_bid: float  # highest grid price keeping the value rule every year (None = none)
    dscr_bid: float        # highest grid price keeping the debt service cover every year (None = none)
    max_bid: float
    binding: str
    value_rule_at_grid_top: bool = False   # True: passes even at the top of the grid, so no limit was found
    dscr_at_grid_top: bool = False
    retest: dict = None    # the deal re-run at the maximum bid: each test, passed or not


def _return_bid(p: DCFInputs, f: FinanceInputs, grid):
    """Price where the owners' NPV at the cost of equity is zero. NPV falls as the price rises, so the grid
    brackets it; bisection on NPV (not IRR) gives the exact price."""
    npv = lambda x: deal(p, f, x).equity_npv  # noqa: E731
    vals = [npv(x) for x in grid]
    if vals[0] < 0:
        return None                      # no grid price earns the required return
    if vals[-1] >= 0:
        return grid[-1]                  # every grid price earns it: limited by the grid
    k = max(i for i, v in enumerate(vals) if v >= 0)
    lo, hi = grid[k], grid[k + 1]
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if npv(mid) >= 0 else (lo, mid)
    return lo


def max_bid(p: DCFInputs, f: FinanceInputs) -> MaxBid:
    """Repeat the deal at grid prices (18, 18.5 .. 38) and take the lowest of the three bids, as the workbook does;
    then re-run the deal at that price and confirm every test passes."""
    validate(p, f)
    grid = [f.grid_start + i * f.grid_step for i in range(f.grid_n)]
    deals = [deal(p, f, x) for x in grid]
    rb = _return_bid(p, f, grid)
    ok_cov = [d.price for d in deals if d.min_headroom is None or d.min_headroom >= 0]
    ok_dscr = [d.price for d in deals if d.min_dscr is None or d.min_dscr >= f.min_dscr]
    vb, db = (max(ok_cov) if ok_cov else None), (max(ok_dscr) if ok_dscr else None)
    top = dict(value_rule_at_grid_top=vb == grid[-1], dscr_at_grid_top=db == grid[-1])
    if rb is None or vb is None or db is None:
        return MaxBid(rb, vb, db, None, "no price passes " + ("the return" if rb is None else
                                                               "the value rule" if vb is None else "debt service"),
                      **top)
    m = min(rb, vb, db)
    binding = "return" if m == rb else "value rule" if m == vb else "debt service cover"
    d = deal(p, f, m)
    retest = {"return": d.equity_npv >= -1e-9,
              "value rule": d.min_headroom is None or d.min_headroom >= 0,
              "debt service cover": d.min_dscr is None or d.min_dscr >= f.min_dscr}
    return MaxBid(rb, vb, db, m, binding, retest=retest, **top)


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
    eq_irr = irr(owners)    # NaN when no single IRR exists (see the note)
    return replace(d, owners=owners, project=project, equity_irr=eq_irr, equity_npv=npv, multiple=back / out,
                   project_irr=irr(project), sale_net=sale_net, equity_irr_note=irr_note(owners))
