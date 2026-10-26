-- Conformed item (product) dimension: the latest description, pack, size, category and vendor for each item number.
select
    item_no,
    arg_max(item_description, ordered_on)                       as item_description,
    arg_max(pack, ordered_on)                                   as pack,
    arg_max(bottle_volume_ml, ordered_on)                       as bottle_volume_ml,
    arg_max(m.conformed_category_code, ordered_on)              as category_code,
    arg_max(vendor_number, ordered_on)                          as vendor_number,
    count(distinct item_description)                            as description_variants
from {{ ref('stg_iowa__sales_lines') }} s
join {{ ref('category_business_unit') }} m using (category_code)
group by item_no
