-- One row per distinct sales line, with conformed keys: the store version valid on the order date (point in time),
-- item, conformed category and business unit, vendor. Margin exists only where the state published cost and retail
-- price (none in 2023-2024, 58% of 2025 lines).
select
    s.sales_line_id,
    s.invoice_id,
    s.ordered_on,
    d.store_sk,
    s.store_no,
    s.item_no,
    m.conformed_category_code                                               as category_code,
    m.business_unit,
    s.vendor_number,
    s.sales_bottles,
    s.sales_liters,
    s.sales_gallons,
    s.sales_dollars,
    s.state_bottle_cost * s.sales_bottles                                   as cost_dollars,
    case when s.state_bottle_cost is not null
         then s.sales_dollars - s.state_bottle_cost * s.sales_bottles end   as gross_margin_dollars
from {{ ref('stg_iowa__sales_lines') }} s
join {{ ref('category_business_unit') }} m using (category_code)
join {{ ref('dim_store') }} d
  on d.store_no = s.store_no
 and s.ordered_on >= d.valid_from
 and (d.valid_to is null or s.ordered_on < d.valid_to)
