"""Self-healing failure-mode fixtures (POC use case 4.1).

Grant's four named failure modes, each as a reproducible scenario with:
  - inject():   create the failure condition in Snowflake
  - detect():   the diagnostic query an observability agent would run
  - diagnosis:  plain-language root cause (what the PR description should say)
  - fix_ddl:    the surgical fix (what the PR should change — NOT a rewrite)
  - heal():     apply the fix and confirm detection passes

This proves the detect -> diagnose -> surgical-fix loop end-to-end. The
BrightHive Observability + Engineering agents own the diagnosis-to-PR step in
production; here we encode the *signatures* they must detect and the *exact
fix* they must produce, so the agent work has a target to hit.

Run:
  uv run --with snowflake-connector-python python failure_modes.py list
  uv run --with snowflake-connector-python python failure_modes.py run schema_drift
  uv run --with snowflake-connector-python python failure_modes.py run-all
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import snowflake.connector


def connect(connection: str = "brighthive"):
    cfg_path = Path.home() / ".snowflake" / "config.toml"
    with cfg_path.open("rb") as f:
        c = tomllib.load(f)["connections"][connection]
    return snowflake.connector.connect(
        account=c["account"], user=c["user"], password=c["password"],
        role=c.get("role"), warehouse=c.get("warehouse"),
        database=c.get("database"), schema="BRONZE",
    )


def exec_sql(conn, sql: str):
    cur = conn.cursor()
    for stmt in [s for s in sql.split(";") if s.strip()]:
        cur.execute(stmt)
    return cur


def scalar(conn, sql: str):
    cur = conn.cursor()
    cur.execute(sql)
    row = cur.fetchone()
    return row[0] if row else None


@dataclass
class FailureMode:
    key: str
    title: str
    diagnosis: str
    inject: Callable[[object], None]
    detect: Callable[[object], bool]   # returns True when failure IS present
    heal: Callable[[object], None]
    fix_summary: str


# -----------------------------------------------------------------------------
# 1. Schema drift — vendor adds/renames a column in the landing table.
# -----------------------------------------------------------------------------

def _drift_inject(conn):
    # Vendor starts sending a new column "settlement_ccy" that our table lacks.
    # We simulate by creating a drifted staging table that the dbt source expects.
    exec_sql(conn, """
        CREATE OR REPLACE TABLE LONGAEVA_POC.BRONZE._drift_market_prices AS
        SELECT *, 'USD' AS settlement_ccy
        FROM LONGAEVA_POC.BRONZE.raw_market_prices LIMIT 10
    """)

def _drift_detect(conn) -> bool:
    # Drift present if the drifted table has a column the canonical table lacks.
    canonical = set(_columns(conn, "RAW_MARKET_PRICES"))
    drifted = set(_columns(conn, "_DRIFT_MARKET_PRICES"))
    return bool(drifted - canonical)

def _drift_heal(conn):
    # Surgical fix: ALTER TABLE ADD COLUMN (not a rewrite).
    new_cols = set(_columns(conn, "_DRIFT_MARKET_PRICES")) - set(_columns(conn, "RAW_MARKET_PRICES"))
    for col in new_cols:
        exec_sql(conn, f"ALTER TABLE LONGAEVA_POC.BRONZE.raw_market_prices ADD COLUMN {col} VARCHAR")
    exec_sql(conn, "DROP TABLE IF EXISTS LONGAEVA_POC.BRONZE._drift_market_prices")


def _columns(conn, table: str) -> list[str]:
    cur = conn.cursor()
    cur.execute(f"""
        SELECT column_name FROM LONGAEVA_POC.information_schema.columns
        WHERE table_schema = 'BRONZE' AND table_name = '{table}'
    """)
    return [r[0] for r in cur.fetchall()]


# -----------------------------------------------------------------------------
# 2. Missing partition — a daily partition never landed.
# -----------------------------------------------------------------------------

def _partition_inject(conn):
    # Remove one day's rows to simulate a partition that failed to land.
    exec_sql(conn, """
        DELETE FROM LONGAEVA_POC.SILVER.stg_security_prices
        WHERE ts = '2026-05-15'
    """)

def _partition_detect(conn) -> bool:
    # Detect a business-day gap in the daily series.
    gaps = scalar(conn, """
        WITH days AS (
          SELECT DISTINCT ts FROM LONGAEVA_POC.SILVER.stg_security_prices
        ),
        expected AS (
          SELECT DATEADD(day, seq4(), '2026-05-01') AS d
          FROM TABLE(GENERATOR(ROWCOUNT => 29))
        )
        SELECT COUNT(*) FROM expected e
        WHERE DAYOFWEEK(e.d) BETWEEN 1 AND 5
          AND e.d <= (SELECT MAX(ts) FROM days)
          AND e.d NOT IN (SELECT ts FROM days)
    """)
    return (gaps or 0) > 0

def _partition_heal(conn):
    # Surgical fix: backfill the missing partition from the most recent prior day.
    exec_sql(conn, """
        INSERT INTO LONGAEVA_POC.SILVER.stg_security_prices
        SELECT internal_issuer_id, instrument_id, metric_name,
               '2026-05-15'::DATE AS ts, value, currency, source_system,
               as_of_time, 'BACKFILLED' AS quality_flag
        FROM LONGAEVA_POC.SILVER.stg_security_prices
        WHERE ts = '2026-05-14'
    """)


# -----------------------------------------------------------------------------
# 3. Broken external stage — stage points at a bad location / wrong file format.
# -----------------------------------------------------------------------------

def _stage_inject(conn):
    # Break the stage by pointing its file format at a non-existent one.
    exec_sql(conn, """
        CREATE OR REPLACE STAGE LONGAEVA_POC.BRONZE.s3_vendor_market_data
          FILE_FORMAT = (TYPE = JSON)
          COMMENT = 'BROKEN: wrong file format for CSV drops'
    """)

def _stage_detect(conn) -> bool:
    # Detect mismatch: stage file format type != expected CSV.
    fmt = scalar(conn, """
        SELECT "type" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
    """) if False else None
    # Simpler: DESCRIBE STAGE and look for the format type.
    cur = conn.cursor()
    cur.execute("DESCRIBE STAGE LONGAEVA_POC.BRONZE.s3_vendor_market_data")
    rows = cur.fetchall()
    blob = " ".join(str(r) for r in rows)
    return "JSON" in blob and "CSV" not in blob.split("STAGE_FILE_FORMAT")[-1][:200]

def _stage_heal(conn):
    # Surgical fix: restore the correct CSV file format.
    exec_sql(conn, """
        CREATE OR REPLACE STAGE LONGAEVA_POC.BRONZE.s3_vendor_market_data
          FILE_FORMAT = LONGAEVA_POC.BRONZE.ff_csv_vendor
          COMMENT = 'Source Type 1 stand-in: daily-partitioned vendor market data drops'
    """)


# -----------------------------------------------------------------------------
# 4. dbt contract violation — a not-null/range contract starts failing.
# -----------------------------------------------------------------------------

def _contract_inject(conn):
    # Inject negative exposure rows that violate the non-negative contract.
    exec_sql(conn, """
        UPDATE LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure
        SET exposure_amount_usd = -1 * exposure_amount_usd
        WHERE as_of_date = '2026-05-20'
    """)

def _contract_detect(conn) -> bool:
    n = scalar(conn, """
        SELECT COUNT(*) FROM LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure
        WHERE exposure_amount_usd < 0
    """)
    return (n or 0) > 0

def _contract_heal(conn):
    # Surgical fix: correct the sign on the violating rows (root cause: an
    # upstream sign-flip). NOT a table rewrite — scoped to the bad partition.
    exec_sql(conn, """
        UPDATE LONGAEVA_POC.GOLD.mart_daily_portfolio_exposure
        SET exposure_amount_usd = ABS(exposure_amount_usd)
        WHERE exposure_amount_usd < 0
    """)


MODES = {
    "schema_drift": FailureMode(
        key="schema_drift",
        title="Schema drift — vendor adds a column the landing table lacks",
        diagnosis="Vendor delivery added column `settlement_ccy`; landing table "
                  "raw_market_prices has no such column, so COPY INTO would drop it.",
        inject=_drift_inject, detect=_drift_detect, heal=_drift_heal,
        fix_summary="ALTER TABLE raw_market_prices ADD COLUMN settlement_ccy VARCHAR "
                    "(+ update dbt source). Surgical: 1 column, no rewrite.",
    ),
    "missing_partition": FailureMode(
        key="missing_partition",
        title="Missing partition — a daily partition never landed",
        diagnosis="Business day 2026-05-15 has zero rows in stg_security_prices; "
                  "upstream partition failed to deliver.",
        inject=_partition_inject, detect=_partition_detect, heal=_partition_heal,
        fix_summary="Backfill 2026-05-15 from prior business day, flagged "
                    "quality_flag='BACKFILLED'. Scoped to one partition.",
    ),
    "broken_stage": FailureMode(
        key="broken_stage",
        title="Broken external stage — wrong file format",
        diagnosis="Stage s3_vendor_market_data file format is JSON; vendor delivers "
                  "CSV, so COPY INTO fails to parse.",
        inject=_stage_inject, detect=_stage_detect, heal=_stage_heal,
        fix_summary="Restore FILE_FORMAT = ff_csv_vendor on the stage. "
                    "Single DDL statement.",
    ),
    "dbt_contract": FailureMode(
        key="dbt_contract",
        title="dbt contract violation — non-negative exposure breached",
        diagnosis="mart_daily_portfolio_exposure has negative exposure_amount_usd "
                  "for 2026-05-20 (upstream sign flip), violating the non-negative "
                  "contract.",
        inject=_contract_inject, detect=_contract_detect, heal=_contract_heal,
        fix_summary="Correct sign on violating rows (ABS). Scoped to the bad "
                    "partition, not a full rebuild.",
    ),
}


def run_mode(conn, mode: FailureMode) -> bool:
    print(f"\n=== {mode.key}: {mode.title} ===")
    # Healthy baseline
    pre = mode.detect(conn)
    print(f"  baseline detect (expect False/healthy): {pre}")
    # Inject
    mode.inject(conn)
    injected = mode.detect(conn)
    print(f"  after inject (expect True/failure): {injected}")
    print(f"  diagnosis: {mode.diagnosis}")
    print(f"  surgical fix: {mode.fix_summary}")
    # Heal
    mode.heal(conn)
    healed = mode.detect(conn)
    print(f"  after heal (expect False/healthy): {healed}")
    ok = injected and not healed
    print(f"  {'✅ PASS' if ok else '❌ FAIL'} — detect-fired-then-cleared: {ok}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["list", "run", "run-all"])
    ap.add_argument("mode", nargs="?", help="failure mode key (for `run`)")
    ap.add_argument("--connection", default="brighthive")
    args = ap.parse_args()

    if args.command == "list":
        for k, m in MODES.items():
            print(f"  {k:20s} {m.title}")
        return 0

    conn = connect(args.connection)
    if args.command == "run":
        if args.mode not in MODES:
            print(f"unknown mode: {args.mode}. Options: {list(MODES)}", file=sys.stderr)
            return 2
        ok = run_mode(conn, MODES[args.mode])
        conn.close()
        return 0 if ok else 1

    # run-all
    results = {k: run_mode(conn, m) for k, m in MODES.items()}
    conn.close()
    passed = sum(results.values())
    print(f"\n{'='*55}")
    print(f"Self-healing fixtures: {passed}/{len(results)} detect→fix loops verified")
    print("=" * 55)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
