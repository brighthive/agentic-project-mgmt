-- Loop Capital sandbox — the OTHER databases on the instance (BH-1403 / BH-172).
--
-- A SQL Server INSTANCE hosts many databases; Frank's box certainly does, and
-- Doc 1 grants us "read on in-scope DBs" (plural) plus the SSISDB/ReportServer
-- catalogs. A one-database sandbox cannot exercise any of that: not criterion 1
-- ("connect & catalog"), not three-part `DB.schema.table` naming, and not
-- BH-172's cross-database table parity.
--
-- These two databases are NOT invented. They are the ones the sandbox's own
-- diagnostic artifacts already reference, which until now pointed at nothing:
--
--   ssis/02_LoadTradesFromOLTP.dtsx  reads OMS.dbo.{Trades,Positions,SecurityMaster}
--                                    and writes TradeDW.dbo.FactTrade
--   ssrs/DailyTradeBlotter.rdl       reads TradeDW.dbo.FactTrade JOIN dbo.SecurityMaster
--   contracts/TradeDW.ReconStaging.xsd   declares TradeDW.dbo.ReconStaging
--
-- Creating them promotes three orphaned samples into live fixtures, and gives a
-- realistic OLTP -> warehouse hop for lineage: OMS is the operational source,
-- TradeDW is what SSIS loads into, LoopCapitalAM is the Asset Management mart.
--
-- FILE PLACEMENT MATTERS. These live on SQL Server's DEFAULT data path (the
-- persistent system volume), NOT the fixed-size tmpfs mount that LoopCapitalAM
-- sits on. GC-15's disk-pressure scenario measures free space on THAT mount, so
-- putting these here keeps fill_disk.sh's math scoped to LoopCapitalAM exactly
-- as designed — otherwise every new database would silently move the 18% target.

-- ============================================================================
-- OMS — the order-management OLTP system SSIS extracts FROM
-- ============================================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'OMS')
  CREATE DATABASE OMS;
GO

USE OMS;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SecurityMaster')
CREATE TABLE dbo.SecurityMaster (
    security_id   VARCHAR(20) PRIMARY KEY,
    Symbol        NVARCHAR(12) NOT NULL,
    security_name VARCHAR(200),
    asset_class   VARCHAR(50),
    currency      VARCHAR(3) NOT NULL DEFAULT 'USD'
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Trades')
CREATE TABLE dbo.Trades (
    trade_id     BIGINT IDENTITY PRIMARY KEY,
    Symbol       NVARCHAR(12) NOT NULL,
    side         VARCHAR(4) NOT NULL,          -- BUY / SELL
    LastQty      INT NOT NULL,
    LastPx       MONEY NOT NULL,
    trade_date   DATE NOT NULL,
    portfolio_id VARCHAR(20) NOT NULL,
    booked_at    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Positions')
CREATE TABLE dbo.Positions (
    position_id  BIGINT IDENTITY PRIMARY KEY,
    portfolio_id VARCHAR(20) NOT NULL,
    Symbol       NVARCHAR(12) NOT NULL,
    quantity     DECIMAL(18,4) NOT NULL,
    as_of_date   DATE NOT NULL
);
GO

-- ============================================================================
-- TradeDW — the trading warehouse SSIS loads INTO, and SSRS reports off
-- ============================================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'TradeDW')
  CREATE DATABASE TradeDW;
GO

USE TradeDW;
GO

-- The dimension DailyTradeBlotter.rdl joins. Replicated from OMS, which is what
-- a real SSIS dimension load does — and gives BH-172 a genuine cross-database
-- parity target: OMS.dbo.SecurityMaster vs TradeDW.dbo.SecurityMaster.
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SecurityMaster')
CREATE TABLE dbo.SecurityMaster (
    security_id   VARCHAR(20) PRIMARY KEY,
    Symbol        NVARCHAR(12) NOT NULL,
    security_name VARCHAR(200),
    asset_class   VARCHAR(50),
    currency      VARCHAR(3) NOT NULL DEFAULT 'USD'
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'FactTrade')
CREATE TABLE dbo.FactTrade (
    fact_trade_id BIGINT IDENTITY PRIMARY KEY,
    Symbol        NVARCHAR(12) NOT NULL,
    side          VARCHAR(4) NOT NULL,
    LastQty       INT NOT NULL,
    LastPx        MONEY NOT NULL,
    trade_date    DATE NOT NULL,
    portfolio_id  VARCHAR(20) NOT NULL,
    notional_usd  AS (LastQty * LastPx),
    loaded_at     DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- Built to contracts/TradeDW.ReconStaging.xsd EXACTLY, defects included:
--   * NO primary key — the XSD records "Primary key: (none defined)"
--   * LastPx is MONEY while the pipeline feeds it a DT_STR (TC-DTM-03)
-- These are the findings a diagnostics skill is supposed to surface, so
-- "fixing" them here would delete the very thing under test.
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ReconStaging')
CREATE TABLE dbo.ReconStaging (
    Symbol  NVARCHAR(12) NOT NULL,
    LastQty INT NULL,
    LastPx  MONEY NULL
);
GO

-- ============================================================================
-- Deterministic seed. Same construction as reset.py's baseline: every value
-- derives from the row number, so the content is identical on every rebuild.
-- $(ANCHOR_DATE) pins the date window the same way reset.py --anchor-date does.
-- ============================================================================

USE OMS;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.SecurityMaster)
INSERT INTO dbo.SecurityMaster (security_id, Symbol, security_name, asset_class, currency)
SELECT
    'SEC-' + RIGHT('000' + CAST(n AS VARCHAR), 3),
    'TCK' + RIGHT('000' + CAST(n AS VARCHAR), 3),
    'Synthetic Security ' + CAST(n AS VARCHAR),
    CASE n % 3 WHEN 0 THEN 'EQUITY' WHEN 1 THEN 'FIXED_INCOME' ELSE 'DERIVATIVE' END,
    'USD'
FROM (SELECT TOP (50) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n FROM sys.all_objects) AS seq;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Trades)
INSERT INTO dbo.Trades (Symbol, side, LastQty, LastPx, trade_date, portfolio_id)
SELECT
    'TCK' + RIGHT('000' + CAST((n % 50) + 1 AS VARCHAR), 3),
    CASE n % 2 WHEN 0 THEN 'BUY' ELSE 'SELL' END,
    100 + (n % 400),
    CAST(10.0 + (n % 90) + 0.25 AS MONEY),
    DATEADD(DAY, -1 * (n % 30), CAST('$(ANCHOR_DATE)' AS DATE)),
    'PORT-' + RIGHT('000' + CAST((n % 5) + 1 AS VARCHAR), 3)
FROM (SELECT TOP (500) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n FROM sys.all_objects) AS seq;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.Positions)
INSERT INTO dbo.Positions (portfolio_id, Symbol, quantity, as_of_date)
SELECT
    'PORT-' + RIGHT('000' + CAST((n % 5) + 1 AS VARCHAR), 3),
    'TCK' + RIGHT('000' + CAST((n % 50) + 1 AS VARCHAR), 3),
    1000.0 + (n * 12.5),
    DATEADD(DAY, -1 * (n % 30), CAST('$(ANCHOR_DATE)' AS DATE))
FROM (SELECT TOP (250) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n FROM sys.all_objects) AS seq;
GO

USE TradeDW;
GO

-- The dimension load: OMS -> TradeDW, three-part naming across databases.
IF NOT EXISTS (SELECT 1 FROM dbo.SecurityMaster)
INSERT INTO dbo.SecurityMaster (security_id, Symbol, security_name, asset_class, currency)
SELECT security_id, Symbol, security_name, asset_class, currency FROM OMS.dbo.SecurityMaster;
GO

-- The fact load the SSIS package models. Deliberately loads only trades on or
-- before the anchor, so FactTrade lags OMS.dbo.Trades by design — a real,
-- explainable row-count gap for cross-database parity to find.
IF NOT EXISTS (SELECT 1 FROM dbo.FactTrade)
INSERT INTO dbo.FactTrade (Symbol, side, LastQty, LastPx, trade_date, portfolio_id)
SELECT Symbol, side, LastQty, LastPx, trade_date, portfolio_id
FROM OMS.dbo.Trades
WHERE trade_date < DATEADD(DAY, -1, CAST('$(ANCHOR_DATE)' AS DATE));
GO

-- FIX drop-copy landing rows. Sparse LastQty/LastPx on purpose: the XSD marks
-- both nullable, and null-rate is what a profiler run should flag.
IF NOT EXISTS (SELECT 1 FROM dbo.ReconStaging)
INSERT INTO dbo.ReconStaging (Symbol, LastQty, LastPx)
SELECT
    'TCK' + RIGHT('000' + CAST((n % 50) + 1 AS VARCHAR), 3),
    CASE WHEN n % 7 = 0 THEN NULL ELSE 100 + (n % 400) END,
    CASE WHEN n % 11 = 0 THEN NULL ELSE CAST(10.0 + (n % 90) + 0.25 AS MONEY) END
FROM (SELECT TOP (200) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n FROM sys.all_objects) AS seq;
GO
