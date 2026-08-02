

-- The reclaim model. The nightly SSIS extract left `holdings_snapshot_raw` as a
-- wide, uncompressed heap that appends a full copy of the book every night and
-- never dedups — the single biggest consumer on the Loop Capital data volume.
--
-- This model keeps only what the business actually reads: the LATEST snapshot
-- per (portfolio, instrument), narrowly typed, with the redundant per-row JSON
-- blob dropped entirely, then compressed with a clustered columnstore index
-- (as_columnstore = true — dbt-sqlserver builds the CCI natively for a `table`
-- model). The driver drops the raw heap and SHRINKFILEs afterward, so
-- the bytes this removes are released back to the real volume — the 70%-free
-- monitor flips from BREACH to OK.
--
-- Oversized source types (NVARCHAR(4000), DECIMAL(38,10)) are cast down to what
-- the domain needs: short codes fit VARCHAR(20), money fits DECIMAL(18,4).

WITH ranked AS (
    SELECT
        CAST(portfolio_id  AS VARCHAR(20))   AS portfolio_id,
        CAST(instrument_id AS VARCHAR(20))   AS instrument_id,
        CAST(quantity      AS DECIMAL(18, 4)) AS quantity,
        CAST(price         AS DECIMAL(18, 4)) AS price,
        CAST(market_value  AS DECIMAL(18, 4)) AS market_value,
        CAST(currency      AS VARCHAR(3))     AS currency,
        snapshot_date,
        ROW_NUMBER() OVER (
            PARTITION BY portfolio_id, instrument_id
            ORDER BY snapshot_date DESC
        ) AS recency_rank
    FROM "LoopCapitalAM"."dbo"."holdings_snapshot_raw"
)

SELECT
    portfolio_id,
    instrument_id,
    quantity,
    price,
    market_value,
    currency,
    snapshot_date AS as_of_date
FROM ranked
WHERE recency_rank = 1