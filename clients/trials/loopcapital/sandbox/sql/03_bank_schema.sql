-- Loop Capital Asset Management -- full synthetic bank data model (BH-1036)
-- 3-tier medallion architecture: BRONZE (raw_*) → SILVER (stg_*) → GOLD (mart_*)
-- Matches the dbt naming convention `lineage_graph.py` uses for tier classification.
-- Seeded by 04_seed_bank_data.sql (run after this file).

USE LoopCapitalAM;
GO

-- ============================================================================
-- BRONZE / RAW layer — custodian and market data feeds, unvalidated
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'raw_positions')
CREATE TABLE raw_positions (
    position_id     BIGINT IDENTITY PRIMARY KEY,
    portfolio_id    VARCHAR(20) NOT NULL,
    security_id     VARCHAR(20) NOT NULL,
    cusip           VARCHAR(12),
    isin            VARCHAR(12),
    quantity        DECIMAL(18,4) NOT NULL,
    market_value    DECIMAL(18,2),
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    as_of_date      DATE NOT NULL,
    source_system   VARCHAR(50) DEFAULT 'CUSTODIAN_A',
    loaded_at       DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'raw_security_master')
CREATE TABLE raw_security_master (
    security_id     VARCHAR(20) PRIMARY KEY,
    cusip           VARCHAR(12),
    isin            VARCHAR(12),
    ticker          VARCHAR(10),
    security_name   VARCHAR(200),
    asset_class     VARCHAR(50),  -- EQUITY, FIXED_INCOME, CASH, DERIVATIVE
    sector          VARCHAR(100),
    country         VARCHAR(3),
    currency        VARCHAR(3),
    is_active       BIT DEFAULT 1,
    last_updated    DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'raw_market_prices')
CREATE TABLE raw_market_prices (
    price_id        BIGINT IDENTITY PRIMARY KEY,
    security_id     VARCHAR(20) NOT NULL,
    price_date      DATE NOT NULL,
    close_price     DECIMAL(18,6) NOT NULL,
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    price_source    VARCHAR(50) DEFAULT 'BLOOMBERG',
    loaded_at       DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'raw_counterparties')
CREATE TABLE raw_counterparties (
    counterparty_id  VARCHAR(20) PRIMARY KEY,
    name             VARCHAR(200) NOT NULL,
    legal_entity_id  VARCHAR(50),
    country          VARCHAR(3),
    credit_rating    VARCHAR(10),
    is_active        BIT DEFAULT 1,
    created_at       DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- ============================================================================
-- SILVER / STAGING layer — validated, enriched, ready for analytics
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'stg_positions')
CREATE TABLE stg_positions (
    position_id       BIGINT PRIMARY KEY,
    portfolio_id      VARCHAR(20) NOT NULL,
    security_id       VARCHAR(20) NOT NULL,
    security_name     VARCHAR(200),
    asset_class       VARCHAR(50),
    sector            VARCHAR(100),
    quantity          DECIMAL(18,4) NOT NULL,
    close_price       DECIMAL(18,6),
    market_value      DECIMAL(18,2),
    market_value_usd  DECIMAL(18,2),
    currency          VARCHAR(3) NOT NULL,
    as_of_date        DATE NOT NULL,
    data_quality_flag VARCHAR(20) DEFAULT 'CLEAN',  -- CLEAN / WARN / ERROR
    processed_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'stg_holdings')
CREATE TABLE stg_holdings (
    holding_id        INT IDENTITY PRIMARY KEY,
    portfolio_id      VARCHAR(20) NOT NULL,
    instrument_id     VARCHAR(20) NOT NULL,
    security_name     VARCHAR(200),
    asset_class       VARCHAR(50),
    quantity          DECIMAL(18,4) NOT NULL,
    market_value_usd  DECIMAL(18,2),
    weight_pct        DECIMAL(8,4),
    as_of_date        DATE NOT NULL,
    settlement_ccy    VARCHAR(3),
    processed_at      DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'stg_daily_pnl')
CREATE TABLE stg_daily_pnl (
    pnl_id          BIGINT IDENTITY PRIMARY KEY,
    portfolio_id    VARCHAR(20) NOT NULL,
    security_id     VARCHAR(20) NOT NULL,
    trade_date      DATE NOT NULL,
    realised_pnl    DECIMAL(18,2) DEFAULT 0,
    unrealised_pnl  DECIMAL(18,2) DEFAULT 0,
    total_pnl       AS (realised_pnl + unrealised_pnl),
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    calculated_at   DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- ============================================================================
-- GOLD / MART layer — aggregated, KPI-ready, what the risk reports query
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'mart_daily_portfolio_exposure')
CREATE TABLE mart_daily_portfolio_exposure (
    exposure_id           BIGINT IDENTITY PRIMARY KEY,
    portfolio_id          VARCHAR(20) NOT NULL,
    as_of_date            DATE NOT NULL,
    total_market_value    DECIMAL(18,2),
    equity_exposure       DECIMAL(18,2),
    fixed_income_exposure DECIMAL(18,2),
    cash_exposure         DECIMAL(18,2),
    num_positions         INT,
    top_holding_pct       DECIMAL(8,4),
    calculated_at         DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UNIQUE (portfolio_id, as_of_date)
);
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'mart_portfolio_risk_summary')
CREATE TABLE mart_portfolio_risk_summary (
    risk_id         BIGINT IDENTITY PRIMARY KEY,
    portfolio_id    VARCHAR(20) NOT NULL,
    as_of_date      DATE NOT NULL,
    var_1d_95       DECIMAL(18,4),
    var_1d_99       DECIMAL(18,4),
    beta            DECIMAL(8,4),
    sharpe_ratio    DECIMAL(8,4),
    max_drawdown_pct DECIMAL(8,4),
    calculated_at   DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

-- Compliance limit breaches -- the proactive monitoring target (GC-14/15 demo)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'mart_compliance_breaches')
CREATE TABLE mart_compliance_breaches (
    breach_id       BIGINT IDENTITY PRIMARY KEY,
    portfolio_id    VARCHAR(20) NOT NULL,
    rule_name       VARCHAR(100) NOT NULL,
    breach_type     VARCHAR(50),    -- CONCENTRATION / SECTOR_LIMIT / LEVERAGE
    limit_value     DECIMAL(18,4),
    actual_value    DECIMAL(18,4),
    breach_pct      DECIMAL(8,4),
    as_of_date      DATE NOT NULL,
    severity        VARCHAR(20) DEFAULT 'WARNING',  -- WARNING / CRITICAL
    resolved_at     DATETIME2,
    detected_at     DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
