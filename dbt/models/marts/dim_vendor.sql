-- Conformed vendor dimension: one row per vendor number with its most recent name, and how many spellings it had.
select
    vendor_number,
    arg_max(vendor_name, ordered_on)            as vendor_name,
    count(distinct vendor_name)                 as name_variants
from {{ ref('stg_iowa__sales_lines') }}
group by vendor_number
