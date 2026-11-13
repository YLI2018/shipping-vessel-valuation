"""Leave-one-out validation within the collected sample: value each sale with a model fitted on all the others.

Training may include sales reported after the omitted one, so this is not a historical forecasting test.
"""
from dataclasses import dataclass

import numpy as np

from shipping_valuation.models.age_curve import fit_age_curve


@dataclass(frozen=True)
class BacktestResult:
    errors: np.ndarray      # e_i = curve without sale i / its price - 1 (positive = curve too high)
    predicted: np.ndarray   # the curve-without-it value for each sale

    @property
    def average_miss(self) -> float:
        """Average absolute error: how far off a single valuation typically is."""
        return float(np.abs(self.errors).mean())

    @property
    def bias(self) -> float:
        """Average signed error: whether the curve leans high (+) or low (-)."""
        return float(self.errors.mean())


def leave_one_out(ages, prices, deals=None) -> BacktestResult:
    """M1: value each sale with a curve fitted on the others.

    deals (optional): a label per sale; sales with the same non-blank label were sold together in one package and are
    held out together, so a sister ship with the same age and price cannot give the answer away.
    """
    x = np.asarray(ages, float)
    p = np.asarray(prices, float)
    g = None if deals is None else np.asarray(["" if (v is None or v != v) else str(v) for v in deals])
    pred = np.empty_like(p)
    for i in range(p.size):
        keep = np.arange(p.size) != i
        if g is not None and g[i]:
            keep &= g != g[i]
        pred[i] = fit_age_curve(x[keep], p[keep]).value(x[i])
    return BacktestResult(errors=pred / p - 1, predicted=pred)


def _predict(formula, train, row, quarter=None):
    """Fit on train; predict one row (optionally at a given quarter's market level); Duan smearing back to dollars."""
    import statsmodels.formula.api as smf

    m = smf.ols(formula, data=train).fit()
    x = row.copy()
    if quarter is not None:
        x["quarter"] = quarter
        x["type_quarter"] = x["type"] + "_" + quarter
    return float(np.exp(m.predict(x).iloc[0]) * np.mean(np.exp(m.resid)))


def leave_one_out_formula(formula, data, test_index, deal_col=None, quarter=None, observed=None):
    """Leave-one-out for a regression formula (used by the hedonic model M1+).

    Each row in test_index is valued by the model re-estimated on the other rows of data.
    deal_col (optional): rows with the same non-blank label in this column are held out together (package deals).
    quarter (optional): predict every test row at this quarter's market level (e.g. the quarter of the valuation date).
    observed (optional): a Series of prices to compare with (default: the row's reported price_musd).
    Returns the misses e_i = predicted / observed - 1. Prices are taken back from log price with Duan's smearing factor.
    """
    errors, preds = [], []
    for idx in test_index:
        out = [idx]
        if deal_col and str(data.at[idx, deal_col]) not in ("", "nan"):
            out = data.index[data[deal_col] == data.at[idx, deal_col]]
        pred = _predict(formula, data.drop(index=out), data.loc[[idx]], quarter)
        obs = data.at[idx, "price_musd"] if observed is None else observed[idx]
        preds.append(pred)
        errors.append(pred / obs - 1)
    return BacktestResult(errors=np.array(errors), predicted=np.array(preds))


def time_ordered_formula(formula, data, test_index, week_col="report_week"):
    """Time-ordered validation for a regression formula: each test row is predicted only from rows reported in
    EARLIER weeks (rows from the same week are excluded, so a package never trains on itself).

    A quarter with no earlier rows cannot be estimated; the row then uses the latest earlier quarter's level
    (for type_quarter models, the latest earlier quarter of the same ship type). This assumption is stated.
    Returns the misses against the reported price.
    """
    errors, preds = [], []
    for idx in test_index:
        row = data.loc[[idx]]
        train = data[data[week_col] < data.at[idx, week_col]]
        q = data.at[idx, "quarter"]
        if "type_quarter" in formula and data.at[idx, "type_quarter"] not in set(train["type_quarter"]):
            q = train.loc[train["type"] == data.at[idx, "type"], "quarter"].max()
        elif "C(quarter)" in formula and q not in set(train["quarter"]):
            q = train["quarter"].max()
        pred = _predict(formula, train, row, q)
        preds.append(pred)
        errors.append(pred / data.at[idx, "price_musd"] - 1)
    return BacktestResult(errors=np.array(errors), predicted=np.array(preds))
