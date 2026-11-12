"""Leave-one-out back-test: value each sale with a curve fitted without it."""
from dataclasses import dataclass

import numpy as np

from vessel_valuation.models.age_curve import fit_age_curve


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


def leave_one_out(ages, prices) -> BacktestResult:
    x = np.asarray(ages, float)
    p = np.asarray(prices, float)
    pred = np.empty_like(p)
    for i in range(p.size):
        keep = np.arange(p.size) != i
        pred[i] = fit_age_curve(x[keep], p[keep]).value(x[i])
    return BacktestResult(errors=pred / p - 1, predicted=pred)
