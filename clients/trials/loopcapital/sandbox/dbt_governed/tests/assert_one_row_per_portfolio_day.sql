-- The grain assertion: one row per portfolio per day.
--
-- This is the test that would actually catch a broken rollup. The not_null tests in
-- schema.yml pass happily while a group-by is wrong — every column is populated, the
-- numbers are just duplicated. A repeated portfolio/date pair is what an aggregation
-- bug looks like from the outside.
--
-- dbt treats any returned row as a failure, so this selects only the violations.
select
    portfolio_id,
    as_of_date,
    count(*) as row_count
from {{ ref('portfolio_exposure_daily') }}
group by portfolio_id, as_of_date
having count(*) > 1
