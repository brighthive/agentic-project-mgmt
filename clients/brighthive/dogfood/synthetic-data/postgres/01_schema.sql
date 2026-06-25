-- =============================================================================
-- Local dogfood warehouse — Longaeva schema ported to Postgres (BH-764)
-- =============================================================================
-- Port of clients/trials/longaeva/sandbox/snowflake/{40_ref,30_gold,90_weekly_delta,
-- 80_watchlist}.sql for the local docker Postgres warehouse (bh_warehouse).
--
-- Snowflake -> Postgres porting rules applied:
--   NUMBER(p,s)   -> NUMERIC(p,s)
--   NUMBER(n)     -> NUMERIC(n)  (or INTEGER where it's a count)
--   VARCHAR       -> VARCHAR (unbounded text; Postgres VARCHAR w/o length = text)
--   TIMESTAMP_NTZ -> TIMESTAMP
--   BOOLEAN       -> BOOLEAN
--   inline COMMENT = '...'  -> dropped (Postgres uses COMMENT ON; omitted for brevity)
--   USE ROLE / USE DATABASE / CREATE STAGE / FILE FORMAT  -> dropped (Snowflake-only)
--
-- Schemas mirror the Snowflake layers so the agent's catalog + introspection see
-- the same fully-qualified shapes (gold.mart_daily_portfolio_exposure, etc.).
-- Idempotent: CREATE SCHEMA/TABLE IF NOT EXISTS.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS ref;
CREATE SCHEMA IF NOT EXISTS gold;

-- ── REF layer ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ref.fiscal_calendar (
    fiscal_period_id    VARCHAR     NOT NULL,
    issuer_cohort       VARCHAR     NOT NULL,
    fiscal_year         NUMERIC(4)  NOT NULL,
    fiscal_quarter      NUMERIC(1)  NOT NULL,
    period_start_date   DATE        NOT NULL,
    period_end_date     DATE        NOT NULL,
    is_current          BOOLEAN     DEFAULT FALSE,
    CONSTRAINT pk_fiscal_calendar PRIMARY KEY (fiscal_period_id)
);

CREATE TABLE IF NOT EXISTS ref.identifier_map (
    internal_issuer_id  VARCHAR     NOT NULL,
    lei                 VARCHAR(20),
    figi                VARCHAR(12),
    cusip               VARCHAR(9),
    isin                VARCHAR(12),
    issuer_name         VARCHAR,
    issuer_cohort       VARCHAR,
    primary_country     VARCHAR(3),
    primary_sector      VARCHAR,
    is_active           BOOLEAN     DEFAULT TRUE,
    effective_from      DATE,
    effective_to        DATE,
    CONSTRAINT pk_identifier_map PRIMARY KEY (internal_issuer_id)
);

CREATE TABLE IF NOT EXISTS ref.geo_codes (
    country_code        VARCHAR(3)  NOT NULL,
    country_name        VARCHAR     NOT NULL,
    region              VARCHAR,
    sub_region          VARCHAR,
    longaeva_grouping   VARCHAR,
    CONSTRAINT pk_geo_codes PRIMARY KEY (country_code)
);

CREATE TABLE IF NOT EXISTS ref.classification_codes (
    classification_id   VARCHAR     NOT NULL,
    classification_type VARCHAR     NOT NULL,
    code                VARCHAR     NOT NULL,
    label               VARCHAR     NOT NULL,
    parent_id           VARCHAR,
    CONSTRAINT pk_classification_codes PRIMARY KEY (classification_id)
);

CREATE TABLE IF NOT EXISTS ref.watchlist (
    internal_issuer_id  VARCHAR     NOT NULL,
    issuer_name         VARCHAR     NOT NULL,
    watchlist_reason    VARCHAR     NOT NULL,
    severity            VARCHAR     NOT NULL,   -- critical | elevated | monitor
    added_date          DATE        NOT NULL,
    added_by            VARCHAR     NOT NULL,
    CONSTRAINT pk_watchlist PRIMARY KEY (internal_issuer_id)
);

-- ── GOLD layer ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS gold.mart_daily_portfolio_exposure (
    as_of_date              DATE        NOT NULL,
    portfolio_id            VARCHAR     NOT NULL,
    internal_issuer_id      VARCHAR     NOT NULL,
    instrument_id           VARCHAR     NOT NULL,
    country_code            VARCHAR(3),
    sector_code             VARCHAR,
    asset_class_code        VARCHAR,
    fiscal_period_id        VARCHAR,
    exposure_amount_usd     NUMERIC(20, 6),
    position_count          NUMERIC,
    weight_pct              NUMERIC(10, 6),
    CONSTRAINT pk_mart_dpe PRIMARY KEY (as_of_date, portfolio_id, instrument_id)
);

CREATE TABLE IF NOT EXISTS gold.mart_issuer_risk_summary (
    as_of_date              DATE        NOT NULL,
    internal_issuer_id      VARCHAR     NOT NULL,
    country_code            VARCHAR(3),
    sector_code             VARCHAR,
    asset_class_code        VARCHAR,
    total_exposure_usd      NUMERIC(20, 6),
    var_95_1d               NUMERIC(20, 6),
    avg_credit_rating_num   NUMERIC(5, 2),
    CONSTRAINT pk_mart_irs PRIMARY KEY (as_of_date, internal_issuer_id)
);

CREATE TABLE IF NOT EXISTS gold.mart_weekly_exposure_delta (
    portfolio_id            VARCHAR,
    internal_issuer_id      VARCHAR,
    issuer_name             VARCHAR,
    sector_code             VARCHAR,
    country_code            VARCHAR(3),
    country_name            VARCHAR,
    exposure_today_usd      NUMERIC(32, 6),
    exposure_7d_ago_usd     NUMERIC(32, 6),
    delta_usd               NUMERIC(33, 6),
    delta_pct               NUMERIC(38, 4),
    change_type             VARCHAR(15),     -- increased | decreased | new | exited
    as_of_date              DATE,
    build_ts                TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
