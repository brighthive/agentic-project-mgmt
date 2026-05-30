-- Data product: daily regional exposure rollup.
-- Mirrors what an analyst would query from the semantic view's
--   DIMENSIONS region METRICS total_exposure_usd
-- but persists it as a table so downstream compute jobs can timeseries-scan it.

{{ config(materialized='table') }}

select
    as_of_date,
    region,
    longaeva_grouping,
    sum(market_value_usd)              as total_exposure_usd,
    avg(market_value_usd)              as avg_exposure_per_position_usd,
    count(distinct internal_issuer_id) as distinct_issuers,
    count(distinct portfolio_id)       as distinct_portfolios,
    count(*)                           as position_count
from {{ ref('int_enriched_holdings') }}
where region is not null
group by 1, 2, 3
