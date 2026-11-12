"""Charts for the M1 technical note: the fitted age curve and the leave-one-out back-test."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INK, MUTED, GRID = "#1f2328", "#5b6470", "#e3e6ea"
DOT, BAND, CASE = "#2f5f98", "#dde7f3", "#b4441c"
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})


def _style(ax):
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def age_curve_chart(curve, ages, prices, target_age, known_price, out, target_name="Target Ship 1"):
    """Comparables, fitted curve with a +/- 1 SD band, the target's fitted value and reported price."""
    x = np.linspace(0, 22, 300)
    y = curve.a * np.exp(curve.b * x)
    value = curve.value(target_age)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.fill_between(x, y - curve.sd, y + curve.sd, color=BAND, lw=0, label=r"Fitted value $\pm$ 1 SD")
    ax.plot(x, y, color=INK, lw=1.4, label=rf"Fitted curve $P = {curve.a:.2f}\,e^{{{curve.b:.4f}\,\mathrm{{age}}}}$")
    ax.scatter(ages, prices, s=16, color=DOT, edgecolor="white", linewidth=0.6, zorder=3,
               label=f"Comparable sales, adjusted ($n = {len(ages)}$)")
    ax.scatter([target_age], [value], s=34, marker="D", color=CASE, edgecolor="white", linewidth=0.8, zorder=4,
               label=f"{target_name}: fitted value \\${value:.2f}m")
    if known_price is not None:
        ax.scatter([target_age], [known_price], s=34, facecolor="white", edgecolor=CASE, linewidth=1.2, zorder=4,
                   label=f"{target_name}: reported price \\${known_price:.2f}m")
    ax.set_xlim(0, 22); ax.set_ylim(0, 110)
    ax.set_xlabel("Age at sale (years)"); ax.set_ylabel("Adjusted price (US\\$m)")
    _style(ax)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.tight_layout()
    fig.savefig(Path(out), dpi=200)
    plt.close(fig)


def backtest_chart(ages, backtest, out):
    """Leave-one-out misses by age, with the average miss marked."""
    miss = backtest.errors
    m = backtest.average_miss
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.scatter(ages, miss * 100, s=16, color=DOT, edgecolor="white", linewidth=0.6, zorder=3)
    ax.axhline(m * 100, color=CASE, lw=0.9, ls="--")
    ax.axhline(-m * 100, color=CASE, lw=0.9, ls="--")
    ax.text(21.8, m * 100 + 1.5, f"average miss ±{m:.1%}", ha="right", color=CASE, fontsize=7.5)
    ax.set_xlim(4, 22)
    ax.set_xlabel("Age at sale (years)"); ax.set_ylabel("Miss (%): curve without the sale\n÷ reported price − 1")
    _style(ax)
    fig.tight_layout()
    fig.savefig(Path(out), dpi=200)
    plt.close(fig)
