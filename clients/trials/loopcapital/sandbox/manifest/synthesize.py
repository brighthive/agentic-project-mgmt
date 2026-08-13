#!/usr/bin/env python3
"""Deterministic synthetic-data generator for the Loop Capital sandbox (BH-1406).

Reads a committed `schema_manifest.json`, rebuilds the manifest's tables as faithful
`CREATE TABLE` DDL, and seeds them with deterministic, per-type synthetic rows. Same manifest +
same `--seed` -> byte-identical database every time (git-only reproducibility, INV-10). No real
Loop Capital rows are ever produced or committed (INV-9); every value is synthesized from the RNG.

Manifest mode owns the whole `LoopCapitalAM` database while active: this drops and recreates it so
a recreate is always pristine. It does not run alongside scenario mode (`reset.py`).

Usage (run from repo root; the container must already be up):
    export MSSQL_SA_PASSWORD='<throwaway-local-password>'
    uv run --with pymssql --with pydantic python \\
        clients/trials/loopcapital/sandbox/manifest/synthesize.py --rows 200 --seed 42
"""

from __future__ import annotations

import argparse
import datetime
import os
import random
import sys
from decimal import Decimal
from pathlib import Path
from typing import Final

import pymssql

from manifest_model import (
    ColumnSpec,
    KeyRole,
    SchemaManifest,
    TableSpec,
    load_manifest,
)

MANIFEST_PATH: Final = Path(__file__).resolve().parent.parent / "schema_manifest.json"

DEFAULT_HOST: Final[str] = "127.0.0.1"  # NOT localhost — IPv6 ::1 stalls TLS on the emulated container
DEFAULT_PORT: Final[int] = 1433
DEFAULT_ROWS: Final[int] = 200
DEFAULT_SEED: Final[int] = 42
INSERT_BATCH: Final[int] = 500
NULL_FRACTION: Final[float] = 0.08  # deterministic fraction of nullable cells left NULL

# SQL Server type families — drives per-column value synthesis.
_INT_TYPES: Final[frozenset[str]] = frozenset({"int", "bigint", "smallint", "tinyint"})
_REAL_TYPES: Final[frozenset[str]] = frozenset({"decimal", "numeric", "float", "real", "money", "smallmoney"})
_DATE_TYPES: Final[frozenset[str]] = frozenset({"date"})
_DATETIME_TYPES: Final[frozenset[str]] = frozenset({"datetime2", "datetime", "smalldatetime", "datetimeoffset"})
_STRING_TYPES: Final[frozenset[str]] = frozenset({"char", "varchar", "nchar", "nvarchar", "text", "ntext"})


def _base_type(sql_type: str) -> str:
    """The bare SQL type name, lowercased, without length/precision (e.g. 'DECIMAL(18,4)' -> 'decimal')."""
    return sql_type.split("(", 1)[0].strip().lower()


def _string_length(sql_type: str) -> int:
    """Declared length of a string type, capped for synthesis (MAX/-1 -> a sane cap)."""
    if "(" not in sql_type:
        return 32
    inner = sql_type[sql_type.index("(") + 1 : sql_type.rindex(")")].strip().lower()
    if inner in {"max", "-1"}:
        return 200
    try:
        return max(1, int(inner.split(",")[0]))
    except ValueError:
        return 32


def _decimal_precision(sql_type: str) -> tuple[int, int]:
    """(precision, scale) for a decimal/numeric type; sensible defaults for float/money."""
    base = _base_type(sql_type)
    if base in {"float", "real"}:
        return (15, 4)
    if base in {"money", "smallmoney"}:
        return (18, 2)
    if "(" not in sql_type:
        return (18, 0)
    inner = sql_type[sql_type.index("(") + 1 : sql_type.rindex(")")]
    parts = [p.strip() for p in inner.split(",")]
    precision = int(parts[0])
    scale = int(parts[1]) if len(parts) > 1 else 0
    return (precision, scale)


def synth_value(*, column: ColumnSpec, rng: random.Random, row_index: int) -> object:
    """Deterministic synthetic value for one column/row, honoring type, nullability, and PK uniqueness."""
    base = _base_type(column.sql_type)
    is_pk = column.key is KeyRole.PRIMARY

    # Nullable non-key columns occasionally NULL — deterministic via the seeded RNG.
    if column.nullable and not is_pk and rng.random() < NULL_FRACTION:
        return None

    if base in _INT_TYPES:
        return row_index if is_pk else rng.randint(1, 1_000_000)

    if base in _REAL_TYPES:
        precision, scale = _decimal_precision(column.sql_type)
        whole_digits = max(1, precision - scale)
        upper = min(10 ** whole_digits - 1, 1_000_000)
        value = Decimal(rng.randint(0, int(upper))) + (Decimal(rng.randint(0, 9999)) / Decimal(10_000))
        return value.quantize(Decimal(1).scaleb(-scale)) if scale else value.quantize(Decimal(1))

    if base in _DATE_TYPES:
        return datetime.date(2026, 1, 1) + datetime.timedelta(days=rng.randint(0, 364))

    if base in _DATETIME_TYPES:
        return datetime.datetime(2026, 1, 1) + datetime.timedelta(
            days=rng.randint(0, 364), seconds=rng.randint(0, 86_399)
        )

    if base == "bit":
        return rng.randint(0, 1)

    if base == "uniqueidentifier":
        return "{:08x}-0000-4000-8000-{:012x}".format(rng.getrandbits(32), row_index)

    if base in _STRING_TYPES:
        length = _string_length(column.sql_type)
        if is_pk:
            token = f"{column.name.upper()[:6]}-{row_index:08d}"
            return token[:length]
        body = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(min(length, 12)))
        return body[:length]

    # Unknown/uncovered type — a short deterministic string keeps the insert honest and visible.
    return f"SYN-{row_index:06d}"


def _seedable_columns(table: TableSpec) -> list[ColumnSpec]:
    """Columns we write on INSERT — everything except IDENTITY columns (the engine owns those)."""
    return [c for c in table.columns if not c.identity]


def render_create_table(*, table: TableSpec) -> str:
    """Faithful CREATE TABLE from the manifest: types, nullability, IDENTITY, single-column PK.

    Computed columns are materialized as plain columns of their captured type (documented
    simplification — a shape sandbox needs the column present and typed, not the expression).
    Foreign keys are not enforced; synthetic rows are shape-faithful, not referentially linked.
    """
    lines: list[str] = []
    for column in table.columns:
        identity = " IDENTITY(1,1)" if column.identity else ""
        null = "NOT NULL" if not column.nullable else "NULL"
        lines.append(f"    [{column.name}] {column.sql_type}{identity} {null}")
    pk_cols = [c.name for c in table.columns if c.key is KeyRole.PRIMARY]
    if pk_cols:
        lines.append("    PRIMARY KEY (" + ", ".join(f"[{c}]" for c in pk_cols) + ")")
    body = ",\n".join(lines)
    return f"CREATE TABLE [{table.schema_name}].[{table.bare_name}] (\n{body}\n);"


def recreate_database(*, host: str, port: int, password: str, database: str) -> None:
    """Drop and recreate the target database for a pristine, deterministic manifest-mode rebuild."""
    conn = pymssql.connect(host, "sa", password, "master", port=port, timeout=60)
    conn.autocommit(True)
    cur = conn.cursor()
    cur.execute(
        "IF EXISTS (SELECT name FROM sys.databases WHERE name = %s) "
        "BEGIN ALTER DATABASE [" + database + "] SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
        "DROP DATABASE [" + database + "]; END",
        (database,),
    )
    cur.execute(f"CREATE DATABASE [{database}];")
    conn.close()
    print(f"  Database {database} dropped + recreated (ground zero).")


def apply_schema_and_seed(
    *, host: str, port: int, password: str, manifest: SchemaManifest, rows: int, seed: int
) -> int:
    """Create every manifest table and seed deterministic rows; returns total rows inserted."""
    conn = pymssql.connect(host, "sa", password, manifest.database, port=port, timeout=120)
    conn.autocommit(True)
    cur = conn.cursor()
    total_inserted = 0

    for table_index, table in enumerate(manifest.tables):
        cur.execute(
            f"IF OBJECT_ID('[{table.schema_name}].[{table.bare_name}]', 'U') IS NOT NULL "
            f"DROP TABLE [{table.schema_name}].[{table.bare_name}];"
        )
        cur.execute(render_create_table(table=table))

        columns = _seedable_columns(table)
        if not columns:
            print(f"  {table.name}: schema only (all columns IDENTITY).")
            continue

        col_list = ", ".join(f"[{c.name}]" for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = (
            f"INSERT INTO [{table.schema_name}].[{table.bare_name}] ({col_list}) VALUES ({placeholders})"
        )

        rng = random.Random(f"{seed}:{table.name}")  # table-scoped, so order-independent + deterministic
        batch: list[tuple[object, ...]] = []
        inserted = 0
        for row_index in range(rows):
            batch.append(tuple(synth_value(column=c, rng=rng, row_index=row_index) for c in columns))
            if len(batch) >= INSERT_BATCH:
                cur.executemany(insert_sql, batch)
                inserted += len(batch)
                batch = []
        if batch:
            cur.executemany(insert_sql, batch)
            inserted += len(batch)

        total_inserted += inserted
        print(f"  {table.name}: {inserted} rows.")

    conn.close()
    return total_inserted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS, help=f"rows per table (default: {DEFAULT_ROWS})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"RNG seed (default: {DEFAULT_SEED})")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="path to schema_manifest.json")
    args = parser.parse_args()

    password = os.environ.get("MSSQL_SA_PASSWORD")
    if not password:
        print("export MSSQL_SA_PASSWORD before running synthesize.py", file=sys.stderr)
        return 1

    host = os.environ.get("MSSQL_HOST", DEFAULT_HOST)
    port = int(os.environ.get("MSSQL_PORT", str(DEFAULT_PORT)))

    if not args.manifest.exists():
        print(f"manifest not found: {args.manifest} — run capture-loopcapital or introspect_local first", file=sys.stderr)
        return 1

    manifest = load_manifest(path=args.manifest)
    print(f"Synthesizing {manifest.database} from {args.manifest.name} "
          f"({len(manifest.tables)} tables, source={manifest.source.value}, rows={args.rows}, seed={args.seed})...")

    recreate_database(host=host, port=port, password=password, database=manifest.database)
    total = apply_schema_and_seed(
        host=host, port=port, password=password, manifest=manifest, rows=args.rows, seed=args.seed
    )
    print(f"\nSynthesize complete — {len(manifest.tables)} tables, {total} synthetic rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
