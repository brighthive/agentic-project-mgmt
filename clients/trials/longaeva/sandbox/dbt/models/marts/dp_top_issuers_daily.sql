-- Data product: daily top-50 issuers by exposure.
-- Materializes the `top_50_issuers` filter preset from the YAML as a real table.

{{ config(materialized='table') }}

with ranked as (
    select
        as_of_date,
        internal_issuer_id,
        issuer_name,
        country_code,
        country_name,
        region,
        sector_code,
        sum(market_value_usd) as issuer_exposure_usd,
        row_number() over (
            partition by as_of_date
            order by sum(market_value_usd) desc
        ) as exposure_rank
    from {{ ref('int_enriched_holdings') }}
    where internal_issuer_id is not null
    group by 1, 2, 3, 4, 5, 6, 7
)

select
    as_of_date,
    exposure_rank,
    internal_issuer_id,
    issuer_name,
    country_code,
    country_name,
    region,
    sector_code,
    issuer_exposure_usd
from ranked
where exposure_rank <= 50
