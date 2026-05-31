-- Data product: per-fiscal-quarter exposure trend.
-- Joins the holdings to fiscal_calendar so non-Jan-Dec issuers roll up correctly.

{{ config(materialized='table') }}

select
    fiscal_year,
    fiscal_quarter,
    issuer_cohort,
    region,
    sector_code,
    sum(market_value_usd)              as total_exposure_usd,
    avg(market_value_usd)              as avg_exposure_per_position_usd,
    count(distinct internal_issuer_id) as distinct_issuers,
    count(distinct as_of_date)         as days_in_period
from {{ ref('int_enriched_holdings') }}
where fiscal_period_id is not null
group by 1, 2, 3, 4, 5
