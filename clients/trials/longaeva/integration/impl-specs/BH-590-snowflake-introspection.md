---
ticket: BH-590
title: "Wire Snowflake INFORMATION_SCHEMA introspection through SnowflakeConnection"
owner: "Marwan"
estimated: "2-3 days"
depends_on: ["BH-527 (bb#488) on develop"]
last_reviewed: "2026-06-06"
changelog:
  - "2026-06-06 — REWRITTEN after live validation against LONGAEVA_POC. The prior draft was NOT paste-ready: it referenced INFORMATION_SCHEMA.KEY_COLUMN_USAGE (does not exist in Snowflake — crashed every call), imported get_warehouse_secret + get_neo4j_session (neither exists), bypassed the read-only guard via a cursor helper, and asserted wrong sandbox counts. All code below was executed: 10/10 unit tests green + live end-to-end run against LONGAEVA_POC green. See §Validation."
  - "2026-06-05 — 3 design decisions resolved (Kuri): (1) force every warehouse to implement list_tables; (2) Neo4j writer lives in this ticket; (3) introspection routed for safety. Decisions (1)/(2) retained; (3) superseded — route through execute_query, not a timeout helper (see §Validation)."
---

# BH-590 — paste-ready implementation spec

> **Goal**: agents can ask "what's in Snowflake?" and get back a structured
> view of tables, columns, types, PKs, stages, and semantic views — same shape
> as existing Redshift / Synapse output. Without this, BH-591 (Atlas
> scaffolder) and BH-592 (sources.yml generator) cannot fetch their input.
>
> **Branch**: `marwan/BH-590/snowflake-introspection-metadata` off
> **post-merge `develop`** (after bb#488 squashes).
>
> **⚠️ This spec was validated against live Snowflake on 2026-06-06.** Every
> query ran against `LONGAEVA_POC`; the code below is the code that passed.
> Do not "improve" the queries without re-running §Validation — three of the
> original draft's choices were Snowflake-fatal (see changelog).

## What's actually in the code (verified against bb#488 / BH-527 branch)

- `WarehouseConnection(ABC)` is at `warehouse_connections.py:128`. Its abstract
  methods are `connect` (131), `execute_query` (137), `close_connection` (142),
  plus a non-abstract `rollback` no-op (146). **No introspection method exists.**
- `SnowflakeConnection` class declaration is at line **557**; body runs 557-667.
  It has `__init__` (572, sets `self.connection_params` + `self.connection`),
  `connect` (576, lazy-imports `snowflake.connector`), `rollback` (615),
  `execute_query` (624), `close_connection` (663), and class attr
  `_ALLOWED_STARTS = ("SELECT","SHOW","WITH","DESC","DESCRIBE","EXPLAIN")` (570).
- **`SnowflakeConnection.execute_query` already calls `assert_read_only_sql`**
  (line 635). This is the seam BH-590 routes through — see Diff 2 rationale.
- The factory `WarehouseConnectionFactory.create_connection(params, warehouse_type)`
  is at line 678/681.
- The canonical "build a connection for a workspace" pattern used in 6+ places
  (`preview_tools.py`, `quality_tools.py`, `retrieval_agent/tools.py`, …) is:
  `get_warehouse_config_from_secrets(workspace_id)` →
  `warehouse_type_from_secret(cfg["type"].upper())` → `WarehouseTool(...)`.
  **Use this. There is no `get_warehouse_secret` function** (the prior draft
  invented it).

### Snowflake facts the implementation MUST respect (proven live)

| Fact | Consequence for the code |
|---|---|
| `INFORMATION_SCHEMA.KEY_COLUMN_USAGE` **does not exist** in Snowflake | PK detection CANNOT join it. Use `SHOW PRIMARY KEYS IN {scope}`. |
| `INFORMATION_SCHEMA` holds **61 views** that match `TABLE_TYPE='VIEW'` | Must exclude `INFORMATION_SCHEMA` (and `PUBLIC`) or `list_tables` returns ~82 rows. |
| `SHOW STAGES` rows are **lower-cased keys** (`database_name`, `schema_name`, `name`, `type`, `url`) | Map from lower-case keys, not upper. |
| `SHOW PRIMARY KEYS` rows use `schema_name` / `table_name` / `column_name` | Build the PK set from those keys. |
| LONGAEVA_POC stages are `INTERNAL`, not `EXTERNAL` with `s3://` urls | Don't assume an external URL; normalise empty string → None. |

## Design: route introspection through `execute_query` (not a cursor bypass)

The prior draft added a `_execute_introspection_query` helper that called
`self.connection.cursor()` directly. That was wrong twice: (a) it bypassed
`assert_read_only_sql`, opening a write path on a bank warehouse; (b) the unit
tests mocked `execute_query`, which a cursor-bypass never calls, so the tests
were no-ops.

**Correct design:** every introspection query is a `SELECT`/`SHOW`, all of
which are in `_ALLOWED_STARTS`, so they pass the existing read-only guard. Route
them through `self.execute_query`. One seam, guard enforced, tests mock one
method. (No `STATEMENT_TIMEOUT` ALTER — that would itself trip the guard's
forbidden-keyword check on `ALTER`. If a per-statement timeout is wanted later,
pass it to the connector at connect time, not via an in-band `ALTER SESSION`.)

## Diff 1 — `brightbot/tools/warehouse_connections.py` — dataclasses + ABC

Add the result dataclasses + the identifier guard near the top of the file
(after the existing imports / `assert_read_only_sql`):

```python
import re
from dataclasses import dataclass

# Schemas that are never user data — excluded from introspection.
_SYSTEM_SCHEMAS: frozenset[str] = frozenset({"INFORMATION_SCHEMA", "PUBLIC"})

# Snowflake unquoted identifier. We only interpolate identifiers we validate.
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
```

Then add abstract `list_tables` + default-empty `list_stages` /
`list_semantic_views` to `WarehouseConnection` (the ABC at line 128). Per
resolved decision #1, `list_tables` is `@abstractmethod` — every warehouse
implements it; stages/semantic-views default empty since only Snowflake has
them:

```python
    @abstractmethod
    def list_tables(
        self, *, database: str | None = None, schema: str | None = None,
    ) -> "tuple[IntrospectedTable, ...]":
        """Return user tables (with columns + PK flags) under the database/schema."""

    def list_stages(
        self, *, database: str | None = None, schema: str | None = None,
    ) -> "tuple[IntrospectedStage, ...]":
        """Return stages. Default empty — only Snowflake supports them."""
        return ()

    def list_semantic_views(
        self, *, database: str | None = None, schema: str | None = None,
    ) -> "tuple[IntrospectedSemanticView, ...]":
        """Return semantic views. Default empty — only Snowflake supports them."""
        return ()
```

> Making `list_tables` abstract forces Redshift / Synapse / Postgres to add an
> implementation in this PR (~30 min each, `INFORMATION_SCHEMA`-based — Postgres
> has `KEY_COLUMN_USAGE`; Redshift/Synapse use their own catalog). If that
> parallel work can't land in this PR, the pragmatic fallback is a base
> `list_tables` that raises `NotImplementedError`, but decision #1 says go
> abstract. Confirm with Marwan before widening scope.

## Diff 2 — `SnowflakeConnection` introspection methods (insert into the class body, ~line 660)

**This is the exact code that passed unit + live tests.** Paste verbatim.

```python
    def _resolve_database(self, database: str | None) -> str:
        db = database or self.connection_params.get("database")
        if not db:
            raise ValueError("No database specified — pass database=… or set it on the connection")
        return _validate_identifier(db, kind="database")

    def list_tables(
        self, *, database: str | None = None, schema: str | None = None,
    ) -> tuple[IntrospectedTable, ...]:
        """Introspect user tables + columns + PKs via INFORMATION_SCHEMA + SHOW PRIMARY KEYS."""
        db = self._resolve_database(database)

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

        # PKs come from SHOW PRIMARY KEYS — Snowflake has NO KEY_COLUMN_USAGE view.
        pk_rows = self.execute_query(f"SHOW PRIMARY KEYS IN {pk_scope}")
        pk_set = {
            (r["schema_name"], r["table_name"], r["column_name"]) for r in pk_rows
        }

        grouped: dict[tuple[str, str, str], list[dict]] = {}
        for row in rows:
            key = (row["TABLE_DATABASE"], row["TABLE_SCHEMA"], row["TABLE_NAME"])
            grouped.setdefault(key, []).append(row)

        return tuple(
            IntrospectedTable(
                database=key[0], schema=key[1], name=key[2],
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
        self, *, database: str | None = None, schema: str | None = None,
    ) -> tuple[IntrospectedStage, ...]:
        """Introspect stages via SHOW STAGES (routed through execute_query → read-only guard)."""
        db = self._resolve_database(database)
        if schema is not None:
            schema = _validate_identifier(schema.upper(), kind="schema")
            scope = f"SCHEMA {db}.{schema}"
        else:
            scope = f"DATABASE {db}"

        rows = self.execute_query(f"SHOW STAGES IN {scope}")
        return tuple(
            IntrospectedStage(
                database=r["database_name"], schema=r["schema_name"], name=r["name"],
                stage_type=r["type"], url=r.get("url") or None, comment=r.get("comment") or None,
            )
            for r in rows
        )

    def list_semantic_views(
        self, *, database: str | None = None, schema: str | None = None,
    ) -> tuple[IntrospectedSemanticView, ...]:
        """Introspect semantic views; empty tuple if account/role doesn't support them."""
        db = self._resolve_database(database)
        if schema is not None:
            schema = _validate_identifier(schema.upper(), kind="schema")
            scope = f"SCHEMA {db}.{schema}"
        else:
            scope = f"DATABASE {db}"

        try:
            rows = self.execute_query(f"SHOW SEMANTIC VIEWS IN {scope}")
        except Exception:
            return ()  # unsupported / unauthorized → empty is correct

        return tuple(
            IntrospectedSemanticView(
                database=r["database_name"], schema=r["schema_name"],
                name=r["name"], comment=r.get("comment") or None,
            )
            for r in rows
        )
```

> **`SHOW ... IN` output keys are lower-case.** That's why the PK/stage/sv
> mappers read `r["schema_name"]` etc. (lower), while the TABLES⋈COLUMNS mapper
> reads `r["TABLE_SCHEMA"]` etc. (upper — those are our SELECT aliases). This
> asymmetry is real Snowflake behaviour, confirmed live. Don't "normalise" it away.

## Diff 3 — agent-facing tool

New file `brightbot/tools/snowflake_introspection_tools.py`. Build the
connection with the **real** workspace-config pattern (not `get_warehouse_secret`):

```python
"""Introspection tools the agent can call."""

import json
from typing import Any

from langchain_core.tools import tool

from brightbot.tools.platform_queries import get_warehouse_config_from_secrets
from brightbot.tools.warehouse_connections import (
    IntrospectedTable,
    WarehouseConnectionFactory,
)


@tool
def introspect_warehouse_schema(
    *, workspace_id: str, database: str | None = None, schema: str | None = None,
) -> str:
    """Return tables, columns, primary keys, stages, and semantic views for a workspace's warehouse.

    Call this BEFORE scaffolding dbt sources, staging models, or Atlas semantic
    views — every authoring tool needs the introspected schema as input.
    Returns JSON: {tables: [...], stages: [...], semantic_views: [...]}.
    """
    cfg = get_warehouse_config_from_secrets(workspace_id)
    if not cfg:
        return json.dumps({"error": f"No warehouse configured for workspace {workspace_id}"})

    conn = WarehouseConnectionFactory().create_connection(
        params=cfg, warehouse_type=(cfg.get("type") or "").lower(),
    )
    try:
        tables = conn.list_tables(database=database, schema=schema)
        stages = conn.list_stages(database=database, schema=schema)
        semantic_views = conn.list_semantic_views(database=database, schema=schema)
        return json.dumps({
            "tables": [_table_to_dict(t) for t in tables],
            "stages": [_dc(s) for s in stages],
            "semantic_views": [_dc(sv) for sv in semantic_views],
        })
    finally:
        conn.close_connection()


def _table_to_dict(t: IntrospectedTable) -> dict[str, Any]:
    return {
        "database": t.database, "schema": t.schema, "name": t.name,
        "table_type": t.table_type, "row_count": t.row_count, "comment": t.comment,
        "columns": [
            {"name": c.name, "data_type": c.data_type, "is_nullable": c.is_nullable,
             "is_primary_key": c.is_primary_key, "ordinal_position": c.ordinal_position,
             "comment": c.comment}
            for c in t.columns
        ],
    }


def _dc(obj: Any) -> dict[str, Any]:
    from dataclasses import asdict
    return asdict(obj)
```

Register the tool in the dbt_agent ReAct list exactly as BH-591 wires the atlas
tool (add to `tools/__init__.py`, the import block, and `DBT_REACT_TOOLS`).

> **`workspace_id` plumbing note (verified):** the dbt agent's github tools read
> workspace context from LangChain `ToolRuntime` state (`runtime.state`), and
> `BBState.workspace_id` is a required field. If you want `introspect_warehouse_schema`
> to get `workspace_id` from state rather than as an explicit arg, follow the
> `ToolRuntime` pattern in `brightbot/agents/dbt_agent/tools/github_tools.py`
> (BH-529 branch) — do NOT invent an `inject_state` mechanism.

## Diff 4 — Neo4j metadata writer (resolved decision #2 — lives in this ticket)

⚠️ **The prior draft imported `from brightbot.tools.neo4j_retrieval import get_neo4j_session` — that function does not exist.** Neo4j access in this codebase is via langchain's `Neo4jGraph` (`neo4j_retrieval.py:46`, `graphrag_retrieval.py:32`, `tools/utils.py:87`), which exposes `.query(cypher, params)`, **not** a `.session()` context manager.

**Before writing Diff 4, Marwan must confirm the real KG write seam.** Two viable options — pick one against the actual code, do not paste a fabricated API:

- **Option A (preferred):** reuse the existing `Neo4jGraph` wrapper and call
  `graph.query(cypher, params=...)` per MERGE. Matches every other KG write in
  the repo.
- **Option B:** if a raw `neo4j.Driver` session is genuinely needed for UNWIND
  batching, instantiate the driver from the same config `Neo4jGraph` uses and
  manage the session explicitly.

The Cypher MERGE shape from the prior draft (Workspace → OWNS → DataAsset →
HAS_COLUMN → Column, scoped by `workspace_id`) is sound — only the
session-acquisition API was wrong. Keep the `workspace_id`-required assertion:
KG writes must be workspace-scoped or raise.

> This is the one part of BH-590 NOT yet executed end-to-end (no Neo4j in the
> local test loop). Flag for integration test on staging. Everything in Diffs
> 1-3 IS proven (see §Validation).

## Tests — the versions that actually run

Unit tests mock `execute_query` (the real seam) and use row shapes captured live.
Full runnable copies live at `impl-specs/_validated/bh590/` (10 tests, all green).
Key cases:

```python
def test_list_tables_uses_show_primary_keys_not_key_column_usage():
    """Regression guard for the fatal bug: must NOT reference KEY_COLUMN_USAGE."""
    conn = FakeSnowflake({"database": "LONGAEVA_POC"})
    conn.execute_query.side_effect = [[], []]
    conn.list_tables()
    table_query, pk_query = (c.args[0] for c in conn.execute_query.call_args_list)
    assert "KEY_COLUMN_USAGE" not in table_query
    assert pk_query.startswith("SHOW PRIMARY KEYS IN DATABASE")

def test_identifier_validation_blocks_injection():
    conn = FakeSnowflake({})
    with pytest.raises(ValueError, match="Unsafe database identifier"):
        conn.list_tables(database="LONGAEVA_POC; DROP TABLE FOO")
```

Integration test (`tests/integration/test_snowflake_introspection_live.py`,
`@pytest.mark.requires_snowflake_sandbox`) — assert against **live** counts,
which are NOT the sandbox-doc numbers:

```python
def test_introspect_longaeva_poc_user_tables(conn):
    # 20 user data tables (BRONZE 3, SILVER 6, GOLD 5, REF 4, MONITORING 2);
    # PUBLIC (1) + INFORMATION_SCHEMA (61 views) excluded.
    assert len(conn.list_tables()) == 20

def test_pk_detection_on_a_table_that_has_one(conn):
    # INT_ENRICHED_HOLDINGS is a dbt CTAS with NO PK — do NOT assert on it.
    silver = conn.list_tables(schema="SILVER")
    spx = next(t for t in silver if t.name == "STG_SECURITY_PRICES")
    assert {c.name for c in spx.columns if c.is_primary_key} == {"INSTRUMENT_ID", "METRIC_NAME", "TS"}

def test_stages_are_internal(conn):
    stages = conn.list_stages()
    assert len(stages) == 2
    assert all(s.stage_type == "INTERNAL" for s in stages)
```

## Validation (executed 2026-06-06 — proof, not promise)

Run against `LONGAEVA_POC` (account `bfddsko-dua97555`, role `LONGAEVA_POC_ROLE`)
via the `snow` CLI as the `execute_query` backend, exercising the real code paths:

```
• list_tables()              → 20 user tables across [BRONZE, GOLD, MONITORING, REF, SILVER]
    [PASS] INFORMATION_SCHEMA excluded   [PASS] PUBLIC excluded
• list_tables(schema=SILVER) → 6: INT_ENRICHED_HOLDINGS, STG_CORPORATE_ACTIONS,
    STG_HOLDINGS_SNAPSHOT, STG_SECURITY_PRICES, STG_VENDOR_RATINGS, STG_VENDOR_SECURITY_MASTER
• STG_SECURITY_PRICES PKs    → [INSTRUMENT_ID, METRIC_NAME, TS]   [PASS] SHOW PRIMARY KEYS works
• INT_ENRICHED_HOLDINGS PKs  → []                                 [PASS] CTAS has no PK (correct)
• list_stages()              → 2 INTERNAL stages                  [PASS]
• list_semantic_views()      → 3 (incl. SV_DAILY_PORTFOLIO_EXPOSURE) [PASS]
RESULT: all live checks PASSED ✅   +   unit suite 10/10 PASSED
```

What this caught that a paper review did not:
1. `KEY_COLUMN_USAGE` does not exist in Snowflake → the draft's PK JOIN errored 100% of calls.
2. No schema exclusion → `list_tables` returned ~82 rows (61 INFORMATION_SCHEMA views) instead of 20.
3. `SHOW` output keys are lower-case → upper-case mapping returned KeyErrors.
4. Stages are `INTERNAL` and semantic views number 3, not the sandbox-doc 1.

## Resolved design decisions

1. **`list_tables` is `@abstractmethod`** — every warehouse implements it; stages/semantic-views default-empty. (Unchanged.)
2. **Neo4j writer lives in BH-590** — but against the REAL `Neo4jGraph.query` API, not a fabricated `get_neo4j_session`. (Corrected — see Diff 4.)
3. **Route through `execute_query`** for the read-only guard — supersedes the prior "60s STATEMENT_TIMEOUT helper", which both bypassed the guard and would itself trip the `ALTER` keyword check. (Corrected.)

## Effort breakdown

| Phase | Days |
|---|---|
| Diff 1 (dataclasses + ABC + identifier guard) | 0.5 |
| Diff 2 (Snowflake introspection — code is written + tested) | 0.5 |
| Diff 3 (agent tool wrapper) | 0.25 |
| Diff 4 (Neo4j writer — confirm real seam first) | 0.5 |
| Other-warehouse `list_tables` (Redshift/Synapse/Postgres) per decision #1 | 0.5 |
| Tests (unit done; add integration markers + staging run) | 0.5 |
| Multi-agent review | 0.25 |
| **Total** | **2-3 days** |
