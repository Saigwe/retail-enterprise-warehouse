-- What conformance fixed, by issue, so the numbers above can be trusted and the publisher told.
with raw as (select * from {{ source('bronze', 'liquor_sales') }}),
staged as (select * from {{ ref('stg_iowa__sales_lines') }})

select 'exact duplicate rows dropped' as issue,
       (select count(*) from raw) - (select count(*) from staged) as affected,
       'rows' as unit,
       'Whole months published twice: Aug-Oct 2023, Oct-Dec 2024, Aug-Oct 2025' as detail
union all
select 'sales overstated by duplicates', round((select sum(sales_dollars) from raw) - (select sum(sales_dollars) from staged), 0),
       'dollars', 'Raw file total minus de-duplicated total, 2023-2025'
union all
select 'invoice ids reused for different lines',
       (select count(*) from (select invoice_id from staged group by 1 having count(*) > 1)), 'invoice ids',
       'invoice_id is documented as unique but repeats on lines with different items or amounts'
union all
select 'category codes conformed (legacy parent codes)',
       (select count(*) from {{ ref('category_business_unit') }} where category_code <> conformed_category_code), 'codes',
       'Parent codes used until early 2024 roll into their current codes'
union all
select 'category codes with more than one name',
       (select count(*) from (select category_code from raw group by 1 having count(distinct category_name) > 1)), 'codes',
       'Singular and plural spellings of the same category'
union all
select 'stores with more than one version',
       (select count(*) from (select store_no from {{ ref('dim_store') }} group by 1 having count(*) > 1)), 'stores',
       'Name, address, city, zip or county changed; kept as SCD2 versions'
union all
select 'vendors with more than one spelling',
       (select count(*) from {{ ref('dim_vendor') }} where name_variants > 1), 'vendors', 'Latest spelling used'
union all
select 'lines without a state cost',
       (select count(*) from staged where state_bottle_cost is null), 'lines',
       'Cost and retail price are blank in 2023-2024 and 42% of 2025, so margin is reported only where cost exists'
