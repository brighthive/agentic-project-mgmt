"""BH-590 unit tests — mock execute_query (the real seam), assert mapping + safety.

Fixtures use the EXACT row shapes proven against LONGAEVA_POC via the snow CLI:
  - INFORMATION_SCHEMA.COLUMNS rows are UPPER-keyed (aliased in the SELECT)
  - SHOW PRIMARY KEYS rows are lower-keyed (Snowflake SHOW output convention)
"""

from unittest.mock import MagicMock

import pytest

from introspection import (
    IntrospectedTable,
    SnowflakeIntrospectionMixin,
    _validate_identifier,
)


class FakeSnowflake(SnowflakeIntrospectionMixin):
    """Minimal stand-in: just the attributes the mixin reads + a mockable execute_query."""

    def __init__(self, connection_params: dict) -> None:
        self.connection_params = connection_params
        self.execute_query = MagicMock()


def _col_row(schema, table, col, pos, *, dtype="TEXT", nullable="YES", rows=100):
    return {
        "TABLE_DATABASE": "LONGAEVA_POC",
        "TABLE_SCHEMA": schema,
        "TABLE_NAME": table,
        "TABLE_TYPE": "BASE TABLE",
        "ROW_COUNT": rows,
        "TABLE_COMMENT": None,
        "COLUMN_NAME": col,
        "COLUMN_TYPE": dtype,
        "IS_NULLABLE": nullable,
        "ORDINAL_POSITION": pos,
        "COLUMN_COMMENT": None,
        "CHAR_MAX_LEN": None,
        "NUMERIC_PRECISION": None,
        "NUMERIC_SCALE": None,
    }


def _pk_row(schema, table, col):
    return {"schema_name": schema, "table_name": table, "column_name": col}


def test_list_tables_groups_columns_and_marks_pks():
    """Two tables grouped from flat rows; PK flag set only for SHOW PRIMARY KEYS hits."""
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.side_effect = [
        # 1st call: TABLES⋈COLUMNS
        [
            _col_row("SILVER", "STG_SECURITY_PRICES", "INSTRUMENT_ID", 1, dtype="TEXT", nullable="NO"),
            _col_row("SILVER", "STG_SECURITY_PRICES", "TS", 2, dtype="TIMESTAMP_NTZ", nullable="NO"),
            _col_row("SILVER", "STG_SECURITY_PRICES", "PX", 3, dtype="NUMBER"),
            _col_row("SILVER", "INT_ENRICHED_HOLDINGS", "MARKET_VALUE_USD", 1, dtype="NUMBER"),
        ],
        # 2nd call: SHOW PRIMARY KEYS — only STG_SECURITY_PRICES has PKs
        [
            _pk_row("SILVER", "STG_SECURITY_PRICES", "INSTRUMENT_ID"),
            _pk_row("SILVER", "STG_SECURITY_PRICES", "TS"),
        ],
    ]

    tables = conn.list_tables(database="LONGAEVA_POC")

    assert len(tables) == 2
    spx = next(t for t in tables if t.name == "STG_SECURITY_PRICES")
    holdings = next(t for t in tables if t.name == "INT_ENRICHED_HOLDINGS")

    pk_cols = {c.name for c in spx.columns if c.is_primary_key}
    assert pk_cols == {"INSTRUMENT_ID", "TS"}          # PKs detected
    assert all(not c.is_primary_key for c in holdings.columns)  # CTAS table → no PK (matches live)
    assert spx.columns[1].is_nullable is False
    assert spx.columns[2].is_nullable is True


def test_list_tables_uses_show_primary_keys_not_key_column_usage():
    """Regression guard for the fatal bug: we must NOT reference KEY_COLUMN_USAGE."""
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.side_effect = [[], []]
    conn.list_tables()

    queries = [c.args[0] for c in conn.execute_query.call_args_list]
    table_query, pk_query = queries[0], queries[1]
    assert "KEY_COLUMN_USAGE" not in table_query          # the bug that crashed every call
    assert "INFORMATION_SCHEMA.TABLES" in table_query
    assert "INFORMATION_SCHEMA.COLUMNS" in table_query
    assert pk_query.startswith("SHOW PRIMARY KEYS IN DATABASE")


def test_list_tables_excludes_system_schemas():
    """INFORMATION_SCHEMA + PUBLIC must be filtered (else ~82 rows on a real DB)."""
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.side_effect = [[], []]
    conn.list_tables()
    table_query = conn.execute_query.call_args_list[0].args[0]
    assert "'INFORMATION_SCHEMA'" in table_query
    assert "'PUBLIC'" in table_query
    assert "NOT IN" in table_query


def test_schema_filter_scopes_query_and_pk_lookup():
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.side_effect = [[], []]
    conn.list_tables(schema="silver")
    table_query, pk_query = (c.args[0] for c in conn.execute_query.call_args_list)
    assert "TABLE_SCHEMA = 'SILVER'" in table_query        # upper-cased + scoped
    assert pk_query == "SHOW PRIMARY KEYS IN SCHEMA LONGAEVA_POC.SILVER"


def test_missing_database_raises():
    conn = FakeSnowflake({})  # no default database
    with pytest.raises(ValueError, match="No database specified"):
        conn.list_tables()


def test_identifier_validation_blocks_injection():
    """db/schema are interpolated — they MUST be validated against the identifier regex."""
    conn = FakeSnowflake({})
    with pytest.raises(ValueError, match="Unsafe database identifier"):
        conn.list_tables(database="LONGAEVA_POC; DROP TABLE FOO")
    with pytest.raises(ValueError, match="Unsafe schema identifier"):
        conn.list_tables(database="LONGAEVA_POC", schema="SILVER'; DROP")


def test_validate_identifier_accepts_real_names():
    assert _validate_identifier("LONGAEVA_POC", kind="database") == "LONGAEVA_POC"
    assert _validate_identifier("STG_HOLDINGS_SNAPSHOT", kind="table") == "STG_HOLDINGS_SNAPSHOT"


def test_list_stages_maps_show_output():
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.return_value = [
        {"database_name": "LONGAEVA_POC", "schema_name": "BRONZE",
         "name": "S3_VENDOR_MARKET_DATA", "type": "INTERNAL", "url": "", "comment": ""},
    ]
    stages = conn.list_stages(database="LONGAEVA_POC")
    assert len(stages) == 1
    assert stages[0].name == "S3_VENDOR_MARKET_DATA"
    assert stages[0].stage_type == "INTERNAL"   # live truth: INTERNAL, not EXTERNAL
    assert stages[0].url is None                # empty string normalised to None


def test_list_semantic_views_swallows_unsupported():
    """Older account / no privilege → empty tuple, never an exception."""
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.side_effect = Exception("Unsupported feature 'SEMANTIC_VIEWS'")
    assert conn.list_semantic_views(database="LONGAEVA_POC") == ()


def test_list_semantic_views_maps_rows():
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.return_value = [
        {"database_name": "LONGAEVA_POC", "schema_name": "SEMANTIC",
         "name": "SV_DAILY_PORTFOLIO_EXPOSURE", "comment": ""},
    ]
    svs = conn.list_semantic_views(database="LONGAEVA_POC")
    assert len(svs) == 1
    assert svs[0].name == "SV_DAILY_PORTFOLIO_EXPOSURE"
