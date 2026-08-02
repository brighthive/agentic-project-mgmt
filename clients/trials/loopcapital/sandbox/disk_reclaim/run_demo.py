#!/usr/bin/env python3
"""End-to-end Loop Capital disk-reclaim demo, run against the REAL sandbox container.

The story, start to finish, every number read off sys.dm_os_volume_stats:

    1. MEASURE   baseline free % on the real tmpfs data volume
    2. BLOAT     nightly SSIS anti-pattern fills holdings_snapshot_raw → .mdf grows
    3. BREACH    the 70%-free monitor fires: disk pressure below the safe floor
    4. RECLAIM   great dbt code rebuilds the data deduped + narrow-typed + columnstore
    5. RELEASE   drop the raw heap + DBCC SHRINKFILE → real bytes returned to the volume
    6. OK        the same 70% monitor flips back to OK — space actually freed

Step 4 prefers real `dbt run` (dbt-sqlserver) if it's installed; otherwise it
applies the model's identical transformation via sqlcmd so the demo always runs
end to end. Either way the artifact of record is dbt/models/holdings_current.sql.

    export MSSQL_SA_PASSWORD='...'
    python run_demo.py --nights 40 --threshold 70
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from monitor import read_disk_verdict

_CONTAINER = "loopcapital-sql-sandbox"
_DATABASE = "LoopCapitalAM"
_HERE = Path(__file__).resolve().parent
_DBT_DIR = _HERE / "dbt"

# The reclaim, expressed as pure T-SQL — identical shape to holdings_current.sql,
# used only when dbt-sqlserver isn't installed so the demo still runs end to end.
_RECLAIM_SQL = """
SET NOCOUNT ON;
IF OBJECT_ID('dbo.holdings_current', 'U') IS NOT NULL DROP TABLE dbo.holdings_current;
WITH ranked AS (
    SELECT
        CAST(portfolio_id  AS VARCHAR(20))    AS portfolio_id,
        CAST(instrument_id AS VARCHAR(20))    AS instrument_id,
        CAST(quantity      AS DECIMAL(18, 4)) AS quantity,
        CAST(price         AS DECIMAL(18, 4)) AS price,
        CAST(market_value  AS DECIMAL(18, 4)) AS market_value,
        CAST(currency      AS VARCHAR(3))     AS currency,
        snapshot_date,
        ROW_NUMBER() OVER (PARTITION BY portfolio_id, instrument_id
                           ORDER BY snapshot_date DESC) AS recency_rank
    FROM dbo.holdings_snapshot_raw
)
SELECT portfolio_id, instrument_id, quantity, price, market_value, currency,
       snapshot_date AS as_of_date
INTO dbo.holdings_current
FROM ranked WHERE recency_rank = 1;
CREATE CLUSTERED COLUMNSTORE INDEX cci_holdings_current ON dbo.holdings_current;
"""

# Drop the wasteful heap and hand the freed pages back to the OS. On a tmpfs
# volume the SHRINKFILE is what makes sys.dm_os_volume_stats report the space
# as available again — the reclaim is only real once the file gives bytes back.
_RELEASE_SQL = """
SET NOCOUNT ON;
IF OBJECT_ID('dbo.holdings_snapshot_raw', 'U') IS NOT NULL DROP TABLE dbo.holdings_snapshot_raw;
DECLARE @f SYSNAME = (SELECT name FROM sys.database_files WHERE type_desc = 'ROWS');
DBCC SHRINKFILE (@f, 10) WITH NO_INFOMSGS;
CHECKPOINT;
"""


def sqlcmd(*, query: str, password: str) -> str:
    result = subprocess.run(
        [
            "docker", "exec", "-i", _CONTAINER,
            "/opt/mssql-tools18/bin/sqlcmd",
            "-S", "localhost", "-U", "sa", "-P", password, "-C", "-b",
            "-d", _DATABASE, "-Q", query,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"sqlcmd failed (exit {result.returncode})")
    return result.stdout


def report(*, label: str, password: str, threshold: float) -> float:
    verdict = read_disk_verdict(password=password, threshold_pct=threshold)
    icon = "🚨" if verdict.breached else "✅"
    print(f"  {icon} {label}: {verdict.percent_free}% free "
          f"({verdict.free_mib} MiB of {verdict.total_mib} MiB) → {verdict.status}")
    return verdict.percent_free


def _dbt_binary() -> str | None:
    """Prefer the sandbox venv's dbt (dbt-core + dbt-sqlserver) over any dbt on PATH.

    The dbt on a dev machine's PATH is often the dbt Cloud CLI, which can't run a
    local sqlserver profile. The venv created by `make -C .. reclaim-setup` (or the
    README steps) holds dbt-core 1.12 + dbt-sqlserver 1.10 — that's the one that runs.
    """
    venv_dbt = _HERE / ".venv" / "bin" / "dbt"
    if venv_dbt.exists():
        return str(venv_dbt)
    on_path = shutil.which("dbt")
    return on_path


def run_reclaim(*, password: str) -> None:
    """Prefer real `dbt run` (dbt-sqlserver); fall back to the identical T-SQL transform."""
    dbt = _dbt_binary()
    if dbt:
        # dbt owns holdings_current end to end (drop + rebuild + columnstore), so a
        # stale copy from a prior fallback run must not block the CCI build.
        sqlcmd(query="IF OBJECT_ID('dbo.holdings_current','U') IS NOT NULL DROP TABLE dbo.holdings_current;",
               password=password)
        env = {**os.environ, "DBT_PROFILES_DIR": str(_DBT_DIR)}
        proc = subprocess.run(
            [dbt, "run", "--select", "holdings_current", "--project-dir", str(_DBT_DIR)],
            env=env, capture_output=True, text=True,
        )
        if proc.returncode == 0:
            print(f"  ✅ reclaim via `dbt run` (dbt-sqlserver) — {dbt}")
            return
        tail = (proc.stdout.strip().splitlines() or ["<no output>"])[-1]
        print("  ⚠️  dbt run failed, applying the model's T-SQL directly:")
        print("     " + tail)
    else:
        print("  ℹ️  dbt not found — applying the model's identical T-SQL transform")
    sqlcmd(query=_RECLAIM_SQL, password=password)
    print("  ✅ reclaim applied (holdings_current rebuilt, deduped + columnstore)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nights", type=int, default=40, help="nightly snapshots to bloat with")
    parser.add_argument("--threshold", type=float, default=70.0, help="free-space floor percent")
    args = parser.parse_args()

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running run_demo.py", file=sys.stderr)
        return 2

    print("\n=== Loop Capital disk-reclaim demo (real sandbox volume) ===\n")

    print("1. MEASURE baseline")
    baseline = report(label="baseline", password=password, threshold=args.threshold)

    print(f"\n2. BLOAT — appending {args.nights} nightly SSIS snapshots")
    subprocess.run([sys.executable, str(_HERE / "seed_bloat.py"), "--nights", str(args.nights)],
                   check=True, env={**os.environ})

    print("\n3. MONITOR after bloat")
    pressured = report(label="after bloat", password=password, threshold=args.threshold)

    print("\n4. RECLAIM — great dbt code rebuilds the data")
    run_reclaim(password=password)

    print("\n5. RELEASE — drop raw heap + DBCC SHRINKFILE")
    sqlcmd(query=_RELEASE_SQL, password=password)

    print("\n6. MONITOR after reclaim")
    reclaimed = report(label="after reclaim", password=password, threshold=args.threshold)

    print("\n=== Result ===")
    print(f"  baseline free:      {baseline:.2f}%")
    print(f"  under bloat:        {pressured:.2f}%  ({'BREACH' if pressured < args.threshold else 'OK'})")
    print(f"  after dbt reclaim:  {reclaimed:.2f}%  ({'BREACH' if reclaimed < args.threshold else 'OK'})")
    print(f"  space reclaimed:    {reclaimed - pressured:+.2f} percentage points free\n")
    if pressured < args.threshold <= reclaimed:
        print("  ✅ 70% monitor flipped BREACH → OK. dbt reclaim freed real disk.\n")
        return 0
    print("  ⚠️  monitor did not flip as expected — raise --nights to build more pressure.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
