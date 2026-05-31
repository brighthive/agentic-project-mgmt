-- Longitudinal monitoring store (POC use case 4.3).
-- One row per (dataset, metric, snapshot) so anomalies are detected against a
-- trailing window rather than a single pass/fail gate.

USE ROLE LONGAEVA_POC_ROLE;
USE DATABASE LONGAEVA_POC;

CREATE SCHEMA IF NOT EXISTS MONITORING
  COMMENT = 'Longitudinal data-health metrics, tracked over time';

USE SCHEMA MONITORING;

CREATE TABLE IF NOT EXISTS metric_history (
    snapshot_ts       TIMESTAMP_NTZ NOT NULL,
    dataset           VARCHAR       NOT NULL,   -- e.g. GOLD.mart_daily_portfolio_exposure
    metric_name       VARCHAR       NOT NULL,   -- row_count | cardinality:<col> | null_rate:<col> | mean:<col> | stddev:<col>
    metric_value      FLOAT,
    run_id            VARCHAR,
    CONSTRAINT pk_metric_history PRIMARY KEY (snapshot_ts, dataset, metric_name)
)
COMMENT = 'Per-snapshot data-health metrics for trend-based anomaly detection';

CREATE TABLE IF NOT EXISTS anomaly_events (
    detected_ts       TIMESTAMP_NTZ NOT NULL,
    dataset           VARCHAR       NOT NULL,
    metric_name       VARCHAR       NOT NULL,
    current_value     FLOAT,
    baseline_value    FLOAT,
    deviation_pct     FLOAT,
    anomaly_type      VARCHAR,                  -- row_count_drift | cardinality_breakdown | distributional_skew | null_spike
    severity          VARCHAR,                  -- info | warning | error
    description       VARCHAR
)
COMMENT = 'Anomalies surfaced by the longitudinal monitor';
