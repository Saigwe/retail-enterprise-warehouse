-- Conformed store dimension, SCD Type 2. valid_from is the day a version was first seen (the first version also covers
-- any earlier date); valid_to is the next version's first day (exclusive), null for the current version.
with v as (
    select
        *,
        lead(first_seen) over (partition by store_no order by version) as next_first_seen
    from {{ ref('int_store_versions') }}
)

select
    md5(store_no || '-' || cast(version as varchar))           as store_sk,
    store_no,
    version,
    case when version = 1 then date '1900-01-01' else first_seen end as valid_from,
    next_first_seen                                             as valid_to,
    next_first_seen is null                                     as is_current,
    split_part(attrs, '|', 1)                                   as store_name,
    split_part(attrs, '|', 2)                                   as store_address,
    split_part(attrs, '|', 3)                                   as store_city,
    split_part(attrs, '|', 4)                                   as store_zip_code,
    split_part(attrs, '|', 5)                                   as county_fips_code,
    split_part(attrs, '|', 6)                                   as county_name,
    first_seen,
    last_seen
from v
