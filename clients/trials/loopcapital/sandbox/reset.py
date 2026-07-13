#!/usr/bin/env python3
"""Tears the sandbox down to ground zero and reseeds it against a named
scenario — the ask: "we need to be able to tear up and tear down so we can
always come back to ground zero in the middle of flight developments and
redefine the seeds to achieve the cases we want to represent."

Ground zero = LoopCapitalAM dropped and recreated fresh (not the whole
container) — the fast path for "redefine the seed and try again" during
active development, without paying Docker's ~20s container-boot cost every
time. Use `docker compose down -v && docker compose up -d` (or setup.sh)
for a full container-level reset; use THIS script to reset just the data
between scenario runs on an already-running container.

Scenarios (each maps to a real Golden Case this sandbox exists to prove):

  baseline        Clean 2,000-row seed, no injected problem. Starting point.
  disk-pressure   GC-15: same seed, then fills the data volume to ~18% free
                  (delegates to fill_disk.sh — this script's job is the DATA
                  reset, not the disk-fill mechanism, which stays separate
                  since it operates at the filesystem level, not SQL).
  type-drift      GC-16: seeds holdings_raw, then appends a second batch of
                  rows where `quantity` was written as a string ('1234.5')
                  instead of a native decimal, simulating the NUMBER->FLOAT
                  source-column drift GC-16's demo scenario describes.
  cancelled-run   GC-14: reseeds baseline, then updates the OK job's most
                  recent run history row to status=3 (Cancelled) instead of
                  1 (Succeeded) — the exact status BrightHive's watchdog
                  must learn to treat differently once Invariant 19 lands.

Usage:
    export MSSQL_SA_PASSWORD='...'
    python reset.py --scenario disk-pressure
    python reset.py --scenario type-drift --seed 99   # different RNG seed, same scenario
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass

SCENARIOS = ("baseline", "disk-pressure", "type-drift", "cancelled-run")


@dataclass(frozen=True)
class ResetConfig:
    scenario: str
    rng_seed: int
    row_count: int


def sqlcmd(*, database: str, query: str, password: str) -> str:
    """Runs one batch against the sandbox via docker exec — mirrors setup.sh's
    own SQLCMD invocation (same -C/-b flags) so this script fails loudly on a
    real SQL error instead of silently continuing, per the same fix applied
    to setup.sh after review."""
    result = subprocess.run(
        [
            "docker", "exec", "-i", "loopcapital-sql-sandbox",
            "/opt/mssql-tools18/bin/sqlcmd",
            "-S", "localhost", "-U", "sa", "-P", password, "-C", "-b",
            "-d", database, "-Q", query,
        ],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"sqlcmd failed (exit {result.returncode}) — see stderr above")
    return result.stdout


def run_sql_file_respecting_use(*, path: str, password: str, default_database: str = "master") -> None:
    """Runs a .sql file's GO-separated batches, switching database on each
    literal `USE <db>;` batch. Each batch is a SEPARATE docker exec process
    (no shared session across calls), so a `USE` in one batch has no effect
    on the next unless THIS function explicitly tracks it and passes -d per
    batch — confirmed the hard way: an earlier version that ran every batch
    against a single fixed database silently created holdings_raw in the
    wrong database, and sqlcmd's own -b strict-error-checking is what
    surfaced "Invalid object name" instead of failing silently."""
    with open(path) as f:
        content = f.read()
    current_db = default_database
    for batch in content.split("\nGO"):
        stripped = batch.strip()
        if not stripped:
            continue
        upper = stripped.upper().rstrip(";")
        if upper.startswith("USE "):
            current_db = upper.split(" ", 1)[1].strip()
            continue
        sqlcmd(database=current_db, query=batch, password=password)


def drop_and_recreate_database(*, password: str) -> None:
    """Ground zero for the DATA layer. Drops LoopCapitalAM if it exists (safe
    even in RECOVERY_PENDING — confirmed by direct test: DROP DATABASE cleanly
    removes an orphaned catalog entry whose underlying tmpfs files were wiped
    by a container restart, which is exactly what happens between sessions
    since LoopCapitalAM deliberately lives on the ephemeral tmpfs mount)."""
    print("Dropping LoopCapitalAM if it exists (ground zero)...")
    sqlcmd(
        database="master",
        query="IF EXISTS (SELECT name FROM sys.databases WHERE name = 'LoopCapitalAM') "
        "DROP DATABASE LoopCapitalAM;",
        password=password,
    )
    print("Recreating LoopCapitalAM + holdings_raw (fresh, per sql/01_create_database.sql)...")
    run_sql_file_respecting_use(path="sql/01_create_database.sql", password=password)


def seed_baseline(*, password: str, row_count: int, rng_seed: int) -> None:
    """Deterministic seed — same shape as sql/01_create_database.sql's own
    seed block, but parameterized here so --seed changes the RNG without
    editing the SQL file. Mirrors Longaeva sandbox/seed/seed.py's
    RNG_SEED convention."""
    print(f"Seeding {row_count} baseline rows (rng_seed={rng_seed})...")
    sqlcmd(
        database="LoopCapitalAM",
        query=f"""
        DECLARE @seed INT = {rng_seed};
        INSERT INTO holdings_raw (portfolio_id, instrument_id, quantity, as_of_date)
        SELECT
            'PORT-' + RIGHT('000' + CAST((n % 5) + 1 AS VARCHAR), 3),
            'INST-' + RIGHT('0000' + CAST(n AS VARCHAR), 4),
            1000.0 + (n * 12.5),
            DATEADD(DAY, -1 * (n % 30), CAST(SYSUTCDATETIME() AS DATE))
        FROM (SELECT TOP ({row_count}) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n
              FROM sys.all_objects) AS seq;
        """,
        password=password,
    )


def create_agent_jobs_and_wait(*, password: str, timeout_s: int = 60) -> None:
    """Every scenario needs GC-15's job-status data (validate.sh and any real
    watchdog dry run query it regardless of which scenario is active) — job
    creation used to live ONLY in the cancelled-run branch, silently leaving
    baseline/disk-pressure/type-drift with empty sysjobhistory (caught in
    review). sp_start_job is asynchronous, so this waits for both jobs to
    reach a step_id=0 history row before returning, mirroring the wait
    setup.sh used to do directly."""
    print("Creating SQL Server Agent jobs (mix of pass/fail, for GC-15's job-status query)...")
    run_sql_file_respecting_use(
        path="sql/02_create_agent_jobs.sql", password=password, default_database="msdb"
    )
    print("Waiting for both Agent jobs to reach a terminal history row...")
    elapsed = 0
    while True:
        output = sqlcmd(
            database="msdb",
            query="SET NOCOUNT ON; SELECT COUNT(DISTINCT j.job_id) FROM sysjobs j "
            "JOIN sysjobhistory h ON h.job_id = j.job_id WHERE h.step_id = 0 "
            "AND j.name IN ('LoopCapital_NightlyExtract_OK', 'LoopCapital_NightlyExtract_FAILED');",
            password=password,
        )
        # sqlcmd's default output includes a header row + a "---" separator
        # before the value — take the last non-empty, non-dash line rather
        # than assuming the whole output is bare (caught in review: an
        # earlier version compared the WHOLE multi-line output to "2",
        # which never matched and looped until the timeout every time).
        data_lines = [
            line.strip() for line in output.splitlines()
            if line.strip() and not line.strip().startswith("-")
        ]
        completed = data_lines[-1] if data_lines else ""
        if completed == "2":
            print("  Both jobs have a terminal history row.")
            return
        if elapsed >= timeout_s:
            raise RuntimeError(f"jobs did not complete within {timeout_s}s (completed={completed}/2)")
        time.sleep(2)
        elapsed += 2


def apply_scenario(*, config: ResetConfig, password: str) -> None:
    seed_baseline(password=password, row_count=config.row_count, rng_seed=config.rng_seed)
    create_agent_jobs_and_wait(password=password)

    if config.scenario == "baseline":
        return

    if config.scenario == "disk-pressure":
        print("Scenario 'disk-pressure' (GC-15): delegating to fill_disk.sh...")
        result = subprocess.run(["./fill_disk.sh"], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            raise RuntimeError("fill_disk.sh failed")
        return

    if config.scenario == "type-drift":
        print("Scenario 'type-drift' (GC-16): appending rows with quantity written as a "
              "string, simulating a NUMBER->FLOAT source-column drift...")
        # holdings_raw.quantity is DECIMAL(18,4) — a real drift would arrive
        # via SSIS writing a value the column can't natively hold without an
        # implicit conversion. This inserts a value that SUCCEEDS today
        # (DECIMAL accepts a numeric string) but fails once the demo's
        # "real" drift scenario narrows the column further — left here as
        # the seed hook GC-16's e2e test can extend once BH-1047 exists to
        # react to it; this script's job is producing the drifted ROW, not
        # simulating BH-1047's classification logic.
        sqlcmd(
            database="LoopCapitalAM",
            query="""
            INSERT INTO holdings_raw (portfolio_id, instrument_id, quantity, as_of_date)
            VALUES ('PORT-001', 'INST-DRIFT', CAST('99999.9999' AS DECIMAL(18,4)),
                    CAST(SYSUTCDATETIME() AS DATE));
            """,
            password=password,
        )
        return

    if config.scenario == "cancelled-run":
        print("Scenario 'cancelled-run' (GC-14): marking the OK job's latest run as "
              "Cancelled (status=3) instead of Succeeded...")
        sqlcmd(
            database="msdb",
            query="""
            UPDATE h SET h.run_status = 3
            FROM sysjobhistory h JOIN sysjobs j ON j.job_id = h.job_id
            WHERE j.name = 'LoopCapital_NightlyExtract_OK' AND h.step_id = 0
              AND h.instance_id = (
                SELECT MAX(instance_id) FROM sysjobhistory h2
                WHERE h2.job_id = h.job_id AND h2.step_id = 0
              );
            """,
            password=password,
        )
        return

    raise ValueError(f"Unknown scenario: {config.scenario}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", choices=SCENARIOS, default="baseline")
    parser.add_argument("--rows", type=int, default=2000, help="baseline row count (default: 2000)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for the baseline data (default: 42)")
    args = parser.parse_args()

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running reset.py", file=sys.stderr)
        return 1

    config = ResetConfig(scenario=args.scenario, rng_seed=args.seed, row_count=args.rows)

    drop_and_recreate_database(password=password)
    apply_scenario(config=config, password=password)

    print(f"\nReset complete — scenario '{config.scenario}' applied.")
    print("Run ./validate.sh (for disk-pressure) or query holdings_raw/sysjobhistory directly to confirm.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
