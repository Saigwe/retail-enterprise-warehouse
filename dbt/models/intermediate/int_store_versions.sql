-- Store history (SCD2 source): a new version starts whenever a store's name, address, city, zip or county changes
-- from one order day to the next. Gaps and islands over the days each store ordered.
with daily as (
    select
        store_no,
        ordered_on,
        arg_max(concat_ws('|', store_name, store_address, store_city, store_zip_code, county_fips_code, county_name),
                sales_dollars)                                                  as attrs
    from {{ ref('stg_iowa__sales_lines') }}
    group by store_no, ordered_on
),

flagged as (
    select *,
           case when attrs is distinct from lag(attrs) over (partition by store_no order by ordered_on) then 1 else 0 end as is_change
    from daily
),

islands as (
    select *, sum(is_change) over (partition by store_no order by ordered_on rows unbounded preceding) as version
    from flagged
)

select
    store_no,
    version,
    min(ordered_on)                                   as first_seen,
    max(ordered_on)                                   as last_seen,
    any_value(attrs)                                  as attrs
from islands
group by store_no, version
