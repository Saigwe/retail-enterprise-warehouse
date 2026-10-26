"""Export the gold star schema to Parquet for the Power BI semantic model in powerbi/RetailWarehouse.SemanticModel.

The sales fact is summarised to day x store version x category (the grain the report needs), which keeps the import
small; dimensions are exported whole. Point the model's DataFolder parameter at the output folder.

Usage: python powerbi/export_powerbi_data.py --db warehouse/retail.duckdb --out powerbi/data
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

EXPORTS = {
    "fct_sales_daily": """select ordered_on as date_day, store_sk, category_code,
                                 sum(sales_dollars) as sales_dollars, sum(sales_liters) as sales_liters,
                                 sum(sales_bottles) as sales_bottles, sum(gross_margin_dollars) as gross_margin_dollars,
                                 sum(case when cost_dollars is not null then sales_dollars end) as sales_dollars_with_cost
                          from gold.fct_sales_line group by all""",
    "dim_store": "select * from gold.dim_store",
    "dim_category": "select * from gold.dim_category",
    "dim_date": "select * from gold.dim_date",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default="warehouse/retail.duckdb")
    ap.add_argument("--out", type=Path, default=Path("powerbi/data"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db, read_only=True)
    for name, sql in EXPORTS.items():
        path = args.out / f"{name}.parquet"
        con.execute(f"copy ({sql}) to '{path.as_posix()}' (format parquet, compression zstd)")
        print(f"{path}  {con.execute(f'select count(*) from read_parquet(?)', [path.as_posix()]).fetchone()[0]:,} rows")


if __name__ == "__main__":
    main()
