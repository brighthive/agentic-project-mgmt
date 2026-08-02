#!/usr/bin/env python3
"""Seeds a realistic disk-waste anti-pattern into LoopCapitalAM, so the reclaim
demo has REAL bytes to reclaim off the real tmpfs data volume.

The story (a genuine legacy asset-management smell, not a fabricated filler):
the nightly SSIS extract APPENDS a full denormalized snapshot of every holding
every night into one wide, uncompressed heap — `holdings_snapshot_raw`. Nothing
dedups it, columns are oversized (NVARCHAR(4000) for short codes, a redundant
`snapshot_json` blob per row), and there is no index or compression. After N
nights this table is the single biggest consumer on the volume — the exact
pattern that quietly fills a legacy SQL Server box.

`dbt/models/holdings_current.sql` is what reclaims it: one deduplicated,
narrowly-typed, columnstore-compressed model keeping only the latest snapshot
per (portfolio, instrument). Dropping the raw heap after the rebuild + a
SHRINKFILE releases the bytes back to the volume — visible in monitor.py.

    export MSSQL_SA_PASSWORD='...'
    python seed_bloat.py --nights 40      # ~40 nightly snapshots of the holdings book
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

_CONTAINER = "loopcapital-sql-sandbox"
_DATABASE = "LoopCapitalAM"

# The wide, redundant heap the nightly SSIS extract appends to. Deliberately
# oversized types + a per-row JSON blob — the waste the reclaim removes.
_CREATE_BLOAT_TABLE = """
SET NOCOUNT ON;
IF OBJECT_ID('dbo.holdings_snapshot_raw', 'U') IS NOT NULL
    DROP TABLE dbo.holdings_snapshot_raw;
CREATE TABLE dbo.holdings_snapshot_raw (
    snapshot_id     BIGINT IDENTITY PRIMARY KEY,
    snapshot_date   DATE            NOT NULL,
    portfolio_id    NVARCHAR(4000)  NOT NULL,   -- oversized: real code is <= 20 chars
    instrument_id   NVARCHAR(4000)  NOT NULL,   -- oversized
    quantity        DECIMAL(38, 10) NOT NULL,   -- over-wide precision
    price           DECIMAL(38, 10) NOT NULL,
    market_value    DECIMAL(38, 10) NOT NULL,
    currency        NVARCHAR(4000)  NOT NULL,
    custodian       NVARCHAR(4000)  NOT NULL,
    snapshot_json   NVARCHAR(MAX)   NOT NULL,   -- redundant per-row blob: pure waste
    loaded_at       DATETIME2       NOT NULL DEFAULT SYSUTCDATETIME()
);
"""

# One night's append: a full snapshot of every holding, padded with the
# redundant JSON blob. Runs entirely server-side (no row-by-row round trips).
_APPEND_ONE_NIGHT = """
SET NOCOUNT ON;
DECLARE @night INT = {night};
INSERT INTO dbo.holdings_snapshot_raw
    (snapshot_date, portfolio_id, instrument_id, quantity, price, market_value,
     currency, custodian, snapshot_json)
SELECT
    DATEADD(DAY, -@night, CAST(SYSUTCDATETIME() AS DATE)),
    h.portfolio_id, h.instrument_id, h.quantity,
    100.0 + (h.holding_id % 400) * 0.25,
    h.quantity * (100.0 + (h.holding_id % 400) * 0.25),
    'USD', 'STATE STREET CUSTODY / NORTHERN TRUST',
    -- redundant blob repeated per row per night: the disk hog
    REPLICATE(
      CAST('{{"src":"nightly_ssis_extract","portfolio":"' + h.portfolio_id
        + '","instrument":"' + h.instrument_id
        + '","note":"full denormalized snapshot row, no dedup, retained forever"}}'
        AS NVARCHAR(MAX)), 8)
FROM dbo.holdings_raw AS h;
"""


def sqlcmd(*, query: str, password: str, database: str = _DATABASE) -> str:
    result = subprocess.run(
        [
            "docker", "exec", "-i", _CONTAINER,
            "/opt/mssql-tools18/bin/sqlcmd",
            "-S", "localhost", "-U", "sa", "-P", password, "-C", "-b",
            "-d", database, "-Q", query,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"sqlcmd failed (exit {result.returncode})")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nights", type=int, default=40,
                        help="how many nightly full-snapshot appends to simulate (default: 40)")
    args = parser.parse_args()

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running seed_bloat.py", file=sys.stderr)
        return 2

    print(f"Creating dbo.holdings_snapshot_raw and appending {args.nights} nightly snapshots...")
    sqlcmd(query=_CREATE_BLOAT_TABLE, password=password)
    for night in range(1, args.nights + 1):
        sqlcmd(query=_APPEND_ONE_NIGHT.format(night=night), password=password)
        if night % 10 == 0:
            print(f"  ...{night}/{args.nights} nights appended")

    # Grow the .mdf to hold what we just wrote (tmpfs shows real pressure only
    # once the data file actually claims the pages).
    summary = sqlcmd(
        query=(
            "SET NOCOUNT ON; "
            "SELECT COUNT(*) AS rows_in_raw FROM dbo.holdings_snapshot_raw; "
            "SELECT CAST(SUM(size) * 8.0 / 1024 AS DECIMAL(10,1)) AS mdf_mib "
            "FROM sys.database_files WHERE type_desc = 'ROWS';"
        ),
        password=password,
    )
    print(summary)
    print("Bloat seeded. Run ../disk_reclaim/monitor.py to see the volume breach the 70% floor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
