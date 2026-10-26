-- Ties the warehouse to the regulator's own published totals (seed regulator_totals.csv, with sources), raw file vs
-- de-duplicated warehouse. The test on this model requires the warehouse to land within 1% of the published figure.
with periods as (
    select * from {{ ref('regulator_totals') }}
),

raw as (
    select p.fiscal_year, sum(r.sales_dollars) as raw_file_sales_dollars
    from periods p
    join {{ source('bronze', 'liquor_sales') }} r on r.ordered_on between p.period_start and p.period_end
    group by p.fiscal_year
),

warehouse as (
    select p.fiscal_year, sum(f.sales_dollars) as warehouse_sales_dollars, sum(f.sales_gallons) as warehouse_gallons
    from periods p
    join {{ ref('fct_sales_line') }} f on f.ordered_on between p.period_start and p.period_end
    group by p.fiscal_year
)

select
    p.fiscal_year,
    p.published_sales_dollars,
    p.published_gallons,
    r.raw_file_sales_dollars,
    w.warehouse_sales_dollars,
    w.warehouse_gallons,
    round(w.warehouse_sales_dollars / p.published_sales_dollars - 1, 4)     as warehouse_vs_published,
    round(r.raw_file_sales_dollars / p.published_sales_dollars - 1, 4)      as raw_file_vs_published,
    round(w.warehouse_gallons / p.published_gallons - 1, 4)                 as gallons_vs_published,
    p.source
from periods p
join raw r using (fiscal_year)
join warehouse w using (fiscal_year)
