# Design doc: Retail Enterprise Warehouse

| | |
|---|---|
| **Author** | Stanley Igwe |
| **Status** | Built on real data; Power BI model awaiting verification in Power BI Desktop |
| **Last updated** | 26 Oct 2026 |

## 1. Problem and users
- **Users:** five business-unit leads, finance (one company number), the planning team (forecast), BI developers.
- **Questions:** What did each business unit sell, on the same definitions? Does the company total match the books? What will each unit sell in four weeks? Who may see which unit's numbers?

## 2. Requirements
| Type | Requirement |
|---|---|
| Functional | Conformed dimensions; one sales fact; shared KPIs for units and company; regulator reconciliation; data-quality report; 4-week forecast; semantic model with business-unit security |
| Correctness | Units add up to the company; the company is within 1% of the regulator; history joins point in time |
| Scale | 9.3M published lines over 3 years (about 3M a year); design target 10x, still one DuckDB file plus Parquet, or the same dbt project on a cloud warehouse |
| Freshness | Monthly: the publisher releases data monthly; a full rebuild takes about a minute |

## 3. Design
- **Parquet first.** The 6 GB of yearly CSV is typed once into 136 MB of Parquet, part by part, so the CSV never sits on disk at once. Bronze is a view over the Parquet, unchanged, so the published duplicates stay visible for the data-quality report.
- **De-duplicate on full-row identity, and prove it against an outside total.** Exact duplicate rows are dropped in staging. The decision isn't taken on faith: the regulator's published fiscal-year total is the test, and only the de-duplicated warehouse passes it.
- **Business units from the publisher's code hierarchy**, held in a reviewed seed rather than SQL, so a reorganisation is a CSV change.
- **SCD2 stores by gaps and islands** over each store's order days, so a renamed or relocated store keeps its history and sales report the name and county the store had at the time.
- **One KPI model with grouping sets** for units and company, so the company row is the same definitions, not a separate query. A test enforces the sum.
- **Forecast four weeks ahead with features at least four weeks old**, refit monthly, against two baselines, and against the same model trained on the raw file, to quantify what conformance is worth.
- **Power BI as text (TMDL)**, so the semantic model, measures and security roles are reviewed in pull requests like the dbt code.

## 4. Options considered
| Decision | Options | Chosen | Why |
|---|---|---|---|
| Duplicate handling | Keep all / dedupe on invoice_id / dedupe on full row | Full row | invoice_id repeats on genuinely different lines; full-row duplicates match the regulator |
| Category conformance | Name matching / code hierarchy | Code hierarchy + reviewed seed | Names vary in spelling; codes carry the hierarchy |
| Store history | Latest attributes (SCD1) / SCD2 | SCD2 | County and name changes would otherwise rewrite past sales |
| Forecast | Per-series models / one global model | One global LightGBM | 495 sparse series; a global model shares seasonality |
| Row-level security | Database / semantic model | Semantic model roles | Where business users actually read the numbers |

## 5. Risks and next steps
- **Fiscal-year reconciliation uses one published year** (FY2025); the 2022 download returned empty, so FY2023 couldn't be checked. Add years as the regulator publishes them.
- **Margin** exists only where the state published cost; coverage is reported beside every margin figure.
- **Power BI model** not yet opened in Power BI Desktop.
- **Next:** Slim CI on modified models; tell the publisher about the duplicated months.
