"""Read the comparable sales file."""
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED = ("sale", "age", "adjusted_price_musd")


def load_comparables(path):
    """Return (labels, ages, adjusted prices) from a CSV with columns sale, age, adjusted_price_musd.

    Stops with a clear message if a column is missing or a price is not positive.
    """
    df = pd.read_csv(Path(path))
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing column(s) {', '.join(missing)}")
    ages = df["age"].to_numpy(float)
    prices = df["adjusted_price_musd"].to_numpy(float)
    if np.isnan(ages).any() or np.isnan(prices).any():
        raise ValueError(f"{path}: empty age or price")
    if (prices <= 0).any():
        raise ValueError(f"{path}: every adjusted price must be above 0")
    return df["sale"].tolist(), ages, prices
