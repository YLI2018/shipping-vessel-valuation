"""M2 discounted cash flow (DCF): value in use of a ship over a holding period, and what a price is betting on.

Year t = 1 .. hold, cash at each year end:
    earning days_t = earning days - dry-dock days in a survey year (every 5 years from the survey year)
    cash_t = TCE_t x (1 - commission) x earning days_t - opex x 365 x (1 + g)^(t-1) - survey cost in a survey year
             - EU ETS          (no survey in the last year of economic life: the ship is scrapped instead)
    value  = sum_t cash_t / (1 + r)^t  +  sale / (1 + r)^hold
TCE_t: the 1-, 2- and 3-year forecasts for t = 1..3, the long-run TCE after (in the hold and after the sale alike).
The hold must be 1 .. economic life - age.

Sale price at the end, two bases:
    "earnings"  (default) what a buyer at the sale would pay for the cash the ship can still earn: the long-run TCE
                (or the 1-3 year forecast, if the sale comes before year 3) from the sale to the end of economic life,
                less opex and surveys (none in the last year), plus scrap, discounted to the sale date at r. Consistent with the earnings forecast.
    "market"    the M1 age curve at the exit age (today's prices for an older ship), never below scrap.
r = WACC = (1 - Wd) x (Rf + beta x ERP) + Wd x Kd, before tax (tonnage tax).
"""
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class DCFInputs:
    ship_age: int
    price_tested: float          # $m, the price being checked (not used in any value)
    tce: tuple                   # $/day for years 1, 2, 3
    tce_long_run: float          # $/day from year 4, and after the sale
    earning_days: float
    opex: float                  # $/day
    opex_growth: float
    survey_year: int
    survey_cost: float           # $m
    drydock_days: float
    ets: float                   # $m a year
    hold: int
    life: int
    lightweight: float           # tonnes
    demolition: float            # $/LDT
    risk_free: float
    beta: float
    beta_unlevered: float
    erp: float
    cost_of_debt: float
    debt_share: float
    exit_basis: str = "earnings"  # "earnings" or "market"
    commission: float = 0.0       # share of hire lost to address and brokerage commission (0 = gross hire)
    tce_history_low: float = None  # $/day, scenario lever: average of the listed owner's three lowest years
    tce_history_avg: float = None  # $/day, scenario lever: the listed owner's long-run average
    rate_step: float = 0.01        # scenario lever: discount rate +/- this

    @property
    def cost_of_equity(self) -> float:
        return self.risk_free + self.beta * self.erp

    @property
    def wacc(self) -> float:
        return (1 - self.debt_share) * self.cost_of_equity + self.debt_share * self.cost_of_debt

    @property
    def scrap(self) -> float:
        return self.lightweight * self.demolition / 1e6

    @property
    def beta_without_debt(self) -> float:
        """Beta in use with its debt removed, no tax: beta x (1 - debt share). 0.75 x (1 - 0.184) = 0.61."""
        return self.beta * (1 - self.debt_share)

    def relevered(self, debt_share: float) -> "DCFInputs":
        """Same inputs with a different debt share. Hamada equation, no tax (tonnage tax), both ways:
        beta with debt = beta without debt / (1 - debt share). 0.61 / (1 - 0.60) = 1.53.
        Starts from the beta in use, not Damodaran's unlevered beta (0.64), which he made with a tax rate."""
        return replace(self, debt_share=debt_share, beta=self.beta_without_debt / (1 - debt_share))


def load_inputs(path) -> DCFInputs:
    j = json.loads(Path(path).read_text())
    v = lambda k: j[k]["value"]  # noqa: E731
    return DCFInputs(ship_age=j["ship_age"], price_tested=j["price_tested_musd"],
                     tce=(v("tce_year1_usd_day"), v("tce_year2_usd_day"), v("tce_year3_usd_day")),
                     tce_long_run=v("tce_long_run_usd_day"), earning_days=v("earning_days"), opex=v("opex_usd_day"),
                     opex_growth=v("opex_growth"), survey_year=v("survey_year"), survey_cost=v("survey_cost_musd"),
                     drydock_days=v("drydock_days"), ets=v("ets_musd_year"), hold=v("hold_years"),
                     life=v("economic_life_years"), lightweight=v("lightweight_t"), demolition=v("demolition_usd_ldt"),
                     risk_free=v("risk_free"), beta=v("beta"), beta_unlevered=v("beta_unlevered"),
                     erp=v("equity_risk_premium"), cost_of_debt=v("cost_of_debt"), debt_share=v("debt_share"),
                     tce_history_low=j.get("tce_history_low3_usd_day", {}).get("value"),
                     tce_history_avg=j.get("tce_history_avg_usd_day", {}).get("value"),
                     rate_step=j.get("scenario_rate_step", {}).get("value", 0.01))


@dataclass
class YearRow:
    year: int
    age: int
    tce: float
    days: float
    revenue: float
    opex: float
    drydock: float
    cash: float
    sale: float
    discount_factor: float

    @property
    def present_value(self) -> float:
        return (self.cash + self.sale) * self.discount_factor


def _tce(p: DCFInputs, t: int) -> float:
    return p.tce[t - 1] if t <= len(p.tce) else p.tce_long_run


def _year(p: DCFInputs, t: int):
    """Cash in DCF year t (counted from the base date), the same rule in the hold and after the sale."""
    last_year_of_life = t == p.life - p.ship_age
    survey = t >= p.survey_year and (t - p.survey_year) % 5 == 0 and not last_year_of_life
    days = p.earning_days - (p.drydock_days if survey else 0)
    revenue = _tce(p, t) * (1 - p.commission) * days / 1e6
    opex = p.opex * 365 * (1 + p.opex_growth) ** (t - 1) / 1e6
    drydock = p.survey_cost if survey else 0.0
    return days, revenue, opex, drydock, revenue - opex - drydock - p.ets


def sale_from_earnings(p: DCFInputs, rate: float) -> float:
    """Value at the sale date of the cash a buyer can still earn to the end of life, plus scrap."""
    left = p.life - p.ship_age - p.hold
    if left == 0:
        return p.scrap
    total = 0.0
    for k in range(1, left + 1):
        cash = _year(p, p.hold + k)[4]
        total += (cash + (p.scrap if k == left else 0.0)) / (1 + rate) ** k
    return total


def sale_from_curve(p: DCFInputs, curve) -> float:
    """M1 age-curve value at the exit age (today's market), never below scrap."""
    return max(curve.value(p.ship_age + p.hold), p.scrap)


@dataclass
class DCFResult:
    rows: list
    rate: float
    sale: float
    value: float
    avg_tce: float          # TCE weighted by earning days x discount factor
    converter: float        # $m today of $1 a day in every year of the hold
    implied_tce: float      # average TCE at which value = price, sale held fixed
    irr: float


def irr(flows, lo=-0.9, hi=1.0) -> float:
    """Rate at which the net present value of the flows is zero (bisection)."""
    npv = lambda r: sum(c / (1 + r) ** i for i, c in enumerate(flows))  # noqa: E731
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if npv(mid) > 0 else (lo, mid)
    return (lo + hi) / 2


def value(p: DCFInputs, curve=None, rate: float = None, tce_change: float = 0.0, sale: float = None) -> DCFResult:
    """Run the DCF. `curve` (an M1 AgeCurve) is needed only for exit_basis = "market".
    tce_change: earnings in every year of the hold x (1 + tce_change) (scenarios); sale: a fixed sale price instead."""
    if not 1 <= p.hold <= p.life - p.ship_age:
        raise ValueError(f"hold must be 1 to {p.life - p.ship_age} years (economic life {p.life} - age {p.ship_age})")
    r = p.wacc if rate is None else rate
    if sale is None:
        sale = sale_from_earnings(p, r) if p.exit_basis == "earnings" else sale_from_curve(p, curve)
    rows, v, conv, wtce = [], 0.0, 0.0, 0.0
    for t in range(1, p.hold + 1):
        tce = _tce(p, t) * (1 + tce_change)
        days, rev, opx, dd, cash = _year(p, t)
        if tce_change:
            rev, cash = rev * (1 + tce_change), cash + rev * tce_change
        df = 1 / (1 + r) ** t
        row = YearRow(t, p.ship_age + t, tce, days, rev, opx, dd, cash, sale if t == p.hold else 0.0, df)
        rows.append(row)
        v += row.present_value
        conv += days * df / 1e6
        wtce += tce * days * df / 1e6
    avg = wtce / conv
    flows = [-p.price_tested] + [x.cash + x.sale for x in rows]
    return DCFResult(rows=rows, rate=r, sale=sale, value=v, avg_tce=avg, converter=conv,
                     implied_tce=avg - (v - p.price_tested) / conv, irr=irr(flows))


def breakeven_long_run_tce(p: DCFInputs, lo: float = 5000, hi: float = 60000) -> float:
    """Long-run TCE (year 4 on, which also sets the earnings-based sale price) at which the DCF value = the price."""
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if value(replace(p, tce_long_run=mid)).value < p.price_tested else (lo, mid)
    return (lo + hi) / 2


@dataclass
class Scenario:
    name: str
    tce_change: float      # earnings in every year of the hold, change against the base case
    rate: float            # discount rate
    sale_change: float     # sale price at the end, change against the base sale price
    result: DCFResult


def scenarios(p: DCFInputs, curve) -> dict:
    """Bear, base and bull: three levers moved together, as in the M2 workbook (sheet Scenarios).

    Earnings, every year:  bear = the listed owner's three lowest years / long-run TCE - 1;
                           bull = its long-run average / long-run TCE - 1.
    Discount rate:         WACC + / - rate_step.
    Sale price at the end: the base sale price x (1 -/+ M1 range / M1 value at today's age): the M1 curve's
                           one-standard-deviation band. The sale price is not recalculated from the scenario
                           earnings, so the range understates how far the value can move.
    """
    base = value(p, curve)
    band = curve.sd / curve.value(p.ship_age)
    levers = {"bear": (p.tce_history_low / p.tce_long_run - 1, p.wacc + p.rate_step, -band),
              "base": (0.0, p.wacc, 0.0),
              "bull": (p.tce_history_avg / p.tce_long_run - 1, p.wacc - p.rate_step, band)}
    out = {}
    for name, (tc, r, sc) in levers.items():
        res = value(p, curve, rate=r, tce_change=tc, sale=base.sale * (1 + sc)) if name != "base" else base
        out[name] = Scenario(name, tc, r, sc, res)
    return out
