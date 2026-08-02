#!/usr/bin/env python3
"""70%-free disk-space monitor for the Loop Capital SQL Server sandbox.

Reads REAL free space off the mounted data volume via sys.dm_os_volume_stats
(the same DMV BH-1045's watchdog uses — brightbot/tools/warehouse_connections.py
SynapseConnection path), compares it to a free-space floor (default 70%), and
emits an OK / BREACH verdict. Nothing here is fabricated: the number is whatever
the real tmpfs mount reports, so filling the .mdf drops it and shrinking the
.mdf raises it — exactly what the reclaim demo proves end to end.

    export MSSQL_SA_PASSWORD='...'
    python monitor.py                 # 70% floor (Frank's named threshold)
    python monitor.py --threshold 70  # explicit
    python monitor.py --json          # machine-readable, for a watchdog dry run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass

_CONTAINER = "loopcapital-sql-sandbox"
_DATABASE = "LoopCapitalAM"
_DEFAULT_FREE_FLOOR_PCT = 70.0

# One row per data/log file on the mounted volume — the real watchdog query.
_VOLUME_STATS_SQL = (
    "SET NOCOUNT ON; "
    "SELECT TOP 1 "
    "  CAST(vs.available_bytes * 100.0 / vs.total_bytes AS DECIMAL(5,2)), "
    "  vs.total_bytes / 1024 / 1024, "
    "  vs.available_bytes / 1024 / 1024 "
    "FROM sys.master_files AS mf "
    "CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs "
    "WHERE DB_NAME(mf.database_id) = '" + _DATABASE + "';"
)


@dataclass(frozen=True)
class DiskVerdict:
    percent_free: float
    total_mib: int
    free_mib: int
    threshold_pct: float

    @property
    def breached(self) -> bool:
        return self.percent_free < self.threshold_pct

    @property
    def status(self) -> str:
        return "BREACH" if self.breached else "OK"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "percent_free": self.percent_free,
            "threshold_pct": self.threshold_pct,
            "free_mib": self.free_mib,
            "total_mib": self.total_mib,
            "used_mib": self.total_mib - self.free_mib,
            "database": _DATABASE,
        }


def read_disk_verdict(*, password: str, threshold_pct: float) -> DiskVerdict:
    """Runs the real sys.dm_os_volume_stats query and shapes an OK/BREACH verdict."""
    result = subprocess.run(
        [
            "docker", "exec", "-i", _CONTAINER,
            "/opt/mssql-tools18/bin/sqlcmd",
            "-S", "localhost", "-U", "sa", "-P", password, "-C",
            "-d", _DATABASE, "-h", "-1", "-W", "-s", ",", "-Q", _VOLUME_STATS_SQL,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"volume-stats query failed (exit {result.returncode}): {result.stderr.strip()}")

    row = next(
        (ln.strip() for ln in result.stdout.splitlines()
         if ln.strip() and "," in ln and not ln.strip().startswith("-")),
        "",
    )
    parts = [p.strip() for p in row.split(",")]
    if len(parts) < 3:
        raise RuntimeError(f"could not parse volume-stats output: {result.stdout!r}")

    return DiskVerdict(
        percent_free=float(parts[0]),
        total_mib=int(parts[1]),
        free_mib=int(parts[2]),
        threshold_pct=threshold_pct,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--threshold", type=float, default=_DEFAULT_FREE_FLOOR_PCT,
                        help=f"free-space floor as a percent (default: {_DEFAULT_FREE_FLOOR_PCT})")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running monitor.py", file=sys.stderr)
        return 2

    verdict = read_disk_verdict(password=password, threshold_pct=args.threshold)

    if args.json:
        print(json.dumps(verdict.to_dict(), indent=2))
    else:
        icon = "🚨" if verdict.breached else "✅"
        print(
            f"{icon} {verdict.status}: {_DATABASE} volume is {verdict.percent_free}% free "
            f"({verdict.free_mib} MiB free of {verdict.total_mib} MiB) "
            f"— floor is {verdict.threshold_pct:.0f}% free."
        )
        if verdict.breached:
            print("   Disk pressure below the safe floor — a reclaim (dbt rebuild + shrink) is warranted.")

    # Exit code doubles as the watchdog signal: 0 = OK, 1 = BREACH.
    return 1 if verdict.breached else 0


if __name__ == "__main__":
    raise SystemExit(main())
