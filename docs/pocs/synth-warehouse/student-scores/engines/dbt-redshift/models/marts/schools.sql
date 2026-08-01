-- Canonical schools dimension (../../MODEL.md). Materialized as a table.
select
    school_id,
    school_name,
    state,
    city,
    enrollment
from {{ ref('stg_schools') }}
