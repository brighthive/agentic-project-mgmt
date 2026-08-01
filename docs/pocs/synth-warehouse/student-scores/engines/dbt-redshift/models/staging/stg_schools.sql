-- Schools dimension, straight from the seeded raw feed. Types already pinned in
-- dbt_project.yml seed config; this view just names the contract columns.
select
    school_id,
    school_name,
    state,
    city,
    enrollment
from {{ ref('schools') }}
