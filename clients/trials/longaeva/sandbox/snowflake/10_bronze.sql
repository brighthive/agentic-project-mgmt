-- BRONZE layer: raw vendor landing.
-- Internal stages stand in for real S3 external stages. Same COPY INTO semantics;
-- swap STAGE definition to URL='s3://...' + STORAGE_INTEGRATION later.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;

CREATE SCHEMA IF NOT EXISTS BRONZE
  COMMENT = 'Raw vendor landing layer (S3 external stages, REST API drops)';

USE SCHEMA BRONZE;

-- File formats reused by all stages
CREATE FILE FORMAT IF NOT EXISTS ff_csv_vendor
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NULL', 'null')
  EMPTY_FIELD_AS_NULL = TRUE
  COMMENT = 'Standard vendor CSV with header row';

CREATE FILE FORMAT IF NOT EXISTS ff_parquet_vendor
  TYPE = PARQUET
  COMMENT = 'Standard vendor Parquet';

-- Internal stages — stand-ins for vendor S3 buckets.
-- File-naming convention: yyyy=YYYY/mm=MM/dd=DD/<dataset>_<batch>.csv + completion.flag
CREATE STAGE IF NOT EXISTS s3_vendor_market_data
  FILE_FORMAT = ff_csv_vendor
  COMMENT = 'Source Type 1 stand-in: daily-partitioned vendor market data drops';

CREATE STAGE IF NOT EXISTS s3_vendor_corp_actions
  FILE_FORMAT = ff_csv_vendor
  COMMENT = 'Source Type 1 stand-in: corporate actions drops';

-- Source Type 1 landing: market prices (CSV from S3-style drops)
CREATE TABLE IF NOT EXISTS raw_market_prices (
    -- Vendor-shaped columns; loaders will map these to canonical SILVER schema
    vendor_security_id  VARCHAR,
    ticker              VARCHAR,
    price_date          DATE,
    open_price          NUMBER(18, 6),
    high_price          NUMBER(18, 6),
    low_price           NUMBER(18, 6),
    close_price         NUMBER(18, 6),
    adj_close_price     NUMBER(18, 6),
    volume              NUMBER(20, 0),
    currency            VARCHAR(3),
    -- Lineage / batch metadata for completion-file detection + lookback windows
    source_file         VARCHAR,
    source_batch_id     VARCHAR,
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Vendor market prices landing from S3 stage @s3_vendor_market_data';

-- Source Type 2 landing: REST API holdings (paginated, date-partitioned)
CREATE TABLE IF NOT EXISTS raw_rest_holdings (
    portfolio_id        VARCHAR,
    instrument_id       VARCHAR,    -- vendor-side ID, joins to identifier_map
    as_of_date          DATE,
    quantity            NUMBER(20, 6),
    market_value        NUMBER(20, 6),
    currency            VARCHAR(3),
    -- REST pagination / batch lineage
    api_endpoint        VARCHAR,
    page_number         NUMBER,
    api_response_id     VARCHAR,
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'REST API holdings landing (paginated, date-partitioned)';

-- Source Type 1 landing: corporate actions
CREATE TABLE IF NOT EXISTS raw_corporate_actions (
    vendor_security_id  VARCHAR,
    action_type         VARCHAR,    -- DIVIDEND / SPLIT / MERGER / ...
    ex_date             DATE,
    record_date         DATE,
    pay_date            DATE,
    ratio               NUMBER(18, 6),
    cash_amount         NUMBER(18, 6),
    currency            VARCHAR(3),
    source_file         VARCHAR,
    source_batch_id     VARCHAR,
    ingested_at         TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
COMMENT = 'Corporate actions landing from S3 stage @s3_vendor_corp_actions';
