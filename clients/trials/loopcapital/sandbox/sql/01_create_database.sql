-- Loop Capital Asset Management — minimal synthetic schema, standing in for
-- the client's real legacy SQL Server (per artifacts/poc-scope-from-client.md's
-- own ask: "a representation of Loop data model — Asset Management").
-- Mirrors the shape SSIS extracts feed today: holdings + a staging table the
-- nightly dbt job depends on. Small on purpose — this sandbox exists to prove
-- BrightHive's watchdog can query a real SQL Server, not to be a full
-- Asset Management data model.

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'LoopCapitalAM')
BEGIN
  CREATE DATABASE LoopCapitalAM;
END
GO

USE LoopCapitalAM;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'holdings_raw')
BEGIN
  CREATE TABLE holdings_raw (
    holding_id     INT IDENTITY PRIMARY KEY,
    portfolio_id   VARCHAR(20)    NOT NULL,
    instrument_id  VARCHAR(20)    NOT NULL,
    quantity       DECIMAL(18, 4) NOT NULL, -- BH-1045's demo drift target: NUMBER -> FLOAT
    as_of_date     DATE           NOT NULL,
    loaded_at      DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME()
  );
END
GO

-- Deterministic seed — same shape every setup.sh run, no RNG.
IF NOT EXISTS (SELECT 1 FROM holdings_raw)
BEGIN
  INSERT INTO holdings_raw (portfolio_id, instrument_id, quantity, as_of_date)
  SELECT
    'PORT-' + RIGHT('000' + CAST((n % 5) + 1 AS VARCHAR), 3),
    'INST-' + RIGHT('0000' + CAST(n AS VARCHAR), 4),
    1000.0 + (n * 12.5),
    DATEADD(DAY, -1 * (n % 30), CAST(SYSUTCDATETIME() AS DATE))
  FROM (SELECT TOP (2000) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n
        FROM sys.all_objects) AS seq;
END
GO
