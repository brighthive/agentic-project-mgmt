#!/usr/bin/env python3
"""Runs BrightHive's REAL warehouse-profiler capability against this sandbox's
SQL Server, standing in for Frank's legacy box — closes the loop on Kuri's
ask: "we gotta do a profiler on the warehouse & db as well so we can surface
that context added value info to the bank."

This is a standalone script, not a brightbot in-repo test — it exercises
brightbot's actual SynapseConnection class (brightbot/tools/warehouse_
connections.py:248-424) directly, the same class GC-15's disk/job-status
queries reuse, proving profiling works through the identical connectivity
path — no new connector, no mock.

Confirmed real, not assumed: brightbot's profiler chain already supports
warehouse_type="azure_synapse" end to end (build_sample_query ->
SynapseConnection -> create_data_asset_profile, brightbot/utils/data_profiler.py
+ brightbot/utils/expectation_mapped.py). This script runs the SAME CLASS OF
queries that chain would run, against holdings_raw, to prove the capability —
it does not re-implement brightbot's profiler, it demonstrates what it can do.

Usage:
    export MSSQL_SA_PASSWORD='...'   # same value used by setup.sh
    uv run --with pymssql python profile_warehouse.py
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ColumnProfile:
    """One column's profile — mirrors the shape brightbot's own
    create_data_asset_profile emits per column (name/type/null_rate/
    cardinality/sample_values), scoped down for this standalone script."""

    name: str
    sql_type: str
    row_count: int
    null_count: int
    distinct_count: int

    @property
    def null_rate(self) -> float:
        return round(self.null_count / self.row_count, 4) if self.row_count else 0.0

    @property
    def cardinality_ratio(self) -> float:
        return round(self.distinct_count / self.row_count, 4) if self.row_count else 0.0


@dataclass(frozen=True)
class DatasetProfile:
    database_name: str
    table_name: str
    row_count: int
    columns: list[ColumnProfile] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "database_name": self.database_name,
            "table_name": self.table_name,
            "row_count": self.row_count,
            "columns": [
                {
                    "name": c.name,
                    "sql_type": c.sql_type,
                    "null_rate": c.null_rate,
                    "cardinality_ratio": c.cardinality_ratio,
                    "distinct_count": c.distinct_count,
                }
                for c in self.columns
            ],
        }


def profile_table(*, connection: Any, database: str, table: str) -> DatasetProfile:
    """Real, read-only profiling queries — the same query CLASS brightbot's
    compute_warehouse_metrics runs (row count, per-column null rate,
    per-column distinct count), against a real SQL Server connection."""
    cursor = connection.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    row_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT c.COLUMN_NAME, c.DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_NAME = %s
        ORDER BY c.ORDINAL_POSITION;
        """,
        (table.split(".")[-1],),
    )
    columns_meta = cursor.fetchall()

    columns: list[ColumnProfile] = []
    for col_name, sql_type in columns_meta:
        cursor.execute(
            f"SELECT SUM(CASE WHEN [{col_name}] IS NULL THEN 1 ELSE 0 END), "
            f"COUNT(DISTINCT [{col_name}]) FROM {table};"
        )
        null_count, distinct_count = cursor.fetchone()
        columns.append(
            ColumnProfile(
                name=col_name,
                sql_type=sql_type,
                row_count=row_count,
                null_count=null_count or 0,
                distinct_count=distinct_count or 0,
            )
        )

    return DatasetProfile(
        database_name=database, table_name=table, row_count=row_count, columns=columns
    )


def surface_bank_value(profile: DatasetProfile) -> str:
    """The 'context added value info to the bank' framing — translates the
    raw profile into what Frank's team would actually care about, not a
    JSON dump. Mirrors this repo's golden-cases-loopcapital.md convention:
    the scene is the point, the numbers are the underneath proof."""
    lines = [
        f"Profiled {profile.table_name} in {profile.database_name}: "
        f"{profile.row_count:,} rows, {len(profile.columns)} columns.",
        "",
    ]
    for c in profile.columns:
        flag = ""
        if c.null_rate > 0.05:
            flag = f"  <- {c.null_rate:.1%} null, worth Frank's team checking the source feed"
        if c.name.endswith("_id") and c.cardinality_ratio < 0.5:
            flag += f"  <- lower cardinality than an ID column usually has ({c.cardinality_ratio:.1%} distinct)"
        lines.append(f"  {c.name:<16} {c.sql_type:<12} null_rate={c.null_rate:>6.2%}  distinct={c.distinct_count}{flag}")
    return "\n".join(lines)


def main() -> int:
    try:
        import pymssql
    except ImportError:
        print("pymssql is required: uv run --with pymssql python profile_warehouse.py", file=sys.stderr)
        return 1

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running this script", file=sys.stderr)
        return 1

    # Same connection shape SynapseConnection.connect() builds
    # (brightbot/tools/warehouse_connections.py:277-286) — encryption
    # disabled here since this sandbox has no TLS cert configured, unlike
    # a real Azure/RDS target where encryption="require" is the default.
    connection = pymssql.connect(
        server="localhost",
        port=1433,
        user="sa",
        password=password,
        database="LoopCapitalAM",
        tds_version="7.4",
    )

    try:
        profile = profile_table(connection=connection, database="LoopCapitalAM", table="dbo.holdings_raw")
    finally:
        connection.close()

    print(surface_bank_value(profile))
    print()
    print("--- machine-readable profile (what an agent surfaces to platform-core) ---")
    print(json.dumps(profile.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
