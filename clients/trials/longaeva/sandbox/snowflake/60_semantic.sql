-- SEMANTIC layer: Snowflake Semantic Views.
-- DDL only — no data; compile success is the gate.
-- Snowflake-native syntax: TABLES -> RELATIONSHIPS -> FACTS -> DIMENSIONS -> METRICS.
-- Each entry follows `alias AS expression` order (NOT expression AS alias).
--
-- Companion YAML at sandbox/semantic/sv_daily_portfolio_exposure.yaml carries the
-- Longaeva-extended fields (filter_presets, agent_instructions, verified_query_examples)
-- that Snowflake-native CREATE SEMANTIC VIEW does not support directly.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;

CREATE SCHEMA IF NOT EXISTS SEMANTIC
  COMMENT = 'Snowflake Semantic Views over GOLD; consumed by analytics + MCP';

USE SCHEMA SEMANTIC;

CREATE OR REPLACE SEMANTIC VIEW sv_daily_portfolio_exposure
  TABLES (
    exposure   AS LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure
                 PRIMARY KEY (as_of_date, portfolio_id, instrument_id),
    issuer     AS LONGAEVA_POC.REF.identifier_map
                 PRIMARY KEY (internal_issuer_id),
    geo        AS LONGAEVA_POC.REF.geo_codes
                 PRIMARY KEY (country_code),
    fiscal     AS LONGAEVA_POC.REF.fiscal_calendar
                 PRIMARY KEY (fiscal_period_id)
  )
  RELATIONSHIPS (
    exposure (internal_issuer_id) REFERENCES issuer,
    exposure (country_code)        REFERENCES geo,
    exposure (fiscal_period_id)    REFERENCES fiscal
  )
  FACTS (
    exposure.exposure_amount_usd   AS exposure_amount_usd,
    exposure.position_count        AS position_count,
    exposure.weight_pct            AS weight_pct
  )
  DIMENSIONS (
    exposure.portfolio_id          AS portfolio_id,
    exposure.internal_issuer_id    AS internal_issuer_id,
    exposure.instrument_id         AS instrument_id,
    exposure.sector_code           AS sector_code,
    exposure.asset_class_code      AS asset_class_code,
    exposure.as_of_date            AS as_of_date,
    issuer.issuer_name             AS issuer_name,
    issuer.lei                     AS lei,
    issuer.figi                    AS figi,
    geo.country                    AS country_name,
    geo.region                     AS region,
    fiscal.fiscal_year             AS fiscal_year,
    fiscal.fiscal_quarter          AS fiscal_quarter
  )
  METRICS (
    exposure.total_exposure_usd               AS SUM(exposure.exposure_amount_usd),
    exposure.avg_exposure_per_position_usd    AS AVG(exposure.exposure_amount_usd),
    exposure.position_count_distinct_issuers  AS COUNT(DISTINCT exposure.internal_issuer_id),
    exposure.avg_weight_pct                   AS AVG(exposure.weight_pct)
  )
  COMMENT = 'Daily portfolio exposure by issuer / geo / sector / fiscal period';
