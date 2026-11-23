"""README charts from the committed 2025 forecast backtest (results/forecast_*.csv). Usage: python charts/make_charts.py"""
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib.dates as mdates

import style as st

ROOT = Path(__file__).resolve().parents[1]
RES = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results"
OUT = ROOT / "docs" / "charts"


def read(name):
    with open(RES / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


wk = read("forecast_bu_weekly_2025.csv")
tot = defaultdict(lambda: defaultdict(float))
for r in wk:
    for k in ("y", "lgbm", "seasonal_naive", "lgbm_raw_file"):
        tot[r["week"]][k] += float(r[k])
weeks = sorted(tot)
x = [date.fromisoformat(w) for w in weeks]
f, ax = st.fig(8, 3.6)
ax.plot(x, [tot[w]["y"] for w in weeks], color=st.TEXT, lw=2, label="Actual sales")
ax.plot(x, [tot[w]["lgbm"] for w in weeks], color=st.S[0], lw=2, label="LightGBM, 4 weeks ahead")
ax.plot(x, [tot[w]["lgbm_raw_file"] for w in weeks], color=st.S[1], lw=1.6, ls="--", label="Same model trained on the raw file")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_ylim(0, None)
ax.yaxis.set_major_formatter(st.FuncFormatter(lambda v, _: f"${v / 1e6:.0f}M"))
st.head(ax, "Weekly state sales, 2025: the warehouse forecast tracks; the raw file overshoots",
        "Iowa spirits, all five business units, each week forecast four weeks ahead", legend=True, ncol=3)
st.save(f, OUT / "forecast_2025.png")

bt = read("forecast_backtest.csv")
levels = ["state", "business unit (pooled)", "Agave & Rum", "Gin, Brandy & Other", "Liqueurs & Cordials",
          "Vodka & Neutral Spirits", "Whiskey"]
labels = ["State", "Business units\n(pooled)", "Agave\n& Rum", "Gin, Brandy\n& Other", "Liqueurs", "Vodka", "Whiskey"]
methods = [("lgbm", "LightGBM", st.S[0]), ("seasonal_naive", "Same week last year", st.S[2]),
           ("lgbm_raw_file", "LightGBM on the raw file", st.S[1])]
val = {(r["method"], r["level"]): float(r["wape"]) for r in bt}
f, ax = st.fig(8, 3.6)
w = 0.26
for i, (m, lab, col) in enumerate(methods):
    xs = [j + (i - 1) * w for j in range(len(levels))]
    ax.bar(xs, [val[(m, lv)] for lv in levels], w * 0.9, color=col, label=lab)
ax.set_xticks(range(len(levels)), labels)
st.fmt(ax, "y", "pct")
st.head(ax, "Clean data matters more than the model: 10% error vs 44% on the raw file",
        "Forecast error (WAPE) by level, every week of 2025; lower is better", legend=True, ncol=3)
st.save(f, OUT / "forecast_error.png")
print(f"wrote charts to {OUT}")
