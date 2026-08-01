-- Weekly matter-scores, staged from the raw feed. matter_score is read as text
-- from the seed (the feed carries one "n/a"). Redshift has no TRY_CAST, so a
-- regex-guarded CASE surfaces the bad row as NULL instead of failing the load —
-- the planted defect a data-quality skill should catch downstream (see
-- ../../MODEL.md § "Planted defect"). This is the one dialect divergence from
-- the Snowflake project, which uses TRY_CAST for the same effect.
select
    school_id,
    iso_year,
    iso_week,
    case
        when matter_score ~ '^[0-9]+(\.[0-9]+)?$'
        then matter_score::decimal(5, 2)
    end as matter_score,
    national_rank
from {{ ref('weekly_matter_scores') }}
