-- Loop Capital Asset Management — minimal synthetic schema, standing in for
-- the client's real legacy SQL Server (per artifacts/poc-scope-from-client.md's
-- own ask: "a representation of Loop data model — Asset Management").
-- Mirrors the shape SSIS extracts feed today: holdings + a staging table the
-- nightly dbt job depends on. Small on purpose — this sandbox exists to prove
-- BrightHive's watchdog can query a real SQL Server, not to be a full
-- Asset Management data model.

-- Placed explicitly on the dedicated tmpfs mount (docker-compose.yml's
-- loopcapital_data path), NOT SQL Server's default /var/opt/mssql/data —
-- system databases (master/msdb/model) stay on the persistent system
-- volume untouched. A prior version of this fixture tmpfs-mounted the
-- DEFAULT data path directly, which wiped system databases on restart
-- (caught in review, fixed here).
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'LoopCapitalAM')
BEGIN
  CREATE DATABASE LoopCapitalAM
  ON (
    NAME = LoopCapitalAM,
    FILENAME = '/var/opt/mssql/loopcapital_data/LoopCapitalAM.mdf'
  )
  LOG ON (
    NAME = LoopCapitalAM_log,
    FILENAME = '/var/opt/mssql/loopcapital_data/LoopCapitalAM_log.ldf'
  );
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

-- Schema only, deliberately NOT seeded here. reset.py owns all seeding
-- (baseline row count + scenario data) so there is exactly ONE seeding
-- mechanism, not two — a prior version seeded here AND in reset.py's
-- seed_baseline(), silently doubling every row count (caught in review).
-- setup.sh calls reset.py --scenario baseline right after this file runs.
