# 3-minute walkthrough: Retail Enterprise Warehouse

A timed script for a Loom recording of about 3 minutes (screen plus camera bubble, 1080p). Say it in your own words; the lines are a guide, not a teleprompter.

**Open these tabs before you press record:** README, the architecture diagram, the "Conformance" table, `dbt/models/marts/rpt_bu_monthly.sql`, the marts YAML (reconciliation and SCD2 tests), `powerbi/RetailWarehouse.SemanticModel` (a role file), `docs/design_doc.md`.

| Time | On screen | What to say |
|---|---|---|
| 0:00–0:20 | Portfolio card, then the README title | Every business unit counts sales its own way, master data drifts, and nobody can say whether the warehouse matches the books. This is three years of real Iowa spirits sales, 9.3 million published lines, conformed into one Kimball warehouse. |
| 0:20–0:40 | README intro | As Lead Data Analytics Engineer at a consumer-audio company I owned the analytics engineering layer across five global business units, with shared KPI definitions and access controls. This rebuilds that on public data. No employer data is used. |
| 0:40–1:10 | Conformance table | The biggest problem: whole months were published twice. That's 1.59 million duplicate rows and $280.7M of sales that never happened. The raw file is 23% over the regulator's total. Deduplicated, the warehouse is within 0.12%, and a dbt test holds it to 1%. |
| 1:10–1:30 | Conformance rows for stores and invoices | Invoice ids are documented as unique but reused on 35,988 invoices, so a content hash is the line key. 164 stores were renamed or moved; they're SCD2, and every sale joins the version valid on its order date, by test. |
| 1:30–1:55 | `rpt_bu_monthly.sql` and the bus matrix | One model defines every KPI for each business unit and for the company, so definitions can't drift, and a test requires the units to add up to the company every month. Margin is about 34% everywhere, a fixed state markup, so it's pricing policy, not a unit lever. |
| 1:55–2:25 | Forecast table | A global LightGBM model forecasts four weeks ahead: 10.1% error across business units in 2025, ahead of same-week-last-year at 10.9%. It loses on gift-pack-driven Gin and Brandy, and I show that. The real lesson: trained on the raw file, the same model misses by 44%. |
| 2:25–2:45 | The Power BI role file | Power BI is in git as TMDL: ten DAX measures matching the warehouse, and row-level security with one role per business unit. I haven't opened it in Power BI Desktop yet, and the README says so. |
| 2:45–3:00 | `docs/design_doc.md` options table, then the README top | The decision I'd defend: dedupe on the full row, not the invoice id, because that's what matches the regulator. For a retailer, the KPIs add up and match the books, and the forecast is trained on data that's right. Links are under the video. |

## Recording checklist
- Close email, chat and notifications. Zoom the browser to 125% so code is readable.
- The full run needs about 3 GB of disk; record from the README and CI output rather than running it live.
- Keep to one take per section; Loom lets you trim. Aim for 2:45 to 3:10.
- Show real numbers on screen as you say them; never estimate on camera.
- If you have opened the model in Power BI Desktop by the time you record, show the report instead of the role file and update the line.

## After recording
1. Copy the Loom share link.
2. In `README.md`, replace the roadmap line with `- [x] [3-minute Loom walkthrough](<your Loom link>)` and add the link under the title.
3. Add the link to this project's card on saigwe.github.io.
