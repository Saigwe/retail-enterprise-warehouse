"""Load REAL Iowa liquor sales (Iowa Department of Revenue, via the Iowa Data Hub, CC BY) into Parquet and DuckDB.

Each yearly download is a zip of CSV parts. Every part is extracted to a temporary folder, typed once by DuckDB, written
to data/parquet/year=YYYY/ and deleted, so the 6 GB of CSV never sits on disk at once. bronze.liquor_sales is a view
over the Parquet files. Re-running a year replaces it (idempotent).

  Iowa Liquor Sales 2023 / 2024 / 2025: data.iowa.gov datasets 1260 / 1261 / 1262
  https://data.iowa.gov/api/dataset-download?path=datasets/<id>/rows.csv

Usage: python ingestion/load.py --raw data/raw --parquet data/parquet --db warehouse/retail.duckdb [--years 2023 2024 2025]
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path

import duckdb

COLUMNS = {
    "invoice_id": "varchar", "ordered_on": "date", "store_no": "varchar", "store_name": "varchar",
    "store_address": "varchar", "store_city": "varchar", "store_zip_code": "varchar", "county_fips_code": "varchar",
    "county_name": "varchar", "category_code": "varchar", "category_name": "varchar", "vendor_number": "varchar",
    "vendor_name": "varchar", "item_no": "varchar", "im_desc": "varchar", "pack": "integer",
    "bottle_volume_ml": "integer", "state_bottle_cost": "decimal(12,2)", "state_bottle_retail": "decimal(12,2)",
    "sales_bottles": "integer", "sales_dollars": "decimal(14,2)", "sales_liters": "decimal(14,2)",
    "sales_gallons": "decimal(14,2)",
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--parquet", type=Path, default=Path("data/parquet"))
    ap.add_argument("--db", default="warehouse/retail.duckdb")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(args.db)
    types = ", ".join(f"'{k}': '{v}'" for k, v in COLUMNS.items())
    for year in args.years:
        out = args.parquet / f"year={year}"
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir(parents=True)
        with zipfile.ZipFile(args.raw / f"liquor_{year}.zip") as z, tempfile.TemporaryDirectory() as tmp:
            for i, member in enumerate(sorted(n for n in z.namelist() if n.endswith(".csv"))):
                csv = Path(z.extract(member, tmp))
                con.execute(f"""copy (select * from read_csv('{csv.as_posix()}', header = true, quote = '"', escape = '"', columns = {{{types}}}))
                                to '{(out / f"part_{i:02d}.parquet").as_posix()}' (format parquet, compression zstd)""")
                csv.unlink()
        n = con.execute(f"select count(*) from read_parquet('{out.as_posix()}/*.parquet')").fetchone()[0]
        print(f"{year}: {n:,} rows -> {out}")
    con.execute("create schema if not exists bronze")
    con.execute(f"""create or replace view bronze.liquor_sales as
                    select * from read_parquet('{args.parquet.resolve().as_posix()}/*/*.parquet', hive_partitioning = true)""")
    print(f"bronze.liquor_sales {con.execute('select count(*) from bronze.liquor_sales').fetchone()[0]:,} rows")


if __name__ == "__main__":
    main()
