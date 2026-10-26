"""Weekly demand forecast by business unit, four weeks ahead, backtested on every week of 2025.

Series: weekly sales dollars per business unit x county (5 x 99), summed bottom-up to business units and the state.
Horizon: 4 weeks (what a replenishment plan needs), so every feature is at least 4 weeks old at forecast time.
Methods, all scored on the same weeks:
  seasonal_naive   the same week last year
  recent_mean      the mean of weeks t-4 .. t-7
  lgbm             one LightGBM model across all series: lags 4-8 and 52, rolling means, week of year, holiday
                   weeks, business unit and county; refit at the start of every month on everything known by then
  lgbm_raw_file    the same model trained on the raw published file, duplicated months included, scored on the
                   clean actuals: what forecasting on unconformed data would have cost
Metric: WAPE (sum of absolute errors / sum of actuals), per business unit and in total.

Usage: python forecasting/backtest.py --db warehouse/retail.duckdb --out results
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd

HORIZON = 4
SEED = 7


def weekly(con: duckdb.DuckDBPyConnection, raw: bool) -> pd.DataFrame:
    if raw:  # the published file as is, mapped to the same business units and counties
        sql = """select date_trunc('week', r.ordered_on) as week, m.business_unit, upper(trim(r.county_name)) as county,
                        sum(r.sales_dollars) as y
                 from bronze.liquor_sales r join silver.category_business_unit m using (category_code)
                 group by all"""
    else:
        sql = """select date_trunc('week', f.ordered_on) as week, f.business_unit, s.county_name as county,
                        sum(f.sales_dollars) as y
                 from gold.fct_sales_line f join gold.dim_store s using (store_sk)
                 group by all"""
    df = con.execute(sql).df()
    df["county"] = df.county.fillna("UNKNOWN").replace("", "UNKNOWN")
    df = df.groupby(["week", "business_unit", "county"], as_index=False).y.sum()
    weeks = pd.date_range(df.week.min(), "2025-12-22", freq="W-MON")  # drop the partial last week (29-31 Dec)
    keys = df[["business_unit", "county"]].drop_duplicates()
    grid = keys.merge(pd.DataFrame({"week": weeks}), how="cross")
    return grid.merge(df, on=["week", "business_unit", "county"], how="left").fillna({"y": 0.0})


def holiday_week(weeks: pd.Series) -> pd.Series:
    flags = pd.Series(0, index=weeks.index)
    for year in (2023, 2024, 2025):
        nov = pd.date_range(f"{year}-11-01", f"{year}-11-30")
        thanksgiving = nov[nov.weekday == 3][3]
        memorial = pd.date_range(f"{year}-05-01", f"{year}-05-31")
        memorial = memorial[memorial.weekday == 0][-1]
        labor = pd.date_range(f"{year}-09-01", f"{year}-09-07")
        labor = labor[labor.weekday == 0][0]
        for day in (thanksgiving, pd.Timestamp(f"{year}-12-25"), pd.Timestamp(f"{year}-12-31"),
                    pd.Timestamp(f"{year}-07-04"), memorial, labor):
            flags[weeks == day - pd.Timedelta(days=day.weekday())] = 1
    return flags


def features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["business_unit", "county", "week"]).copy()
    g = df.groupby(["business_unit", "county"]).y
    for lag in (4, 5, 6, 7, 8, 52):
        df[f"lag_{lag}"] = g.shift(lag)
    df["mean_4_7"] = df[["lag_4", "lag_5", "lag_6", "lag_7"]].mean(axis=1)
    df["mean_4_16"] = g.transform(lambda s: s.shift(HORIZON).rolling(13, min_periods=4).mean())
    df["woy"] = df.week.dt.isocalendar().week.astype(int)
    df["holiday"] = holiday_week(df.week)
    df["bu"] = df.business_unit.astype("category")
    df["county_cat"] = df.county.astype("category")
    return df


FEATS = ["lag_4", "lag_5", "lag_6", "lag_7", "lag_8", "lag_52", "mean_4_7", "mean_4_16", "woy", "holiday", "bu", "county_cat"]


def lgbm_forecast(train_df: pd.DataFrame, target_weeks: list, clean: pd.DataFrame) -> pd.Series:
    preds = []
    months = sorted({w.to_period("M") for w in target_weeks})
    for m in months:
        cutoff = m.start_time - pd.Timedelta(weeks=HORIZON - 1)  # data known at the start of the month, 4 weeks ahead
        tr = train_df[(train_df.week < cutoff) & train_df.lag_52.notna()]
        model = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=63, min_child_samples=20,
                                  objective="tweedie", random_state=SEED, verbose=-1)
        model.fit(tr[FEATS], tr.y.clip(lower=0))  # returns can make a county-week negative; tweedie needs >= 0
        te = clean[clean.week.dt.to_period("M") == m]
        preds.append(pd.Series(np.clip(model.predict(te[FEATS]), 0, None), index=te.index))
    return pd.concat(preds)


def wape(actual: pd.Series, pred: pd.Series) -> float:
    return float((actual - pred).abs().sum() / actual.sum())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/retail.duckdb")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    clean = features(weekly(con, raw=False))
    raw = features(weekly(con, raw=True))
    test_mask = clean.week >= "2025-01-01"
    test_weeks = sorted(clean.loc[test_mask, "week"].unique())
    test = clean[test_mask].copy()
    test["seasonal_naive"] = test.lag_52
    test["recent_mean"] = test.mean_4_7
    test["lgbm"] = lgbm_forecast(clean, test_weeks, clean)
    # the raw-file model sees the raw features (what a forecaster on unconformed data would have had), and is scored
    # on the clean actuals
    raw_test = raw[raw.week >= "2025-01-01"]
    raw_pred = lgbm_forecast(raw, test_weeks, raw_test)
    keys = ["week", "business_unit", "county"]
    test = test.merge(raw_test[keys].assign(lgbm_raw_file=raw_pred), on=keys, how="left").fillna({"lgbm_raw_file": 0.0})

    methods = ["seasonal_naive", "recent_mean", "lgbm", "lgbm_raw_file"]
    bu = test.groupby(["week", "business_unit"])[["y", *methods]].sum().reset_index()
    state = test.groupby("week")[["y", *methods]].sum().reset_index()
    rows = []
    for m in methods:
        rows.append({"method": m, "level": "state", "wape": round(wape(state.y, state[m]), 4)})
        rows.append({"method": m, "level": "business unit (pooled)", "wape": round(wape(bu.y, bu[m]), 4)})
        for b, d in bu.groupby("business_unit"):
            rows.append({"method": m, "level": b, "wape": round(wape(d.y, d[m]), 4)})
    res = pd.DataFrame(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.out / "forecast_backtest.csv", index=False)
    bu.round(2).to_csv(args.out / "forecast_bu_weekly_2025.csv", index=False)
    summary = {"test_weeks": len(test_weeks), "series": int(test.groupby(["business_unit", "county"]).ngroups),
               "horizon_weeks": HORIZON,
               "wape": res.pivot(index="level", columns="method", values="wape").to_dict()}
    (args.out / "forecast_backtest.json").write_text(json.dumps(summary, indent=2))
    print(res.pivot(index="level", columns="method", values="wape").to_string())


if __name__ == "__main__":
    main()
