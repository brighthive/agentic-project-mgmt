-- Staging model for the inbound Data Share security master.
-- Canonicalizes vendor column names to Longaeva conventions and casts types.
--
-- Vendor -> canonical:
--   vendor_security_id  -> external_security_id
--   primary_country     -> country_code
--   last_updated        -> source_updated_at

{{ config(materialized='view') }}

select
    vendor_security_id                          as external_security_id,
    lei,
    figi,
    cusip,
    isin,
    issuer_name,
    primary_country                             as country_code,
    primary_exchange                            as exchange_code,
    asset_class_code,
    sector_code,
    coalesce(is_active, false)                  as is_active,
    last_updated                                as source_updated_at
from {{ source('vendor_share', 'vendor_security_master') }}
where is_active = true
