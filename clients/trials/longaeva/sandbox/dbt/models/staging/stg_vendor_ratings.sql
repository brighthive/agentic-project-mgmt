-- Staging model for inbound Data Share ratings.
-- Canonicalizes + adds a numeric rating scale for downstream risk rollups.

{{ config(materialized='view') }}

select
    vendor_security_id                          as external_security_id,
    rating_agency,
    rating_date,
    rating_value,
    rating_outlook,
    case rating_value
        when 'AAA' then 1 when 'AA' then 2 when 'A' then 3
        when 'BBB' then 4 when 'BB' then 5 when 'B' then 6
        else 99
    end                                         as rating_numeric,
    last_updated                                as source_updated_at
from {{ source('vendor_share', 'vendor_ratings') }}
