-- The shared KPI set, one definition for every business unit: sales, litres, bottles, average price per litre,
-- active stores, and margin where cost exists. A company row (business_unit = 'All') uses the same definitions, so
-- business units always add up to the company (tested).
with base as (
    select f.*, d.month_start, d.fiscal_year
    from {{ ref('fct_sales_line') }} f
    join {{ ref('dim_date') }} d on d.date_day = f.ordered_on
),

kpis as (
    select
        coalesce(business_unit, 'All')                                      as business_unit,
        month_start,
        any_value(fiscal_year)                                              as fiscal_year,
        sum(sales_dollars)                                                  as sales_dollars,
        sum(sales_liters)                                                   as sales_liters,
        sum(sales_bottles)                                                  as sales_bottles,
        count(distinct store_no)                                            as active_stores,
        sum(gross_margin_dollars)                                           as gross_margin_dollars,
        sum(case when cost_dollars is not null then sales_dollars end)      as sales_dollars_with_cost
    from base
    group by grouping sets ((business_unit, month_start), (month_start))
)

select
    *,
    round(sales_dollars / nullif(sales_liters, 0), 2)                       as price_per_liter,
    round(gross_margin_dollars / nullif(sales_dollars_with_cost, 0), 4)     as gross_margin_rate,
    round(sales_dollars_with_cost / nullif(sales_dollars, 0), 4)            as cost_coverage
from kpis
