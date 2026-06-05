"""BH-590 — Snowflake introspection, CORRECTED and live-validated.

Standalone extraction of the methods that BH-590 adds to SnowflakeConnection,
written so they can be unit-tested in isolation (mocked execute_query) and
live-tested against LONGAEVA_POC. Once green, these bodies paste back into
SnowflakeConnection in brightbot/tools/warehouse_connections.py.

Key corrections vs the original spec (each proven against live Snowflake):
  1. Snowflake has NO INFORMATION_SCHEMA.KEY_COLUMN_USAGE — the spec's PK JOIN
     errors on every call. PKs come from `SHOW PRIMARY KEYS IN <scope>` instead.
  2. Introspection routes through execute_query (which runs assert_read_only_sql),
     NOT a cursor-bypass helper. Closes the read-only gap AND makes the tests'
     execute_query mock actually intercept the call.
  3. INFORMATION_SCHEMA (61 views) and PUBLIC are excluded — else list_tables
     returns ~82 rows instead of the real user tables.
  4. Identifiers (db/schema) are validated against an identifier regex before
     interpolation — no raw f-string injection into SQL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

# Schemas that are never user data — excluded from introspection.
_SYSTEM_SCHEMAS: frozenset[str] = frozenset({"INFORMATION_SCHEMA", "PUBLIC"})

# Snowflake unquoted identifier: letter/underscore start, then alnum/underscore/$.
# We only ever interpolate identifiers we validate with this — never raw input.
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


def _validate_identifier(value: str, *, kind: str) -> str:
    """Return value if it is a safe SQL identifier, else raise ValueError."""
    if not _IDENTIFIER_RE.match(value):
        raise ValueError(
            f"Unsafe {kind} identifier {value!r} — must match {_IDENTIFIER_RE.pattern}"
        )
    return value


@dataclass(frozen=True)
class IntrospectedColumn:
    """A single column from INFORMATION_SCHEMA.COLUMNS."""

    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    ordinal_position: int
    comment: str | None = None
    character_max_length: int | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None


@dataclass(frozen=True)
class IntrospectedTable:
    """A single table from INFORMATION_SCHEMA.TABLES with its columns."""

    database: str
    schema: str
    name: str
    table_type: str
    row_count: int | None
    comment: str | None
    columns: tuple[IntrospectedColumn, ...]


@dataclass(frozen=True)
class IntrospectedStage:
    """An external/internal stage (Snowflake SHOW STAGES)."""

    database: str
    schema: str
    name: str
    stage_type: str
    url: str | None
    comment: str | None


@dataclass(frozen=True)
class IntrospectedSemanticView:
    """A Snowflake semantic view (SHOW SEMANTIC VIEWS)."""

    database: str
    schema: str
    name: str
    comment: str | None


class _QueryRunner(Protocol):
    """The subset of SnowflakeConnection the introspection methods rely on."""

    connection_params: dict[str, Any]

    def execute_query(self, query: str) -> list[dict[str, Any]]: ...


class SnowflakeIntrospectionMixin:
    """Introspection methods mixed into SnowflakeConnection.

    Every query goes through self.execute_query so the existing
    assert_read_only_sql guard runs and so unit tests can mock one method.
    """

    def _resolve_database(self: _QueryRunner, database: str | None) -> str:
        db = database or self.connection_params.get("database")
        if not db:
            raise ValueError("No database specified — pass database=… or set it on the connection")
        return _validate_identifier(db, kind="database")

    def list_tables(
        self: _QueryRunner,
        *,
        database: str | None = None,
        schema: str | None = None,
    ) -> tuple[IntrospectedTable, ...]:
        """Introspect user tables + columns + PKs via INFORMATION_SCHEMA + SHOW PRIMARY KEYS."""
        db = SnowflakeIntrospectionMixin._resolve_database(self, database)  # type: ignore[arg-type]

        if schema is not None:
            schema = _validate_identifier(schema.upper(), kind="schema")
            schema_filter = f"AND t.TABLE_SCHEMA = '{schema}'"
            pk_scope = f"SCHEMA {db}.{schema}"
        else:
            schema_filter = ""
            pk_scope = f"DATABASE {db}"

        system_list = ", ".join(f"'{s}'" for s in sorted(_SYSTEM_SCHEMAS))

        query = f"""
            SELECT
                t.TABLE_CATALOG            AS table_database,
                t.TABLE_SCHEMA             AS table_schema,
                t.TABLE_NAME               AS table_name,
                t.TABLE_TYPE               AS table_type,
                t.ROW_COUNT                AS row_count,
                t.COMMENT                  AS table_comment,
                c.COLUMN_NAME              AS column_name,
                c.DATA_TYPE                AS column_type,
                c.IS_NULLABLE              AS is_nullable,
                c.ORDINAL_POSITION         AS ordinal_position,
                c.COMMENT                  AS column_comment,
                c.CHARACTER_MAXIMUM_LENGTH AS char_max_len,
                c.NUMERIC_PRECISION        AS numeric_precision,
                c.NUMERIC_SCALE            AS numeric_scale
            FROM {db}.INFORMATION_SCHEMA.TABLES t
            JOIN {db}.INFORMATION_SCHEMA.COLUMNS c
                ON c.TABLE_CATALOG = t.TABLE_CATALOG
               AND c.TABLE_SCHEMA  = t.TABLE_SCHEMA
               AND c.TABLE_NAME    = t.TABLE_NAME
            WHERE t.TABLE_TYPE IN ('BASE TABLE', 'VIEW', 'EXTERNAL TABLE')
              AND t.TABLE_SCHEMA NOT IN ({system_list})
              {schema_filter}
            ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
        """

        rows = self.execute_query(query)

        # PKs come from SHOW PRIMARY KEYS — KEY_COLUMN_USAGE does not exist in Snowflake.
        pk_rows = self.execute_query(f"SHOW PRIMARY KEYS IN {pk_scope}")
        pk_set: set[tuple[str, str, str]] = {
            (r["schema_name"], r["table_name"], r["column_name"]) for r in pk_rows
        }

        grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for row in rows:
            key = (row["TABLE_DATABASE"], row["TABLE_SCHEMA"], row["TABLE_NAME"])
            grouped.setdefault(key, []).append(row)

        return tuple(
            IntrospectedTable(
                database=key[0],
                schema=key[1],
                name=key[2],
                table_type=col_rows[0]["TABLE_TYPE"],
                row_count=col_rows[0]["ROW_COUNT"],
                comment=col_rows[0]["TABLE_COMMENT"],
                columns=tuple(
                    IntrospectedColumn(
                        name=r["COLUMN_NAME"],
                        data_type=r["COLUMN_TYPE"],
                        is_nullable=(r["IS_NULLABLE"] == "YES"),
                        is_primary_key=(key[1], key[2], r["COLUMN_NAME"]) in pk_set,
                        ordinal_position=r["ORDINAL_POSITION"],
                        comment=r["COLUMN_COMMENT"],
                        character_max_length=r["CHAR_MAX_LEN"],
                        numeric_precision=r["NUMERIC_PRECISION"],
                        numeric_scale=r["NUMERIC_SCALE"],
                    )
                    for r in sorted(col_rows, key=lambda x: x["ORDINAL_POSITION"])
                ),
            )
            for key, col_rows in grouped.items()
        )

    def list_stages(
        self: _QueryRunner,
        *,
        database: str | None = None,
        schema: str | None = None,
    ) -> tuple[IntrospectedStage, ...]:
        """Introspect stages via SHOW STAGES (routed through execute_query → read-only guard)."""
        db = SnowflakeIntrospectionMixin._resolve_database(self, database)  # type: ignore[arg-type]
        if schema is not None:
            schema = _validate_identifier(schema.upper(), kind="schema")
            scope = f"SCHEMA {db}.{schema}"
        else:
            scope = f"DATABASE {db}"

        rows = self.execute_query(f"SHOW STAGES IN {scope}")
        return tuple(
            IntrospectedStage(
                database=r["database_name"],
                schema=r["schema_name"],
                name=r["name"],
                stage_type=r["type"],
                url=r.get("url") or None,
                comment=r.get("comment") or None,
            )
            for r in rows
        )

    def list_semantic_views(
        self: _QueryRunner,
        *,
        database: str | None = None,
        schema: str | None = None,
    ) -> tuple[IntrospectedSemanticView, ...]:
        """Introspect semantic views via SHOW SEMANTIC VIEWS; empty tuple if unsupported/unauthorized."""
        db = SnowflakeIntrospectionMixin._resolve_database(self, database)  # type: ignore[arg-type]
        if schema is not None:
            schema = _validate_identifier(schema.upper(), kind="schema")
            scope = f"SCHEMA {db}.{schema}"
        else:
            scope = f"DATABASE {db}"

        try:
            rows = self.execute_query(f"SHOW SEMANTIC VIEWS IN {scope}")
        except Exception:
            # Account/role without semantic-view support → empty is the correct answer.
            return ()

        return tuple(
            IntrospectedSemanticView(
                database=r["database_name"],
                schema=r["schema_name"],
                name=r["name"],
                comment=r.get("comment") or None,
            )
            for r in rows
        )
