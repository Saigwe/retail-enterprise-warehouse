-- The warehouse must land within 1% of the regulator's published fiscal-year sales. The raw file, with its duplicated
-- months, misses by about 23%, so this test is what proves the de-duplication was right.
select fiscal_year, warehouse_vs_published, raw_file_vs_published
from {{ ref('rpt_regulator_reconciliation') }}
where abs(warehouse_vs_published) > 0.01
