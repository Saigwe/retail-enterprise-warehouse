PY ?= python
DB ?= warehouse/retail.duckdb
DBT_BIN ?= dbt
DBT = cd dbt && DUCKDB_PATH=../$(DB) $(DBT_BIN)
HUB = https://data.iowa.gov/api/dataset-download?path=datasets%2F

.PHONY: all download load dbt forecast powerbi-data test clean

all: download load dbt forecast powerbi-data test   ## real Iowa sales 2023-2025 -> conformed warehouse -> forecast -> Power BI data -> tests

download:   ## about 2 GB of zipped CSV from the Iowa Data Hub (datasets 1260-1262, CC BY); skipped when present
	mkdir -p data/raw
	for y in 2023:1260 2024:1261 2025:1262; do f=data/raw/liquor_$${y%%:*}.zip; \
	  [ -s $$f ] || curl -sL -o $$f "$(HUB)$${y##*:}%2Frows.csv"; done

load:
	$(PY) ingestion/load.py --raw data/raw --parquet data/parquet --db $(DB)

dbt:
	$(DBT) deps --profiles-dir .
	$(DBT) build --profiles-dir .

forecast:   ## weekly demand by business unit, 4 weeks ahead, backtested on 2025
	$(PY) forecasting/backtest.py --db $(DB) --out results

powerbi-data:   ## Parquet for the Power BI semantic model
	$(PY) powerbi/export_powerbi_data.py --db $(DB) --out powerbi/data

test:
	RETAIL_DB=$(DB) $(PY) -m pytest -q tests

clean:
	rm -rf warehouse data/parquet powerbi/data dbt/target dbt/logs dbt/dbt_packages
