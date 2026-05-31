-- Seed the simulated inbound Snowflake Data Share.
-- Vendor's security master + ratings, keyed off the same issuers we already
-- have in REF.identifier_map so downstream staging joins resolve.
--
-- Run: snow sql -f seed_share.sql -c brighthive

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_VENDOR_SHARE_SIM;
USE SCHEMA SHARED;

TRUNCATE TABLE IF EXISTS vendor_security_master;
TRUNCATE TABLE IF EXISTS vendor_ratings;

-- Vendor security master: one row per issuer, vendor-shaped column names.
INSERT INTO vendor_security_master
  (vendor_security_id, lei, figi, cusip, isin, issuer_name, primary_country,
   primary_exchange, asset_class_code, sector_code, is_active, last_updated)
SELECT
    'VSM-' || RIGHT(internal_issuer_id, 4)        AS vendor_security_id,
    lei,
    figi,
    cusip,
    isin,
    issuer_name,
    primary_country,
    CASE MOD(ABS(HASH(internal_issuer_id)), 4)
      WHEN 0 THEN 'NYSE' WHEN 1 THEN 'NASDAQ'
      WHEN 2 THEN 'LSE'  ELSE 'TSE' END           AS primary_exchange,
    'EQUITY'                                       AS asset_class_code,
    primary_sector                                AS sector_code,
    is_active,
    '2026-05-29 06:00:00'::TIMESTAMP_NTZ          AS last_updated
FROM LONGAEVA_POC.REF.identifier_map;

-- Vendor ratings: one rating per issuer from two agencies.
INSERT INTO vendor_ratings
  (vendor_security_id, rating_agency, rating_date, rating_value, rating_outlook, last_updated)
SELECT
    'VSM-' || RIGHT(internal_issuer_id, 4)        AS vendor_security_id,
    agency.name                                   AS rating_agency,
    '2026-03-31'::DATE                            AS rating_date,
    ARRAY_CONSTRUCT('AAA','AA','A','BBB','BB','B')[
      MOD(ABS(HASH(internal_issuer_id || agency.name)), 6)
    ]::STRING                                     AS rating_value,
    ARRAY_CONSTRUCT('STABLE','POSITIVE','NEGATIVE')[
      MOD(ABS(HASH(internal_issuer_id)), 3)
    ]::STRING                                     AS rating_outlook,
    '2026-04-01 06:00:00'::TIMESTAMP_NTZ          AS last_updated
FROM LONGAEVA_POC.REF.identifier_map,
     (SELECT 'MOODYS' AS name UNION ALL SELECT 'SP') agency;

SELECT 'vendor_security_master' AS tbl, COUNT(*) AS row_count FROM vendor_security_master
UNION ALL
SELECT 'vendor_ratings', COUNT(*) FROM vendor_ratings;
