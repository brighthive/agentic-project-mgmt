# BrightHive adapter — `SnowflakeConnection` (GAP-1 drop-in)

This is the **reference implementation that closes GAP-1** (see
[`../../BRIGHTHIVE_GAPS.md`](../../BRIGHTHIVE_GAPS.md)) — the missing
`SnowflakeConnection` in BrightHive's warehouse factory.

It's kept here in the sandbox so we can prove BrightHive's interface connects to
the live `LONGAEVA_POC` environment **before** touching the production
`brightbot` repo (which needs its own branch + the multi-agent review the
standards require).

## What it proves

`snowflake_connection.py` implements BrightHive's `WarehouseConnection` ABC
verbatim (connect / execute_query / close_connection / rollback + the identical
SELECT-only security guard) and self-tests against the live sandbox:

```
✅ connects + SELECT context        (CURRENT_ROLE=LONGAEVA_POC_ROLE, DB=LONGAEVA_POC)
✅ queries semantic view            (SEMANTIC_VIEW(...) returns 4 regions)
✅ SELECT-only guard blocks DELETE  (same policy as RedshiftConnection)
✅ INFORMATION_SCHEMA introspection (GAP-2 surface)
```

Run: `uv run --with snowflake-connector-python python snowflake_connection.py`

## Promotion path (closes GAP-1 + GAP-2 in `brightbot`)

1. Branch `brightbot`: `name/BH-526/snowflake-connection`.
2. Copy the `SnowflakeConnection` class into
   `brightbot/tools/warehouse_connections.py` (drop the local `WarehouseConnection`
   ABC stub — use the repo's existing ABC; drop the `ALLOWED_QUERY_STARTS`
   duplicate if the repo centralizes it).
3. Register it:
   ```python
   CONNECTION_CLASSES: dict[str, type[WarehouseConnection]] = {
       "redshift": RedshiftConnection,
       "azure_synapse": SynapseConnection,
       "postgres": PostgresConnection,
       "snowflake": SnowflakeConnection,   # <-- GAP-1
   }
   ```
4. Add `snowflake-connector-python` to brightbot deps.
5. Run the multi-agent review (Solutions Architect → Senior Python → QA →
   Junior Dev) per the Python rules, then the existing warehouse scenario tests
   pointed at `LONGAEVA_POC`.
6. For `brightagent-v2` (CEMAF): add a `SnowflakeAdapter` implementing the
   `Warehouse` Protocol in `bright_contracts/warehouse.py`, mirroring the
   Redshift adapter — same connect/execute/SELECT-guard semantics.

## Why it's not committed to brightbot here

Per the repo's git-workflow + Python multi-agent-review rules, production code
changes go through their own branch, draft PR, and review cycle. This sandbox
copy is the *validated reference* that makes that PR a mechanical drop-in with
zero design risk — the contract is already proven against the real target.
