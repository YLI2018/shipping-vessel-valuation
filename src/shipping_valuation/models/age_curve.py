"""M1 age curve: an exponential depreciation curve fitted by OLS on log price.

    ln P = c + b * age      =>      P = a * e^(b * age),  a = e^c,  r = e^b

r is the share of value a ship one year older keeps; 1 - r is the value lost per year.
"""
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AgeCurve:
    c: float          # intercept of the straight line in logs
    b: float          # slope: change in log price per year of age
    sd: float         # standard deviation of the dollar residuals (sample, n - 1)
    r_squared: float  # share of the variation in log price that age explains
    n: int            # number of comparables

    @property
    def a(self) -> float:
        """Level of the curve at age 0 (a formula value, not a newbuilding price)."""
        return math.exp(self.c)

    @property
    def r(self) -> float:
        """Yearly factor: share of value kept per extra year of age."""
        return math.exp(self.b)

    @property
    def loss_per_year(self) -> float:
        return 1 - self.r

    def value(self, age: float) -> float:
        """Fitted value at an age."""
        return math.exp(self.c + self.b * age)

    def value_range(self, age: float, k_sd: float = 1.0):
        """(low, high) = fitted value -/+ k standard deviations of the residuals."""
        v = self.value(age)
        return v - k_sd * self.sd, v + k_sd * self.sd


def fit_age_curve(ages, prices) -> AgeCurve:
    """Fit ln(price) = c + b * age by ordinary least squares.

    b = sum((age - mean age) * (ln P - mean ln P)) / sum((age - mean age)^2);  c = mean ln P - b * mean age.
    """
    x = np.asarray(ages, float)
    p = np.asarray(prices, float)
    if x.shape != p.shape or x.size < 3:
        raise ValueError("need at least 3 sales, with one age per price")
    if (p <= 0).any():
        raise ValueError("prices must be above 0")
    if np.ptp(x) == 0:
        raise ValueError("ages must not all be the same")
    y = np.log(p)
    sxx = ((x - x.mean()) ** 2).sum()
    b = ((x - x.mean()) * (y - y.mean())).sum() / sxx
    c = y.mean() - b * x.mean()
    resid_log = y - (c + b * x)
    r2 = 1 - (resid_log ** 2).sum() / ((y - y.mean()) ** 2).sum()
    sd = float((p - np.exp(c + b * x)).std(ddof=1))
    return AgeCurve(c=float(c), b=float(b), sd=sd, r_squared=float(r2), n=int(x.size))
