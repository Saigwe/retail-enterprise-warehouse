-- Conformed category dimension with the business unit each category belongs to. Four legacy parent codes, used a
-- few dozen times until early 2024, roll into their current codes; singular/plural name variants take the canonical
-- name. The mapping lives in a reviewed seed (category_business_unit.csv), not in SQL.
select distinct
    conformed_category_code      as category_code,
    conformed_category_name      as category_name,
    business_unit
from {{ ref('category_business_unit') }}
