-- GOLD layer: business-ready marts.
-- Two domain marts that the semantic view sits on top of.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;

CREATE SCHEMA IF NOT EXISTS GOLD
  COMMENT = 'Business-ready marts; semantic-view-facing';

USE SCHEMA GOLD;

CREATE TABLE IF NOT EXISTS mart_daily_portfolio_exposure (
    as_of_date              DATE        NOT NULL,
    portfolio_id            VARCHAR     NOT NULL,
    internal_issuer_id      VARCHAR     NOT NULL,
    instrument_id           VARCHAR     NOT NULL,
    -- Dimension keys (denormalized from REF for query speed)
    country_code            VARCHAR(3),
    sector_code             VARCHAR,
    asset_class_code        VARCHAR,
    fiscal_period_id        VARCHAR,    -- joins REF.fiscal_calendar
    -- Facts
    exposure_amount_usd     NUMBER(20, 6),
    position_count          NUMBER,
    weight_pct              NUMBER(10, 6),
    CONSTRAINT pk_mart_dpe PRIMARY KEY (as_of_date, portfolio_id, instrument_id)
)
COMMENT = 'Daily portfolio exposure mart (semantic view foundation)';

CREATE TABLE IF NOT EXISTS mart_issuer_risk_summary (
    as_of_date              DATE        NOT NULL,
    internal_issuer_id      VARCHAR     NOT NULL,
    country_code            VARCHAR(3),
    sector_code             VARCHAR,
    asset_class_code        VARCHAR,
    total_exposure_usd      NUMBER(20, 6),
    var_95_1d               NUMBER(20, 6),
    avg_credit_rating_num   NUMBER(5, 2),
    CONSTRAINT pk_mart_irs PRIMARY KEY (as_of_date, internal_issuer_id)
)
COMMENT = 'Daily issuer-level risk summary';
