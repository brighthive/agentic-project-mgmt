-- 90_weekly_delta.sql — GOLD.MART_WEEKLY_EXPOSURE_DELTA
--
-- Powers Bar 3 of the non-technical UAT ("what changed in the last week?").
-- One row per (portfolio × issuer) with today's exposure vs 7 calendar days
-- earlier and the deltas. Idempotent: CREATE OR REPLACE.
--
-- Refresh model: rebuilt nightly from MART_DAILY_PORTFOLIO_EXPOSURE.
-- For PoC purposes the as-of date is the max date in the source mart.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;
USE SCHEMA GOLD;

CREATE OR REPLACE TABLE MART_WEEKLY_EXPOSURE_DELTA AS
WITH max_date AS (
    SELECT MAX(as_of_date) AS d FROM GOLD.MART_DAILY_PORTFOLIO_EXPOSURE
),
today_snap AS (
    SELECT
        m.portfolio_id,
        m.internal_issuer_id,
        ANY_VALUE(m.sector_code) AS sector_code,
        ANY_VALUE(m.country_code) AS country_code,
        SUM(m.exposure_amount_usd) AS exposure_today_usd,
        ANY_VALUE(m.as_of_date) AS as_of_date
    FROM GOLD.MART_DAILY_PORTFOLIO_EXPOSURE m
    JOIN max_date d ON m.as_of_date = d.d
    GROUP BY m.portfolio_id, m.internal_issuer_id
),
prior_snap AS (
    SELECT
        m.portfolio_id,
        m.internal_issuer_id,
        SUM(m.exposure_amount_usd) AS exposure_7d_ago_usd
    FROM GOLD.MART_DAILY_PORTFOLIO_EXPOSURE m
    JOIN max_date d ON m.as_of_date = DATEADD(DAY, -7, d.d)
    GROUP BY m.portfolio_id, m.internal_issuer_id
)
SELECT
    t.portfolio_id,
    t.internal_issuer_id,
    i.issuer_name,
    t.sector_code,
    t.country_code,
    g.country_name,
    t.exposure_today_usd,
    COALESCE(p.exposure_7d_ago_usd, 0) AS exposure_7d_ago_usd,
    t.exposure_today_usd - COALESCE(p.exposure_7d_ago_usd, 0) AS delta_usd,
    CASE
        WHEN COALESCE(p.exposure_7d_ago_usd, 0) = 0 THEN NULL
        ELSE ROUND(100.0 * (t.exposure_today_usd - p.exposure_7d_ago_usd) / p.exposure_7d_ago_usd, 4)
    END AS delta_pct,
    CASE
        WHEN p.exposure_7d_ago_usd IS NULL OR p.exposure_7d_ago_usd = 0 THEN 'new_position'
        WHEN t.exposure_today_usd = 0 THEN 'closed_position'
        WHEN t.exposure_today_usd > p.exposure_7d_ago_usd THEN 'increased'
        WHEN t.exposure_today_usd < p.exposure_7d_ago_usd THEN 'decreased'
        ELSE 'unchanged'
    END AS change_type,
    t.as_of_date,
    CURRENT_TIMESTAMP() AS build_ts
FROM today_snap t
LEFT JOIN prior_snap p
    ON t.portfolio_id = p.portfolio_id
   AND t.internal_issuer_id = p.internal_issuer_id
LEFT JOIN REF.IDENTIFIER_MAP i
    ON t.internal_issuer_id = i.internal_issuer_id
   AND i.is_active = TRUE
LEFT JOIN REF.GEO_CODES g
    ON t.country_code = g.country_code;

ALTER TABLE MART_WEEKLY_EXPOSURE_DELTA
  SET COMMENT = 'Per (portfolio,issuer) week-over-week exposure delta. Built nightly from MART_DAILY_PORTFOLIO_EXPOSURE. Drives Q3 of Sarah''s Monday morning demo.';

-- Verify
SELECT change_type, COUNT(*) AS n FROM MART_WEEKLY_EXPOSURE_DELTA GROUP BY 1 ORDER BY n DESC;
SELECT COUNT(*) AS total_rows FROM MART_WEEKLY_EXPOSURE_DELTA;

-- Top 5 movers in dollar terms (P-000, the demo portfolio)
SELECT issuer_name, sector_code, country_name, exposure_today_usd, exposure_7d_ago_usd, delta_usd, delta_pct, change_type
FROM MART_WEEKLY_EXPOSURE_DELTA
WHERE portfolio_id = 'P-000'
ORDER BY ABS(delta_usd) DESC
LIMIT 5;

-- Grant read to agent
USE ROLE ACCOUNTADMIN;
GRANT SELECT ON TABLE LONGAEVA_POC.GOLD.MART_WEEKLY_EXPOSURE_DELTA TO ROLE LONGAEVA_AGENT_ROLE;
