#!/usr/bin/env python3
"""Introspect OUR OWN sandbox container into a schema manifest (BH-1404, local path).

Reads `INFORMATION_SCHEMA.COLUMNS` + `sys.columns` (identity/computed) + primary-key metadata
from the running `LoopCapitalAM` container and writes a faithful `schema_manifest.json`. This is
the dev-bootstrap + round-trip-proof path: it produces the committed manifest from a REAL backend
(never hand-typed — see test-behavior-real.md), and lets `synthesize.py` rebuild the same shape.

It reads only from the local Brighthive-owned container (source=local-introspect). It NEVER
connects to Loop Capital's real on-prem server — that is what `capture_from_staging.py` guards
against with the staging GraphQL path (source=staging). See INV-11.

Usage (container already up via ../setup.sh):
    export MSSQL_SA_PASSWORD='<throwaway-local-password>'
    uv run --with pymssql --with pydantic python \\
        clients/trials/loopcapital/sandbox/manifest/introspect_local.py
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path
from typing import Final

import pymssql

from manifest_model import (
    SANDBOX_DATABASE,
    CaptureSource,
    ColumnSpec,
    KeyRole,
    SchemaManifest,
    TableSpec,
    dump_manifest,
)

MANIFEST_PATH: Final[Path] = Path(__file__).resolve().parent.parent / "schema_manifest.json"

DEFAULT_HOST: Final[str] = "127.0.0.1"  # NOT localhost — IPv6 ::1 stalls TLS on the emulated container
DEFAULT_PORT: Final[int] = 1433

# SQL Server types that carry a (length) — reconstructed from CHARACTER_MAXIMUM_LENGTH.
_LENGTH_TYPES: Final[frozenset[str]] = frozenset({"char", "varchar", "nchar", "nvarchar", "binary", "varbinary"})
# SQL Server types that carry (precision, scale) — reconstructed from NUMERIC_PRECISION/SCALE.
_PRECISION_TYPES: Final[frozenset[str]] = frozenset({"decimal", "numeric"})
_MAX_LENGTH_SENTINEL: Final[int] = -1  # INFORMATION_SCHEMA reports -1 for VARCHAR(MAX)


def reconstruct_sql_type(
    *, data_type: str, char_len: int | None, precision: int | None, scale: int | None
) -> str:
    """Rebuild the full SQL type string (with length/precision) from INFORMATION_SCHEMA parts."""
    base = data_type.lower()
    if base in _LENGTH_TYPES:
        if char_len == _MAX_LENGTH_SENTINEL:
            return f"{data_type.upper()}(MAX)"
        return f"{data_type.upper()}({char_len})" if char_len is not None else data_type.upper()
    if base in _PRECISION_TYPES and precision is not None:
        return f"{data_type.upper()}({precision},{scale or 0})"
    return data_type.upper()


def fetch_column_flags(*, cursor: pymssql.Cursor) -> dict[tuple[str, str, str], tuple[bool, bool]]:
    """(schema, table, column) -> (is_identity, is_computed) for every user-table column."""
    cursor.execute(
        "SELECT SCHEMA_NAME(t.schema_id), t.name, c.name, c.is_identity, c.is_computed "
        "FROM sys.tables t JOIN sys.columns c ON c.object_id = t.object_id"
    )
    return {(row[0], row[1], row[2]): (bool(row[3]), bool(row[4])) for row in cursor.fetchall()}


def fetch_primary_key_columns(*, cursor: pymssql.Cursor) -> set[tuple[str, str, str]]:
    """(schema, table, column) tuples that participate in a primary key."""
    cursor.execute(
        "SELECT SCHEMA_NAME(t.schema_id), t.name, c.name "
        "FROM sys.indexes i "
        "JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id "
        "JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id "
        "JOIN sys.tables t ON t.object_id = i.object_id "
        "WHERE i.is_primary_key = 1"
    )
    return {(row[0], row[1], row[2]) for row in cursor.fetchall()}


def fetch_row_estimates(*, cursor: pymssql.Cursor) -> dict[tuple[str, str], int]:
    """(schema, table) -> estimated row count from partition stats — a number, never row data."""
    cursor.execute(
        "SELECT SCHEMA_NAME(t.schema_id), t.name, SUM(p.rows) "
        "FROM sys.tables t JOIN sys.partitions p ON p.object_id = t.object_id "
        "WHERE p.index_id IN (0, 1) GROUP BY SCHEMA_NAME(t.schema_id), t.name"
    )
    return {(row[0], row[1]): int(row[2] or 0) for row in cursor.fetchall()}


def introspect(*, host: str, port: int, password: str, database: str) -> SchemaManifest:
    """Read the running container's schema into a faithful, typed manifest."""
    conn = pymssql.connect(host, "sa", password, database, port=port, timeout=60)
    cursor = conn.cursor()

    flags = fetch_column_flags(cursor=cursor)
    pk_columns = fetch_primary_key_columns(cursor=cursor)
    row_estimates = fetch_row_estimates(cursor=cursor)

    # Base tables only (exclude views), ordered for a deterministic, diff-stable manifest.
    cursor.execute(
        "SELECT c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, "
        "c.CHARACTER_MAXIMUM_LENGTH, c.NUMERIC_PRECISION, c.NUMERIC_SCALE, c.IS_NULLABLE "
        "FROM INFORMATION_SCHEMA.COLUMNS c "
        "JOIN INFORMATION_SCHEMA.TABLES t "
        "  ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME "
        "WHERE t.TABLE_TYPE = 'BASE TABLE' "
        "ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION"
    )

    tables: dict[str, TableSpec] = {}
    for schema, table, column, data_type, char_len, precision, scale, is_nullable in cursor.fetchall():
        qualified = f"{schema}.{table}"
        identity, computed = flags.get((schema, table, column), (False, False))
        column_spec = ColumnSpec(
            name=column,
            sql_type=reconstruct_sql_type(
                data_type=data_type, char_len=char_len, precision=precision, scale=scale
            ),
            nullable=(is_nullable == "YES"),
            key=KeyRole.PRIMARY if (schema, table, column) in pk_columns else KeyRole.NONE,
            identity=identity,
            computed=computed,
        )
        if qualified not in tables:
            tables[qualified] = TableSpec(
                name=qualified, columns=[], row_estimate=row_estimates.get((schema, table), 0)
            )
        tables[qualified].columns.append(column_spec)

    conn.close()

    return SchemaManifest(
        captured_at=datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        source=CaptureSource.LOCAL_INTROSPECT,
        database=database,
        tables=[tables[name] for name in sorted(tables)],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=MANIFEST_PATH, help="output manifest path")
    parser.add_argument("--database", default=SANDBOX_DATABASE, help=f"database to introspect (default: {SANDBOX_DATABASE})")
    args = parser.parse_args()

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running introspect_local.py", file=sys.stderr)
        return 1

    host = os.environ.get("MSSQL_HOST", DEFAULT_HOST)
    port = int(os.environ.get("MSSQL_PORT", str(DEFAULT_PORT)))

    manifest = introspect(host=host, port=port, password=password, database=args.database)
    dump_manifest(manifest=manifest, path=args.out)

    total_columns = sum(len(t.columns) for t in manifest.tables)
    print(f"Introspected {manifest.database} -> {args.out}")
    print(f"  {len(manifest.tables)} tables, {total_columns} columns, source={manifest.source.value}")
    for table in manifest.tables:
        pk = ", ".join(c.name for c in table.columns if c.key is KeyRole.PRIMARY) or "—"
        print(f"    {table.name}: {len(table.columns)} cols, pk=({pk}), ~{table.row_estimate} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
