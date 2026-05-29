-- REF layer: Longaeva-style reference data (security master + calendars + codes).
-- These are the join targets the semantic-view scaffolder must auto-detect.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;

CREATE SCHEMA IF NOT EXISTS REF
  COMMENT = 'Reference data: fiscal calendar, identifier mappings, geo + classification codes';

USE SCHEMA REF;

-- Fiscal calendar with non-standard FY alignment (some issuers don't run Jan-Dec).
CREATE TABLE IF NOT EXISTS fiscal_calendar (
    fiscal_period_id    VARCHAR     NOT NULL,    -- e.g. ISSUER_X-FY2026-Q1
    issuer_cohort       VARCHAR     NOT NULL,    -- which fiscal cohort this period belongs to
    fiscal_year         NUMBER(4)   NOT NULL,
    fiscal_quarter      NUMBER(1)   NOT NULL,
    period_start_date   DATE        NOT NULL,
    period_end_date     DATE        NOT NULL,
    is_current          BOOLEAN     DEFAULT FALSE,
    CONSTRAINT pk_fiscal_calendar PRIMARY KEY (fiscal_period_id)
)
COMMENT = 'Fiscal calendar with non-standard FY alignment per issuer cohort';

-- Identifier mapping: industry IDs -> internal issuer ID.
CREATE TABLE IF NOT EXISTS identifier_map (
    internal_issuer_id  VARCHAR     NOT NULL,
    lei                 VARCHAR(20),                    -- ISO 17442
    figi                VARCHAR(12),                    -- OpenFIGI
    cusip               VARCHAR(9),
    isin                VARCHAR(12),
    issuer_name         VARCHAR,
    issuer_cohort       VARCHAR,                        -- joins fiscal_calendar.issuer_cohort
    primary_country     VARCHAR(3),                     -- joins geo_codes.country_code
    primary_sector      VARCHAR,                        -- joins classification_codes
    is_active           BOOLEAN     DEFAULT TRUE,
    effective_from      DATE,
    effective_to        DATE,
    CONSTRAINT pk_identifier_map PRIMARY KEY (internal_issuer_id)
)
COMMENT = 'LEI / FIGI / CUSIP / ISIN -> internal_issuer_id (security master)';

CREATE TABLE IF NOT EXISTS geo_codes (
    country_code        VARCHAR(3)  NOT NULL,           -- ISO 3166-1 alpha-3
    country_name        VARCHAR     NOT NULL,
    region              VARCHAR,                        -- AMERICAS / EMEA / APAC
    sub_region          VARCHAR,
    longaeva_grouping   VARCHAR,                        -- internal grouping
    CONSTRAINT pk_geo_codes PRIMARY KEY (country_code)
)
COMMENT = 'ISO country codes + Longaeva regional groupings';

CREATE TABLE IF NOT EXISTS classification_codes (
    classification_id   VARCHAR     NOT NULL,
    classification_type VARCHAR     NOT NULL,           -- SECTOR | INDUSTRY | ASSET_CLASS
    code                VARCHAR     NOT NULL,
    label               VARCHAR     NOT NULL,
    parent_id           VARCHAR,                        -- self-ref for hierarchy
    CONSTRAINT pk_classification_codes PRIMARY KEY (classification_id)
)
COMMENT = 'Sector / industry / asset-class classification hierarchy';
