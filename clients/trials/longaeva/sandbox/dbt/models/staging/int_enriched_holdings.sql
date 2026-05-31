-- Intermediate SILVER model: holdings enriched with issuer + geo + fiscal context.
-- Becomes the canonical join layer that GOLD marts (and the semantic view) read.
--
-- Materializes into LONGAEVA_POC.SILVER.int_enriched_holdings.

{{ config(materialized='table') }}

with holdings as (
    select * from {{ source('silver_seeded', 'stg_holdings_snapshot') }}
),

issuer as (
    select
        internal_issuer_id,
        lei,
        figi,
        cusip,
        isin,
        issuer_name,
        issuer_cohort,
        primary_country  as country_code,
        primary_sector   as sector_code
    from {{ source('ref', 'identifier_map') }}
    where is_active = true
),

geo as (
    select
        country_code,
        country_name,
        region,
        sub_region,
        longaeva_grouping
    from {{ source('ref', 'geo_codes') }}
),

fiscal as (
    select
        fiscal_period_id,
        issuer_cohort,
        fiscal_year,
        fiscal_quarter,
        period_start_date,
        period_end_date
    from {{ source('ref', 'fiscal_calendar') }}
)

select
    h.portfolio_id,
    h.internal_issuer_id,
    h.instrument_id,
    h.as_of_date,
    h.quantity,
    h.market_value_usd,
    h.currency,

    -- Issuer
    i.lei,
    i.figi,
    i.issuer_name,
    i.issuer_cohort,
    i.country_code,
    i.sector_code,

    -- Geo
    g.country_name,
    g.region,
    g.longaeva_grouping,

    -- Fiscal
    f.fiscal_period_id,
    f.fiscal_year,
    f.fiscal_quarter,

    -- Lineage
    h.source_system,
    h.as_of_time,
    h.quality_flag

from holdings h
left join issuer i  on i.internal_issuer_id = h.internal_issuer_id
left join geo g     on g.country_code      = i.country_code
left join fiscal f  on f.issuer_cohort     = i.issuer_cohort
                   and h.as_of_date between f.period_start_date and f.period_end_date
