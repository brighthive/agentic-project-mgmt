-- Mirrors baseline_expectations.author_supplied.distinct_issuers_minimum_30
-- A healthy portfolio holds at least 30 distinct issuers per day.
select as_of_date, count(distinct internal_issuer_id) as n_issuers
from {{ ref('int_enriched_holdings') }}
group by 1
having n_issuers < {{ var('min_distinct_issuers_per_day') }}
