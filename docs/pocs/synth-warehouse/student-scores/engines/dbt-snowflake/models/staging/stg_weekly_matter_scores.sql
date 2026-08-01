-- Weekly matter-scores, staged from the raw feed. matter_score is read as text
-- from the seed (the feed carries one "n/a"), so TRY_CAST surfaces the bad row
-- as NULL instead of failing the load — the planted defect a data-quality skill
-- should catch downstream (see ../../MODEL.md § "Planted defect").
select
    school_id,
    iso_year,
    iso_week,
    try_cast(matter_score as number(5, 2)) as matter_score,
    national_rank
from {{ ref('weekly_matter_scores') }}
