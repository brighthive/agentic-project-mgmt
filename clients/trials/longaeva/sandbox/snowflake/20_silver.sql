-- SILVER layer: canonicalized, time-series-shaped data ready for marts + semantic views.
-- Standardized columns match the textbook standardized-time-series schema.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;

CREATE SCHEMA IF NOT EXISTS SILVER
  COMMENT = 'Cleaned + standardized data, dbt-shaped, ready for marts and semantic views';

USE SCHEMA SILVER;

-- Standardized time-series form: long table, one row per (entity, metric, ts).
-- Generic enough to hold prices, returns, volumes, FX without schema explosion.
CREATE TABLE IF NOT EXISTS stg_security_prices (
    internal_issuer_id  VARCHAR     NOT NULL,    -- joins REF.identifier_map
    instrument_id       VARCHAR     NOT NULL,    -- internal instrument id
    metric_name         VARCHAR     NOT NULL,    -- close_price | adj_close | volume | return_1d | ...
    ts                  DATE        NOT NULL,    -- daily grain
    value               NUMBER(20, 6),
    currency            VARCHAR(3),
    source_system       VARCHAR,
    as_of_time          TIMESTAMP_NTZ,           -- when source produced this value
    quality_flag        VARCHAR,                 -- OK | LATE | IMPUTED | SUSPECT
    CONSTRAINT pk_stg_security_prices PRIMARY KEY (instrument_id, metric_name, ts)
)
COMMENT = 'Canonical daily time-series for security-level metrics (long form)';

CREATE TABLE IF NOT EXISTS stg_holdings_snapshot (
    portfolio_id            VARCHAR     NOT NULL,
    internal_issuer_id      VARCHAR     NOT NULL,
    instrument_id           VARCHAR     NOT NULL,
    as_of_date              DATE        NOT NULL,
    quantity                NUMBER(20, 6),
    market_value_local      NUMBER(20, 6),
    market_value_usd        NUMBER(20, 6),
    currency                VARCHAR(3),
    source_system           VARCHAR,
    as_of_time              TIMESTAMP_NTZ,
    quality_flag            VARCHAR,
    CONSTRAINT pk_stg_holdings_snapshot PRIMARY KEY (portfolio_id, instrument_id, as_of_date)
)
COMMENT = 'Canonical daily portfolio holdings snapshot';

CREATE TABLE IF NOT EXISTS stg_corporate_actions (
    internal_issuer_id  VARCHAR     NOT NULL,
    instrument_id       VARCHAR     NOT NULL,
    action_type         VARCHAR     NOT NULL,
    ex_date             DATE        NOT NULL,
    record_date         DATE,
    pay_date            DATE,
    ratio               NUMBER(18, 6),
    cash_amount         NUMBER(18, 6),
    currency            VARCHAR(3),
    source_system       VARCHAR,
    as_of_time          TIMESTAMP_NTZ,
    quality_flag        VARCHAR,
    CONSTRAINT pk_stg_corporate_actions PRIMARY KEY (instrument_id, action_type, ex_date)
)
COMMENT = 'Canonical corporate actions';
