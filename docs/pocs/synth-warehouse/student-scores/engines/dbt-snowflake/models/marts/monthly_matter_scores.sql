-- Canonical monthly matter-scores fact (../../MODEL.md). National monthly score
-- per school; roll up to state in reporting. Materialized as a table.
select
    school_id,
    year,
    month,
    matter_score,
    national_rank
from {{ ref('stg_monthly_matter_scores') }}
