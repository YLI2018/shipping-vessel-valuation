"""M1+ hedonic price model: log price explained by age, size, yard country, survey timing, equipment and market level.

    ln P_i = b0 + sum_k b_k x_ik + e_i       (ordinary least squares; robust HC1 standard errors)

A yes/no feature changes the price by (e^b - 1); for ln(dwt), b is the % change in price for 1% more deadweight.

Model A pools tankers and bulkers (tankers get their own age and size slopes; market level = ship type x quarter).
Model B uses MR tankers only (market level = quarter).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from patsy import dmatrix

FORMULA_A = ("ln_price ~ age + age:tanker + ln_dwt + ln_dwt:tanker + C(yard, Treatment('China')) + survey_due_12m"
             " + survey_unknown + scrubber + eco + en_bloc_sale + C(type_quarter)")
FORMULA_B = "ln_price ~ age + ln_dwt + C(yard, Treatment('China')) + survey_due_12m + scrubber + C(quarter)"


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Add the model columns: ln_price, ln_dwt and the ship type x quarter label."""
    out = df.copy()
    if "price_musd" in out:
        out["ln_price"] = np.log(out["price_musd"])
    out["ln_dwt"] = np.log(out["dwt"])
    out["type_quarter"] = out["type"] + "_" + out["quarter"]
    return out


@dataclass
class HedonicValue:
    value: float      # $m: e^(predicted ln price) x smearing factor
    low: float        # 68% prediction interval, $m
    high: float
    ln_price: float   # predicted ln price
    smearing: float   # Duan smearing factor: average of e^(residual)


def fit(formula: str, data: pd.DataFrame):
    """Ordinary least squares with heteroskedasticity-robust (HC1) standard errors."""
    return smf.ols(formula, data=data).fit(cov_type="HC1")


def solve_by_hand(model) -> np.ndarray:
    """The same coefficients from the normal equations, b = (X'X)^-1 X'y, to show what the library does."""
    X, y = model.model.exog, model.model.endog
    return np.linalg.solve(X.T @ X, X.T @ y)


def terms_for(model, ship: pd.DataFrame) -> pd.DataFrame:
    """The ship's row of the design matrix next to the coefficients: x, b and x*b for every non-zero term."""
    x = np.asarray(dmatrix(model.model.data.design_info, ship, return_type="dataframe"))[0]
    t = pd.DataFrame(dict(term=model.model.exog_names, x=x, b=model.params.values))
    t["xb"] = t["x"] * t["b"]
    return t[t["x"] != 0].reset_index(drop=True)


def value(model, ship: pd.DataFrame) -> HedonicValue:
    """Value a ship: predicted ln price back to dollars with Duan's smearing factor; 68% prediction interval."""
    frame = model.get_prediction(ship).summary_frame(alpha=0.32)
    smear = float(np.mean(np.exp(model.resid)))
    ln_p = float(frame["mean"].iloc[0])
    return HedonicValue(value=np.exp(ln_p) * smear, low=float(np.exp(frame["obs_ci_lower"].iloc[0]) * smear),
                        high=float(np.exp(frame["obs_ci_upper"].iloc[0]) * smear), ln_price=ln_p, smearing=smear)


def effects(model) -> pd.DataFrame:
    """Every coefficient except intercept and market level, with its effect in words and reliability."""
    rows = []
    for term, b in model.params.items():
        if term == "Intercept" or "quarter" in term:
            continue
        p = float(model.pvalues[term])
        rows.append(dict(term=term, b=float(b), se=float(model.bse[term]), p=p,
                         effect=f"{b:+.2f}% per 1% DWT" if "ln_dwt" in term else f"{np.exp(b) - 1:+.1%}",
                         reliable="Yes" if p < 0.05 else ("Weak" if p < 0.10 else "No")))
    return pd.DataFrame(rows)
