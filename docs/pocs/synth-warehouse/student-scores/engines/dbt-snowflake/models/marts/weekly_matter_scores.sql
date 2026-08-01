-- Canonical weekly matter-scores fact (../../MODEL.md). National weekly score
-- per school; roll up to state in reporting. Materialized as a table.
select
    school_id,
    iso_year,
    iso_week,
    matter_score,
    national_rank
from {{ ref('stg_weekly_matter_scores') }}
