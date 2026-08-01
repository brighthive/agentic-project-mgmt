-- Monthly matter-scores, staged from the raw feed. Clean feed — types already
-- pinned in the seed config, so this view just names the contract columns.
select
    school_id,
    year,
    month,
    matter_score,
    national_rank
from {{ ref('monthly_matter_scores') }}
