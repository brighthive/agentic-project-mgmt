-- Mirrors baseline_expectations.author_supplied.exposure_present_every_business_day
-- Every business day in the window must have at least one exposure row.
with bdays as (
    select distinct as_of_date
    from {{ ref('int_enriched_holdings') }}
)
select bd.as_of_date
from bdays bd
left join {{ ref('int_enriched_holdings') }} eh on bd.as_of_date = eh.as_of_date
where dayofweek(bd.as_of_date) between 1 and 5
group by bd.as_of_date
having count(eh.as_of_date) = 0
