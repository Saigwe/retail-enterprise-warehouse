"""Checks on a finished run (RETAIL_DB): the Power BI export matches the warehouse KPIs, holidays land in the right
weeks, and the forecast backtest produced sane results."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "forecasting"))
from backtest import holiday_week  # noqa: E402

DB = os.environ.get("RETAIL_DB", str(ROOT / "warehouse" / "retail.duckdb"))
PBI = ROOT / "powerbi" / "data"


def test_power_bi_export_matches_the_warehouse_kpis():
    con = duckdb.connect(DB, read_only=True)
    wh = con.execute("""select sum(sales_dollars), sum(sales_liters), sum(sales_bottles)
                        from gold.rpt_bu_monthly where business_unit = 'All'""").fetchone()
    pbi = con.execute(f"""select sum(sales_dollars), sum(sales_liters), sum(sales_bottles)
                          from read_parquet('{(PBI / 'fct_sales_daily.parquet').as_posix()}')""").fetchone()
    assert pbi == pytest.approx(wh, rel=1e-9)


def test_every_category_in_the_export_has_a_business_unit():
    con = duckdb.connect(DB, read_only=True)
    orphans = con.execute(f"""select count(*) from read_parquet('{(PBI / 'fct_sales_daily.parquet').as_posix()}') f
                              anti join read_parquet('{(PBI / 'dim_category.parquet').as_posix()}') c using (category_code)""").fetchone()[0]
    assert orphans == 0


def test_holiday_weeks():
    weeks = pd.Series(pd.to_datetime(["2025-11-24", "2025-12-22", "2025-12-29", "2025-07-07", "2025-06-30"]))
    assert holiday_week(weeks).tolist() == [1, 1, 1, 0, 1]   # Thanksgiving, Christmas, New Year's Eve, -, July 4


def test_forecast_backtest_is_sane():
    r = json.loads((ROOT / "results" / "forecast_backtest.json").read_text())
    assert r["test_weeks"] >= 50 and r["horizon_weeks"] == 4
    assert r["wape"]["lgbm"]["business unit (pooled)"] < 0.3
