# Source Type 3 — Snowflake Data Share

Stand-in for an inbound Snowflake Data Share. Real shares require provider-side configuration; we use a second database with cross-DB grants to get the same query shape.

## Snowflake objects

| Object | Where |
|---|---|
| Database | `LONGAEVA_VENDOR_SHARE_SIM` |
| Schema | `LONGAEVA_VENDOR_SHARE_SIM.SHARED` |
| Tables | `vendor_security_master`, `vendor_ratings` |

DDL: [`../../snowflake/50_share_sim.sql`](../../snowflake/50_share_sim.sql).

`LONGAEVA_POC_ROLE` owns this DB so `SELECT` is implicit. In a real share, Longaeva would grant a separate share-consumer role; downstream models behave the same.

## Lifecycle the ingestion agent must scaffold

1. **Introspect** — read `LONGAEVA_VENDOR_SHARE_SIM.INFORMATION_SCHEMA.{TABLES,COLUMNS}` to discover the share's tables.
2. **dbt sources.yml** — emit a source pointing to `LONGAEVA_VENDOR_SHARE_SIM.SHARED.*`.
3. **Staging models** — generate `stg_vendor_security_master.sql` and `stg_vendor_ratings.sql` that:
   - Canonicalize column names (e.g. `vendor_security_id` → `external_security_id`)
   - Cast types to the project's canonical types
   - Apply soft-delete semantics if `is_active` columns exist
4. **GX contracts** — emit `not_null`, `unique`, `accepted_values` tests inferred from schema introspection (PKs → unique+not_null; coded columns with low cardinality → accepted_values).

## Swap to a real share later

Replace the simulation database name in dbt sources with the real share name:

```yaml
sources:
  - name: vendor_share
    database: <REAL_SHARE_DB>      # was: LONGAEVA_VENDOR_SHARE_SIM
    schema: SHARED
    tables:
      - name: vendor_security_master
      - name: vendor_ratings
```

No model changes required.
