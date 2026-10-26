-- Conformed date dimension, including Iowa's July-June fiscal year and the ISO week used by forecasting.
with days as (
    select cast(d as date) as date_day
    from range(date '2023-01-01', date '2026-01-01', interval 1 day) t(d)
)

select
    date_day,
    year(date_day)                                                          as calendar_year,
    month(date_day)                                                         as month_no,
    date_trunc('month', date_day)                                           as month_start,
    date_trunc('week', date_day)                                            as week_start,
    isodow(date_day)                                                        as iso_weekday,
    case when month(date_day) >= {{ var('fiscal_year_start_month') }}
         then year(date_day) + 1 else year(date_day) end                    as fiscal_year
from days
