{{ config(materialized="table") }}
-- REAL: one row per distinct sales line. The published file repeats whole months (every field identical, 17% of rows
-- over 2023-2025); those copies are dropped here, and rpt_data_quality counts them. Licensee purchases from the state
-- (the wholesale tier): ordered_on is the order date.
with distinct_lines as (
    select distinct * exclude (year) from {{ source('bronze', 'liquor_sales') }}
)

select
    md5(concat_ws('|', invoice_id, ordered_on, store_no, store_name, store_address, store_city, store_zip_code,
                  county_fips_code, county_name, category_code, category_name, vendor_number, vendor_name, item_no,
                  im_desc, pack, bottle_volume_ml, state_bottle_cost, state_bottle_retail, sales_bottles,
                  sales_dollars, sales_liters, sales_gallons))      as sales_line_id,
    invoice_id,
    ordered_on,
    store_no,
    upper(trim(store_name))                                         as store_name,
    upper(regexp_replace(trim(store_address), '\s+', ' ', 'g'))     as store_address,
    upper(trim(store_city))                                         as store_city,
    left(trim(store_zip_code), 5)                                   as store_zip_code,
    county_fips_code,
    upper(trim(county_name))                                        as county_name,
    category_code,
    vendor_number,
    upper(regexp_replace(trim(vendor_name), '\s+', ' ', 'g'))       as vendor_name,
    item_no,
    trim(im_desc)                                                   as item_description,
    pack,
    bottle_volume_ml,
    state_bottle_cost,
    state_bottle_retail,
    sales_bottles,
    sales_dollars,
    sales_liters,
    sales_gallons
from distinct_lines
