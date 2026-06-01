---
title: "Snowflake — Full Platform Integration (extends warehouse-agnostic pattern)"
epic: "BH-503-snowflake"
author: "drchinca"
status: "Ready"
created: "2026-06-01"
last_reviewed: "2026-06-01"
generates: "epic"
tags: [warehouse, snowflake, byow, ingestion, destination, longaeva]
related:
  features: []
  pocs: []
  bedrock: []
  specs:
    - warehouse-agnostic-architecture.md
    - warehouse-extensibility-pattern.md
    - azure-synapse-full-integration.md
---

# Snowflake — Full Platform Integration

## Problem

Snowflake is the warehouse of every prospect in the financial-services pipeline (Longaeva, AKRF, KPS, plus 4 more in qualification). The platform has **uneven** Snowflake support today:

- **Platform-core (TypeScript)**: full destination handler, OMD webhook adapter, validators, enum — production-shape.
- **Brightbot (Python)**: connection params pydantic model exists, dialect prompt is a one-line stub, `SnowflakeConnection` class **does not exist**, factory route raises `ValueError`. SQL cannot execute against Snowflake from brightbot today.
- **Org CDK**: full `SnowflakeIngestionStack` + JWT lambda + S3 role wiring — production-shape but **predates the workspace-secret-store pattern** Synapse uses.
- **OMD ingestion lambda**: no `SnowflakeSourceConfig` registered (Synapse has one).

The result: brightbot agents cannot query a customer's Snowflake at all, even though the rest of the platform thinks Snowflake is supported. For Longaeva — and every Snowflake-native prospect — this is the gating gap.

## Use Case / Goal

A workspace admin attaches a Snowflake warehouse (BYOW) via the webapp, brightbot agents query it for the retrieval, quality, dbt, and semantic-view agents, and the org-side ingestion SFn lands data into Snowflake destinations — all using the same warehouse-agnostic pattern Azure Synapse follows.

Success: every layer of the 7-layer warehouse pattern (per `warehouse-agnostic-architecture.md`) has a Snowflake-equivalent that mirrors Synapse exactly — same registry entries, same secret-store shape, same test coverage.

## Current Situation

This section is the synthesis of the 4-agent audit completed 2026-06-01. The pattern was established by PRs #706, #707, #719, #720, #722, #724 (platform-core), PR #433 (brightbot Synapse dialect), PRs #139 / #149 (org-cdk Synapse ingestion).

### The 7 Warehouse-Agnostic Layers (the pattern)

Per `warehouse-agnostic-architecture.md` (BH-172, Approved), a new warehouse must touch these layers. Type-string contract: `SNOWFLAKE` (uppercase) flows through `WarehouseServiceProvider` enum → workspace secret store → every downstream layer.

| # | Layer | Repo | What it does |
|---|---|---|---|
| 1 | Destination Service (Connect/Download) | `brighthive-platform-core/src/graphql/service/destination_service/` | Customer's warehouse user provisioning + share grants |
| 2 | OMD Webhook Adapter | `brighthive-platform-core/openmetadata_webhook_lambda/` | Schema-event handler from OpenMetadata catalog |
| 3 | OMD Ingestion Source Config | `brighthive-platform-core/openmetadata_ingestion_lambda/` | OMD source registration + dialect mapping |
| 4 | OMD Service Type Mapping | `brighthive-platform-core/src/graphql/models/warehouse-service.ts` | Translates `WarehouseServiceProvider` → OMD service-type string |
| 5 | Brightbot Connection + Dialect | `brightbot/brightbot/tools/warehouse_connections.py` + `prompts/retrieval_agent_prompts.py` | `WarehouseConnection` impl, SQL dialect rules in agent prompts |
| 6 | Webapp Registry | `brighthive-webapp/.../warehouseRegistry.ts` | UI dropdown + form fields per warehouse |
| 7 | Org CDK Ingestion Pipeline | `brighthive-data-organization-cdk/brighthive_data_cdk/<wh>_ingestion.py` | Step Functions + Loader Lambda for destination side |

### Snowflake Status per Layer (audit findings)

| # | Layer | Status | Evidence | Gap to close |
|---|---|---|---|---|
| 1 | Destination Service | **Shipped** | `destination_service/snowflake.ts` (full `SnowflakeDestination` class, JWT-based auth via `getSnowflakeConfigWithJwt`). Registered in `destination.ts:142` (`case 'SNOWFLAKE'`). | None — already production-shape. Optional symmetric refactor: add `returnSnowflakeAdminSecrets(workspaceId)` helper to mirror `returnSynapseAdminSecrets` (Snowflake currently uses `cdk-admin-secret/{orgAcctId}` via STS, not the workspace secret-store path). |
| 2 | OMD Webhook Adapter | **Shipped** | `openmetadata_webhook_lambda/utils/warehouse_adapter.py:144-148` `SnowflakeAdapter`; registered in `WAREHOUSE_ADAPTERS:158`. Test at `tests/test_warehouse_adapter.py:36`. | None. |
| 3 | OMD Ingestion Source Config | **Gap** | `openmetadata_ingestion_lambda/config_loader.py` has `@register_source("synapse", ...)` (lines 156-209) but **no equivalent for Snowflake**. `main.py:38` service-type map has no `"snowflake"` entry. | Add `SnowflakeSourceConfig` class with `@register_source("snowflake", ...)`. Mirror Synapse structure. |
| 4 | OMD Service Type Mapping | **Shipped** | `warehouse-service.ts:145` translates `AZURE_SYNAPSE` → `Mssql`. Snowflake passes through unchanged (Snowflake's OMD service-type IS `Snowflake`). | None. |
| 5 | Brightbot Connection + Dialect | **Gap (critical — blocks Longaeva)** | (a) `tools/warehouse_connections.py:484-488` `CONNECTION_CLASSES` dict missing `"snowflake"` entry. (b) No `SnowflakeConnection(WarehouseConnection)` class. (c) `prompts/retrieval_agent_prompts.py:10` dialect rule is one-liner placeholder. (d) `prompts/retrieval_agent_prompts.py:14-41` `DIALECT_EXAMPLES` has no Snowflake entry — falls back to Redshift. (e) `utils/warehouse.py:351-359` Snowflake branch reads env vars only, no `warehouse_config` path. | Full set: new `SnowflakeConnection` class, factory registration, fleshed-out dialect rules + examples, `warehouse_config` parsing path. |
| 6 | Webapp Registry | **Unknown — not audited this pass** | Needs separate webapp audit. `WarehouseServiceProvider` enum already includes `SNOWFLAKE` in `gql-types.ts:3624` so dropdown likely shows it. Form-field validation may already exist. | TBD — short audit ticket. |
| 7 | Org CDK Ingestion Pipeline | **Shipped (but pattern-drift)** | `snowflake_ingestion.py` full stack with JWT lambda, parse API GW lambda, ~470 lines. Registered in `app.py:329` `{"SNOWFLAKE": snowflake_ingestion.snowflake_state_machine}`. S3 role wired in `post_deployment_scripts/update_s3_role.py:41,222-265`. | **Pattern drift**: Snowflake ingestion predates the workspace-secret-store pattern Synapse migrated to. Stack reads from deprecated Datapiary instead of `workspace_secret_store/{workspaceId}`. Optional migration to align both warehouses on the same source-of-truth. |

### Hard Limitations (today, before this work)

- Brightbot retrieval agent raises `ValueError("Unknown warehouse type: snowflake")` from `WarehouseConnectionFactory.create_connection`.
- LLM prompts fall back to Redshift dialect for Snowflake queries — produces invalid SQL (e.g. ANSI quoting passes but `LIMIT` injection regex is Redshift-shaped).
- OMD ingestion cannot pull Snowflake catalog metadata for a workspace — no source config registered.
- Workspace-secret-store path is not honored by the ingestion stack — credentials must live in two places.

### Gaps (summary)

- **Brightbot critical gap**: 1 class + 1 factory entry + 2 prompt entries + 1 config-path. The whole reason Longaeva can't go live today.
- **OMD ingestion source config gap**: 1 `@register_source` block.
- **Symmetric refactor (optional)**: `returnSnowflakeAdminSecrets` helper + ingestion-stack migration to `workspace_secret_store`.
- **Webapp audit gap**: short read-only audit needed to confirm UI surfaces work.

## Proposals / Solutions

### Recommended Approach

**Extend the Synapse pattern exactly.** No new architecture, no new abstractions. The pattern works; the audit confirmed it; the foundation for Snowflake is already partially built. The remaining work is:

1. **Mirror the Synapse implementation for the gaps** — same files, same shapes, swap `pymssql` for `snowflake-connector-python`, swap T-SQL dialect rules for Snowflake dialect rules, swap bracket-quoting for ANSI quoting.
2. **Defer the optional symmetric refactors** — `returnSnowflakeAdminSecrets` and ingestion-stack workspace-secret-store migration. These are correctness improvements, not blockers. They land in a second sprint after the critical gaps close.
3. **Webapp audit short ticket** — read-only confirmation that the UI works.

The crucial insight: **the existing Snowflake foundation is uneven but correct**. The destination handler (Layer 1), webhook adapter (Layer 2), OGM model, and ingestion stack (Layer 7) all work. The blocker is Layer 5 (brightbot). Close that and Longaeva goes live.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|---|---|---|---|
| **Full rewrite to align both warehouses on identical patterns** | Symmetry, lower long-term maintenance | 2-4 weeks vs 1 sprint, blocks Longaeva | Reject — symmetry is desirable but not urgent |
| **Add a new "Snowflake-specific" abstraction layer** | Could optimize for Snowflake idioms (clustering, micro-partitions) | Defeats the warehouse-agnostic pattern | Reject — pattern stays; Snowflake-specific perf tuning lives inside the connection class, not in a new abstraction |
| **Build only the brightbot side, defer OMD source config** | Smallest scope | OMD ingestion is part of the Longaeva enrollment workflow | Reject — OMD ingestion is in the trial AC |

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Brightbot Connection + Dialect | `brightbot` | New `SnowflakeConnection` class, factory registration, dialect prompts + examples, `warehouse_config` parsing, tests |
| OMD Ingestion Source Config | `brighthive-platform-core` | New `SnowflakeSourceConfig` in `openmetadata_ingestion_lambda/config_loader.py`, `main.py` service-type wiring |
| Webapp Registry audit | `brighthive-webapp` | Confirm dropdown + form-field rendering for `SNOWFLAKE` |
| Symmetric refactor (Phase 2, optional) | `brighthive-platform-core`, `brighthive-data-organization-cdk` | `returnSnowflakeAdminSecrets` helper + ingestion stack workspace-secret-store migration |

## Interface Contract

### Brightbot — SnowflakeConnection class (Layer 5)

```python
# brightbot/brightbot/tools/warehouse_connections.py
class SnowflakeConnection(WarehouseConnection):
    def __init__(self, connection_params: dict[str, Any]) -> None: ...
    def connect(self) -> Any: ...
    def execute_query(self, query: str) -> list[dict]: ...
    def rollback(self) -> None: ...
    def close_connection(self) -> None: ...

# Registration (mirrors Synapse at line 484):
CONNECTION_CLASSES: dict[str, type[WarehouseConnection]] = {
    "redshift": RedshiftConnection,
    "azure_synapse": SynapseConnection,
    "postgres": PostgresConnection,
    "snowflake": SnowflakeConnection,  # NEW
}
```

Driver: `snowflake-connector-python` (`uv add snowflake-connector-python`).

Auth: support both username/password (Longaeva's POC starter) and JWT/key-pair (production path; matches `destination_service/snowflake.ts` pattern).

SQL safety: same SELECT/SHOW/WITH/DESC/DESCRIBE/EXPLAIN allowlist as `SynapseConnection.execute_query`; multi-statement rejection on `;` in `rstrip(";")`.

### Brightbot — Dialect rules (Layer 5, prompts)

```python
# brightbot/brightbot/prompts/retrieval_agent_prompts.py
DIALECT_SYNTAX_RULES["snowflake"] = (
    "Only use Snowflake SQL. Use LIMIT (not TOP). Use double-quoted "
    'identifiers ("name") with case-sensitive matching — bare identifiers '
    "are folded to UPPER. Use ILIKE for case-insensitive matching. "
    "Use INFORMATION_SCHEMA for metadata, or SHOW commands for catalog "
    "introspection. Snowflake supports QUALIFY, MATCH_RECOGNIZE, and "
    "lateral FLATTEN — use them when appropriate."
)

DIALECT_EXAMPLES["snowflake"] = [
    {"good": 'SELECT * FROM "MY_SCHEMA"."MY_TABLE" LIMIT 10',
     "bad":  "SELECT TOP 10 * FROM [MY_SCHEMA].[MY_TABLE]"},
    {"good": "SELECT * FROM tbl WHERE col ILIKE '%foo%'",
     "bad":  "SELECT * FROM tbl WHERE LOWER(col) LIKE '%foo%'"},
    # ... 4-6 more, parallel to Synapse examples
]
```

### Brightbot — warehouse_config parsing (Layer 5)

```python
# brightbot/brightbot/utils/warehouse.py — Snowflake branch (currently :351-359)
# CURRENT: env-var only — SNOWFLAKE_ACCOUNT, SNOWFLAKE_DATABASE, ...
# TARGET: same warehouse_config-aware path as Synapse :291-349
elif warehouse_type == "snowflake":
    cfg = warehouse_config or {}
    return {
        "account":  cfg.get("account")  or os.getenv("SNOWFLAKE_ACCOUNT"),
        "database": cfg.get("database") or os.getenv("SNOWFLAKE_DATABASE"),
        "warehouse": cfg.get("warehouse") or os.getenv("SNOWFLAKE_WAREHOUSE"),
        "schema":   cfg.get("schema")   or os.getenv("SNOWFLAKE_SCHEMA"),
        "username": cfg.get("username") or os.getenv("SNOWFLAKE_USER"),
        "password": cfg.get("password") or os.getenv("SNOWFLAKE_PASSWORD"),
        "role":     cfg.get("role")     or os.getenv("SNOWFLAKE_ROLE"),
        # optional: private_key for JWT auth (Phase 2)
    }
```

### Platform-Core — OMD ingestion source config (Layer 3)

```python
# brighthive-platform-core/openmetadata_ingestion_lambda/config_loader.py
# Mirror SynapseSourceConfig at lines 156-209
@register_source("snowflake", required_fields=["account", "username", "password", "database", "warehouse"])
class SnowflakeSourceConfig(SourceConfig):
    def to_omd_config(self) -> dict:
        return {
            "type": "snowflake",
            "serviceName": f"{self._uuid.lower()}_snowflake_ingestion",
            "serviceConnection": {"config": {
                "type": "Snowflake",
                "scheme": "snowflake",
                "account": self.account,
                "username": self.username,
                "password": self.password,
                "database": self.database,
                "warehouse": self.warehouse,
                "role": self.role,
            }},
            "sourceConfig": {"config": {
                "type": "DatabaseMetadata",
                "schemaFilterPattern": {"excludes": ["INFORMATION_SCHEMA.*", "PUBLIC.*"]},
            }},
        }
```

```python
# brighthive-platform-core/openmetadata_ingestion_lambda/main.py:38
# Service-type map already handles "snowflake" → DatabaseServiceType.Snowflake via OMD-default;
# verify and add explicit entry mirroring Synapse :38.
```

## Invariants

1. WHEN any brightbot agent requests a Snowflake warehouse, THE `WarehouseConnectionFactory` SHALL return a `SnowflakeConnection` instance — never raise.
2. SQL emitted by the retrieval agent for Snowflake SHALL use Snowflake dialect (LIMIT, ILIKE, ANSI double-quoted identifiers) — never Redshift fallback.
3. WHEN a workspace stores Snowflake credentials in `workspace_secret_store/{workspaceId}.warehouses[type=SNOWFLAKE]`, brightbot SHALL read them through `warehouse_config`, not require env vars.
4. WHEN OMD ingestion runs for a Snowflake source, THE `SnowflakeSourceConfig` SHALL produce a valid `DatabaseService` payload that OMD accepts.
5. The `CONNECTION_CLASSES` dict in `warehouse_connections.py` SHALL stay alphabetically sorted by key (style invariant).
6. New Snowflake connection class SHALL pass the same security tests Synapse passes: multi-statement rejection, DDL rejection, DELETE/INSERT rejection.
7. WHEN a developer adds a new warehouse type beyond Snowflake, they SHALL touch the same 7 layers (or document the layers skipped and why).

## Acceptance Criteria

### Phase 1 — Critical gaps (gates Longaeva trial)

```gherkin
Feature: Snowflake — brightbot can execute SQL

  Scenario: Retrieval agent queries Snowflake
    Given a workspace with type=SNOWFLAKE in workspace_secret_store
    When the retrieval agent generates SQL for a request
    Then the SQL uses LIMIT (not TOP)
    And the SQL uses double-quoted ANSI identifiers
    And the SQL executes against Snowflake successfully
    And no ValueError is raised by WarehouseConnectionFactory

  Scenario: Quality agent queries Snowflake
    Given a Snowflake-backed asset
    When build_sample_query is called with warehouse_type="snowflake"
    Then the query uses LIMIT 5000 (not TOP 5000)
    And the table name uses ANSI double-quoting

  Scenario: SnowflakeConnection rejects DDL/DML
    Given a SnowflakeConnection instance
    When execute_query is called with "DELETE FROM tbl"
    Then a security error is raised
    And no statement is executed

  Scenario: Multi-statement rejection
    When execute_query is called with "SELECT 1; SELECT 2"
    Then a security error is raised
```

- [ ] Phase 1 scenarios above pass as integration tests
- [ ] `tests/unit/test_snowflake_warehouse.py` exists and mirrors `test_synapse_warehouse.py` (factory routing, params parsing, prompt registry, secrets validation)
- [ ] `DIALECT_SYNTAX_RULES["snowflake"]` and `DIALECT_EXAMPLES["snowflake"]` have full detail (not stubs)
- [ ] `warehouse_config` path works without env vars
- [ ] OMD `@register_source("snowflake", ...)` block exists and is exercised by a test
- [ ] Webapp audit ticket closed (UI confirmed working)

### Phase 2 — Symmetric refactors (optional, post-Longaeva)

- [ ] `returnSnowflakeAdminSecrets(workspaceId)` helper added to `validators.ts` (mirrors `returnSynapseAdminSecrets`)
- [ ] `SnowflakeIngestionStack` migrated to read from `workspace_secret_store/{workspaceId}` (away from deprecated Datapiary)
- [ ] Pattern-drift documented in `warehouse-agnostic-architecture.md` as resolved

## Observability Contract

Spans:
- **`brightbot.warehouse.connect`** — `warehouse.type=snowflake`, `warehouse.account`, `workspace.id`, `connection.duration_ms`, `connection.success` (bool)
- **`brightbot.warehouse.execute_query`** — `warehouse.type=snowflake`, `sql.length`, `sql.rejected_reason` (multi_statement | ddl | dml | none), `query.duration_ms`, `result.row_count`

Log events:
- `warehouse.snowflake.connected`
- `warehouse.snowflake.query_rejected` — includes `reason`
- `warehouse.snowflake.query_failed` — includes `snowflake.error_code` if present

Metrics:
- `brighthive.warehouse.connections_total{type=snowflake, success}`
- `brighthive.warehouse.queries_total{type=snowflake, rejected}`
- `brighthive.warehouse.query_duration_ms{type=snowflake}` histogram

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| `warehouse-agnostic-architecture.md` spec (BH-172) | Blueprint | Approved |
| Azure Synapse implementation (PRs #706, #707, #719, #720, #722, #724, #433, #139, #149) | Reference pattern | Shipped |
| Snowflake destination handler in platform-core | Foundation | Shipped (PR predates audit) |
| `SnowflakeAdapter` in OMD webhook lambda | Foundation | Shipped |
| `SnowflakeIngestionStack` in org-cdk | Foundation | Shipped (pattern-drift noted) |
| Longaeva trial (June 2026) | Driver | Pre-trial |

## Ticket Breakdown

### Phase 1 — Critical (blocks Longaeva, ~2 weeks)

| Ticket | Summary | Points | Layer | Owner candidate |
|---|---|---|---|---|
| **BH-SF1** | feat(brightbot): SnowflakeConnection class + factory registration | 3 | 5 | Marwan or Ahmed |
| **BH-SF2** | feat(brightbot): Snowflake dialect rules + examples in retrieval agent prompts | 1 | 5 | Marwan |
| **BH-SF3** | feat(brightbot): warehouse_config-aware Snowflake branch in warehouse.py | 1 | 5 | Marwan |
| **BH-SF4** | test(brightbot): tests/unit/test_snowflake_warehouse.py mirror of Synapse tests | 2 | 5 | QA / Marwan |
| **BH-SF5** | feat(platform-core): SnowflakeSourceConfig in OMD ingestion lambda | 2 | 3 | Ahmed |
| **BH-SF6** | audit(webapp): confirm Snowflake dropdown + form fields render | 1 | 6 | Harbour |
| **BH-SF7** | feat(brightbot): data_profiler Snowflake-specific branches if any needed (likely no-op) | 1 | 5 | Marwan |

**Phase 1 total: 11 points**

### Phase 2 — Symmetric refactors (post-Longaeva, ~1.5 weeks)

| Ticket | Summary | Points | Layer |
|---|---|---|---|
| **BH-SF8** | refactor(platform-core): returnSnowflakeAdminSecrets helper for symmetry | 2 | 1 |
| **BH-SF9** | refactor(org-cdk): SnowflakeIngestionStack reads workspace_secret_store, not Datapiary | 3 | 7 |
| **BH-SF10** | docs(spec): update warehouse-agnostic-architecture.md to mark Snowflake fully aligned | 1 | — |

**Phase 2 total: 6 points**

**Grand total: 17 points across 10 tickets**

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Snowflake driver dependency conflicts with brightbot's existing `cryptography` pinning | Medium | Medium | Test in isolated venv first; pin `snowflake-connector-python` carefully; check `cryptography`, `pyOpenSSL` overlap |
| Auth path divergence (password vs JWT vs SSO) — Longaeva may want SSO | Low | High | Phase 1 ships username/password; JWT/SSO is Phase 2 work mirroring `destination_service/snowflake.ts` pattern |
| Pattern-drift in `SnowflakeIngestionStack` causes silent secret-source mismatch | Already present | Medium | Document the drift in Phase 1; close in Phase 2 |
| Dialect prompt rules don't cover edge cases (QUALIFY, lateral FLATTEN, time travel) | Medium | Low | Ship core dialect rules first; iterate from observed retrieval-agent failures during Longaeva trial |
| OMD `Snowflake` service-type assumption is wrong in OMD client version we use | Low | Low | Verify against deployed OMD version (`requirements.txt` lock) before merging BH-SF5 |

## Related

- **Blueprint spec**: `warehouse-agnostic-architecture.md` (BH-172)
- **Companion**: `warehouse-extensibility-pattern.md` (Draft)
- **Sister spec**: `azure-synapse-full-integration.md` (reference implementation)
- **Driving trial**: `clients/trials/longaeva/overview.md`
- **Pre-trial epic**: BH-526 (Longaeva 14-day pre-trial execution)
- **Quality rules epic** (parallel): BH-503 (Configurable Quality Agent)
