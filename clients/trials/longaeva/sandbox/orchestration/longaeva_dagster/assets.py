"""Dagster assets orchestrating the Longaeva ELT pipeline.

Mirrors Grant's stack: Dagster for orchestration, OpenLineage export, dbt for
transformation. The asset graph is the lineage the self-healing + monitoring
agents read.

Asset graph:

  bronze_s3_market_prices ─┐
  bronze_rest_holdings ────┼─> silver_int_enriched_holdings (via dbt) ─┐
  vendor_share_staging ────┘                                          │
                                                                       ├─> gold_data_products (dbt)
  ref_seed (geo/fiscal/identifier) ────────────────────────────────────┘
                                                                       │
                                          semantic_view_validated <────┘
                                                                       │
                                          anomaly_snapshot <───────────┘

Each asset emits a run-log line to MONITORING-style logging so the self-healing
agent has a log surface to diagnose from (stands in for OpenLineage events).

Run:
  cd orchestration
  uv run --with dagster --with dagster-webserver --with dbt-snowflake \\
    --with snowflake-connector-python dagster dev
  # or materialize headless:
  uv run ... dagster asset materialize --select '*' -m longaeva_dagster.definitions
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from dagster import (
    MaterializeResult,
    MetadataValue,
    asset,
)

SANDBOX = Path(__file__).resolve().parents[2]   # .../sandbox
DBT_DIR = SANDBOX / "dbt"


def _run(context, cmd: list[str], cwd: Path) -> str:
    """Run a subprocess, stream a run-log line, return stdout."""
    context.log.info(f"exec: {' '.join(cmd)} (cwd={cwd})")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        context.log.error(proc.stdout[-2000:] + proc.stderr[-2000:])
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    return proc.stdout


# --- Bronze ingestion assets ------------------------------------------------

@asset(group_name="bronze", compute_kind="snowflake")
def bronze_s3_market_prices(context) -> MaterializeResult:
    """S3 vendor bucket -> BRONZE.raw_market_prices (generate + COPY INTO)."""
    src = SANDBOX / "sources" / "s3-vendor-market-data"
    _run(context, ["uv", "run", "--quiet", "--with", "snowflake-connector-python",
                   "python", "ingest.py", "--generate", "--days", "3"], src)
    out = _run(context, ["uv", "run", "--quiet", "--with", "snowflake-connector-python",
                         "python", "ingest.py", "--load", "--lookback", "7"], src)
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(out[-500:])})


@asset(group_name="bronze", compute_kind="snowflake")
def bronze_rest_holdings(context) -> MaterializeResult:
    """REST API -> BRONZE.raw_rest_holdings (assumes stub on :8000)."""
    src = SANDBOX / "sources" / "rest-stub"
    out = _run(context, ["uv", "run", "--quiet", "--with", "httpx",
                         "--with", "snowflake-connector-python", "python", "ingest.py",
                         "--as-of-date", "2026-05-29", "--max-ids", "1000", "--truncate"], src)
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(out[-500:])})


@asset(group_name="bronze", compute_kind="snowflake")
def vendor_share_seeded(context) -> MaterializeResult:
    """Snowflake Data Share simulation seeded."""
    src = SANDBOX / "sources" / "snowflake-data-share"
    out = _run(context, ["snow", "sql", "-f", "seed_share.sql", "-c", "brighthive"], src)
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(out[-500:])})


# --- Silver + Gold via dbt --------------------------------------------------

@asset(group_name="silver_gold", compute_kind="dbt",
       deps=[bronze_s3_market_prices, bronze_rest_holdings, vendor_share_seeded])
def dbt_build(context) -> MaterializeResult:
    """dbt build: SILVER int model + GOLD data products + tests."""
    out = _run(context, ["bash", "-c",
                         "source ./set_env.sh >/dev/null && DBT_PROFILES_DIR=. "
                         "uv run --quiet --with dbt-snowflake dbt build"], DBT_DIR)
    # surface the dbt PASS/ERROR summary line as run metadata
    summary = next((l for l in out.splitlines() if "PASS=" in l), "")
    return MaterializeResult(metadata={"dbt_summary": MetadataValue.text(summary)})


# --- Semantic view validation -----------------------------------------------

@asset(group_name="semantic", compute_kind="snowflake", deps=[dbt_build])
def semantic_view_validated(context) -> MaterializeResult:
    """Run the 3-layer validation harness over the semantic view."""
    src = SANDBOX / "semantic"
    out = _run(context, ["uv", "run", "--quiet", "--with", "pyyaml",
                         "--with", "snowflake-connector-python", "python", "validate.py",
                         "sv_daily_portfolio_exposure.yaml"], src)
    passed = "Validation: PASS" in out
    if not passed:
        raise RuntimeError("semantic view validation failed")
    return MaterializeResult(metadata={"validation": MetadataValue.text(out[-500:])})


# --- Monitoring snapshot ----------------------------------------------------

@asset(group_name="monitoring", compute_kind="snowflake", deps=[dbt_build])
def anomaly_snapshot(context) -> MaterializeResult:
    """Snapshot data-health metrics into MONITORING.metric_history."""
    src = SANDBOX / "monitoring"
    out = _run(context, ["uv", "run", "--quiet", "--with", "snowflake-connector-python",
                         "python", "monitor.py", "snapshot", "--run-id",
                         f"dagster-{context.run_id[:8]}"], src)
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(out[-500:])})
