-- Source Type 3 simulation: a second database stands in for an inbound Snowflake Data Share.
-- Real shares require provider-side configuration; cross-DB grant gives the same query shape.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_VENDOR_SHARE_SIM;

CREATE SCHEMA IF NOT EXISTS SHARED
  COMMENT = 'Read-only-ish stand-in for an inbound Snowflake Data Share';

USE SCHEMA SHARED;

CREATE TABLE IF NOT EXISTS vendor_security_master (
    vendor_security_id  VARCHAR     NOT NULL,
    lei                 VARCHAR(20),
    figi                VARCHAR(12),
    cusip               VARCHAR(9),
    isin                VARCHAR(12),
    issuer_name         VARCHAR,
    primary_country     VARCHAR(3),
    primary_exchange    VARCHAR,
    asset_class_code    VARCHAR,
    sector_code         VARCHAR,
    is_active           BOOLEAN,
    last_updated        TIMESTAMP_NTZ,
    CONSTRAINT pk_vendor_security_master PRIMARY KEY (vendor_security_id)
)
COMMENT = 'Vendor-managed security master (Data Share simulation)';

CREATE TABLE IF NOT EXISTS vendor_ratings (
    vendor_security_id  VARCHAR     NOT NULL,
    rating_agency       VARCHAR     NOT NULL,
    rating_date         DATE        NOT NULL,
    rating_value        VARCHAR,
    rating_outlook      VARCHAR,
    last_updated        TIMESTAMP_NTZ,
    CONSTRAINT pk_vendor_ratings PRIMARY KEY (vendor_security_id, rating_agency, rating_date)
)
COMMENT = 'Vendor-issued credit ratings (Data Share simulation)';

-- Note: LONGAEVA_POC_ROLE owns this DB so SELECT is implicit.
-- In real life Longaeva would have a separate share role; downstream models behave the same.
