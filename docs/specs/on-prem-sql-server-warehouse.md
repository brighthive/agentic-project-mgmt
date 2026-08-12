---
title: "On-Premise SQL Server Support for BrightAgent"
epic: "BH-1036"
author: "drchinca"
status: "Draft"
created: "2026-08-11"
generates: "tickets"
tags: ["warehouse", "sql-server", "dbt", "loop-capital"]
related:
  features: []
  pocs: []
  bedrock: []
---

# On-Premise SQL Server Support for BrightAgent

> Full contract: `~/.claude/rules/spec-driven.md`. Sections 7–9 are conditional — keep them only
> when they apply. §10 is mandatory.

## 1. Context

BrightAgent's engineering agent (`brightbot`) can't yet fully represent an on-premise SQL Server
as its own warehouse: `WarehouseType` has no `"sql_server"` member, so a SQL Server secret is
silently aliased into `"azure_synapse"` before it reaches the connection factory. Separately, dbt
Cloud — the only pipeline runner `brightbot` currently supports — has no first-party destination
for SQL Server, so there is no way for the engineering agent to run dbt transformations against an
on-prem/no-cloud SQL Server target at all. Both gaps are blocking real support for the Loop
Capital trial, whose production stack is exactly this shape (on-prem SQL Server, no cloud
warehouse, dbt run outside dbt Cloud).

### Use Case / Goal

When a workspace's only warehouse is a SQL Server instance (cloud EC2, on-prem, or Azure VM), the
engineering agent should classify, connect to, profile, and monitor it as `sql_server` — not
misreport it as Synapse — and should be able to execute dbt builds against it via a self-hosted
runner when dbt Cloud isn't in the picture. Success: Loop Capital's stack profiles correctly and
dbt jobs run end-to-end against our EC2 SQL Server stand-in, with zero code path assuming a cloud
warehouse or dbt Cloud.

### How It Works Today

- `brightbot/brightbot/utils/warehouse_types.py:20` — `WarehouseType = Literal["redshift",
  "snowflake", "azure_synapse", "postgres", "databricks"]`. No `"sql_server"` entry.
- Same file, line 34 — `SQL_SERVER_SECRET_TYPE: Final[str] = "SQL_SERVER"` already exists as a
  *secret* type, but `TDS_SECRET_TYPES` (lines 46-48) groups it with `AZURE_SYNAPSE_SECRET_TYPE`
  and `SYNAPSE_AZURE_SECRET_TYPE` as "SQL-Server-shaped" secrets that all normalize to the
  `azure_synapse` `WarehouseType` via `warehouse_type_from_secret()`
  (`brightbot/brightbot/utils/warehouse.py:178-187`).
- `brightbot/brightbot/tools/warehouse_connections.py:675-681` — `CONNECTION_CLASSES` registry has
  no `sql_server` key; a SQL Server secret resolves to `SynapseConnection` (lines 285-480,
  `pymssql`-based) purely because of the alias above.
- Pipeline execution: `brightbot/brightbot/pipelines/adapters/` contains only `dbt_cloud/`,
  `databricks/`, `snowflake_native/` runner adapters. `DbtCloudRunner`
  (`brightbot/brightbot/pipelines/adapters/dbt_cloud/runner.py:72,165,202`) exclusively drives dbt
  Cloud's HTTP job API — there is no local `dbt` CLI/subprocess execution path anywhere in
  `brightbot`.
- **Platform Core is already ahead of brightbot here.** BH-1107 shipped a first-class
  `WarehouseServiceProvider.SQL_SERVER` GraphQL enum value, distinct from `AZURE_SYNAPSE`
  (`brighthive-platform-core/src/graphql/schema/warehouse-provider-typedefs.ts:23`), with an
  explicit comment: *"GC-15 (Loop Capital) already proved the … SQL_SERVER is its own provider"*
  (same file, lines 8-11). `warehouse-provider-mapping.ts:22` defines
  `MSSQL_FAMILY_PROVIDERS = ["AZURE_SYNAPSE", "SQL_SERVER"]` for shared-TDS-shape lookups, and both
  map to the same underlying `"Mssql"` service (`warehouse-service.ts:279`,
  `byow-preview.ts:353`) — i.e. platform-core already treats SQL Server as its own provider that
  *shares* connection mechanics with Synapse, exactly the shape brightbot needs to catch up to.
  brighthive-webapp/GraphQL clients can already request `SQL_SERVER`; brightbot cannot yet honor
  it.
- `brighthive-platform-core/src/graphql/schema/schema.graphql:289-293` —
  `TransformationServiceProvider` enum has only `DBT_CLOUD`, `DEEPNOTE`, `SNOWFLAKE`. No
  self-hosted/dbt-Core value exists at the API layer either.
- Existing Jira tickets: **BH-1075** ("new sql_server WarehouseType/WarehouseServiceProvider
  connection type", parent BH-1036, status Needs Refinement) already tracks the brightbot-side
  gap. **BH-1107** (parent BH-115, status Needs Refinement) tracks the platform-core side, whose
  code is already merged per the citations above even though the ticket isn't closed — Jira status
  and code state have drifted apart here; don't infer one from the other.

### Hard Limitations

- brightbot cannot distinguish a SQL Server warehouse from an Azure Synapse warehouse at the
  `WarehouseType`/connection-factory level today — every profiling result, capability check, and
  monitoring signal for a SQL Server target is currently attributed to `azure_synapse`.
- dbt Cloud has no MSSQL/SQL Server destination adapter (a dbt Cloud/vendor limitation, not
  something brightbot can configure around) — there is no cloud-hosted way to run dbt against SQL
  Server today, on-prem or otherwise.
- We do not have Loop Capital's real server DNS/IP, a scoped login, the in-scope DB list, or
  SSISDB/raw `.dtsx`/`.rdl` samples — all five are listed "Not started" in
  `clients/trials/loopcapital/TRIAL_STATEMENT.md` §3. This spec's acceptance criteria are therefore
  validated against Brighthive's own EC2 SQL Server stand-in
  (`clients/trials/loopcapital/infra/loopcapital_sqlserver_ec2/stack.py`), never against a live
  connection to Loop Capital's real, still-unprovisioned server.

### Gaps

- No `sql_server` `WarehouseType` literal, no registry entry, no dedicated connection class —
  only an aliasing shim.
- No `PipelineRunner` adapter capable of executing dbt outside dbt Cloud (local `dbt` Core
  subprocess execution path is entirely greenfield in brightbot).
- No capability-negotiated fallback: if a workspace's only warehouse can't be reached by dbt
  Cloud, brightbot has no typed "not supported, here's why" response — it would either
  misclassify the warehouse or fail the dbt Cloud call with no explanation.
- No `TransformationServiceProvider` GraphQL value for self-hosted/local dbt execution (phase 2,
  platform-core surface — see Out of Scope).

## 2. Interface Contract (MDE)

```python
# brightbot/brightbot/utils/warehouse_types.py
WarehouseType = Literal["redshift", "snowflake", "azure_synapse", "sql_server", "postgres", "databricks"]
SQL_SERVER: Final[WarehouseType] = "sql_server"

# TDS_SECRET_TYPES no longer collapses SQL_SERVER into azure_synapse; warehouse_type_from_secret()
# maps SQL_SERVER_SECRET_TYPE -> SQL_SERVER, and {AZURE_SYNAPSE_SECRET_TYPE, SYNAPSE_AZURE_SECRET_TYPE} -> AZURE_SYNAPSE.

# brightbot/brightbot/tools/warehouse_connections.py
CONNECTION_CLASSES: dict[WarehouseType, type[WarehouseConnection]] = {
    ...,
    SQL_SERVER: SqlServerConnection,  # new class; shares TDS/pymssql mixin with SynapseConnection
}

# brightbot/brightbot/pipelines/adapters/dbt_core/runner.py (new)
class DbtCoreRunner(PipelineRunner):  # implements brightbot/brightbot/pipelines/core/port.py Protocol
    def capabilities(self) -> frozenset[RunnerCapability]: ...
    async def run_segment(self, *, segment: PipelineSegment, ctx: RequestContext) -> RunResult: ...
    async def run_on_ref(self, *, ref: str, ctx: RequestContext) -> RunResult: ...
```

```
# Runner selection (engineering agent decision)
GIVEN a workspace whose only registered warehouse has WarehouseType == "sql_server"
WHEN the engineering agent needs to execute a dbt build
THEN it SHALL select DbtCoreRunner, never DbtCloudRunner
  Response (typed): RunResult | RunnerCapabilityError{reason: "dbt_cloud_unsupported_target" | "dbt_core_unavailable"}
```

## 3. Invariants (DbC)

- WHEN a secret's type is `SQL_SERVER_SECRET_TYPE`, THE System SHALL classify `warehouse_type` as
  `"sql_server"`, never `"azure_synapse"`.
- `SqlServerConnection`'s TDS/pymssql wire behavior SHALL be identical to `SynapseConnection`'s
  (same driver, same TLS/tds_version fallback, same read-only enforcement) — no regression to
  existing Synapse connections from the refactor that extracts the shared TDS logic.
- WHEN a workspace's only reachable warehouse has no dbt Cloud destination support, THE System
  SHALL route dbt execution to `DbtCoreRunner` if configured, ELSE return a typed
  `RunnerCapabilityError` — it SHALL NOT silently fail or misattribute the run to dbt Cloud.
- `DbtCoreRunner` SHALL execute only the validated `dbt` subcommand + allowlisted flags passed
  through the `PipelineSegment`/`ref` contract — no shell interpolation of untrusted strings
  (command args passed as an argv list, never through `shell=True`).
- `DbtCoreRunner` SHALL NOT be selected for any warehouse type that already has dbt Cloud support
  configured — it is a fallback, not a default.

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: On-premise SQL Server warehouse support

  Scenario: SQL Server secret classifies correctly
    Given a workspace secret of type SQL_SERVER_SECRET_TYPE
    When the engineering agent resolves warehouse_type_from_secret()
    Then the resolved WarehouseType is "sql_server", not "azure_synapse"

  Scenario: SQL Server connection profiles the EC2 stand-in
    Given the Brighthive-owned EC2 SQL Server stand-in (LoopCapitalAM database)
    When the engineering agent runs list_tables() and list_databases() via SqlServerConnection
    Then results match the same shape SynapseConnection would have returned pre-refactor

  Scenario: dbt Cloud is not attempted against a SQL Server-only workspace
    Given a workspace whose only warehouse has WarehouseType "sql_server"
    When the engineering agent needs to run a dbt build
    Then DbtCoreRunner is selected, and DbtCloudRunner is never invoked

  Scenario: dbt Core runner executes a real build against the EC2 stand-in
    Given DbtCoreRunner configured against the EC2 SQL Server stand-in
    When run_on_ref() is called with a valid dbt project ref
    Then the dbt build completes and RunResult reports success with real row/model counts

  Scenario: Capability gap surfaces a typed error, not a silent failure
    Given a workspace whose only warehouse is "sql_server" and no DbtCoreRunner is configured
    When the engineering agent needs to run a dbt build
    Then it returns RunnerCapabilityError(reason="dbt_core_unavailable"), not an unhandled exception

  Scenario: Existing Synapse connections are unaffected
    Given a workspace secret of type AZURE_SYNAPSE_SECRET_TYPE
    When the engineering agent resolves warehouse_type_from_secret()
    Then the resolved WarehouseType is still "azure_synapse"
```

## 5. Out of Scope

- Connecting to Loop Capital's real on-prem server — DNS/IP, credentials, and DB scope are
  client-side blockers, all "Not started" per `TRIAL_STATEMENT.md` §3. Nothing in this spec
  requires or attempts that connection.
- Copying any real Loop Capital data, dbt pipelines, SSIS/SSRS files, or credentials into
  Brighthive-owned infrastructure. All validation here uses our own synthetic EC2 stand-in.
- Sandbox fixture realism improvements (richer synthetic dbt/SSIS/SSRS fixtures under
  `clients/trials/loopcapital/sandbox/`) — tracked as a separate, non-blocking follow-on ticket;
  it's fixture work, not an interface/behavior change.
- `TransformationServiceProvider` GraphQL enum addition (self-hosted/dbt-Core value) on
  `brighthive-platform-core` — phase 2. brightbot's `DbtCoreRunner` can ship and be exercised
  internally before the webapp/API need to expose the choice to users.
- Any change to `brighthive-webapp` — no UI work in this spec.

## 6. Dependencies

| Dependency | Type | Status |
|---|---|---|
| BH-1075 (`sql_server` WarehouseType/WarehouseServiceProvider, brightbot) | Non-blocking (this spec supersedes/refines it — same ticket, don't duplicate) | Needs Refinement |
| BH-1107 (`SQL_SERVER` provider, platform-core) | Non-blocking (code already merged; ticket status stale) | Needs Refinement (code shipped) |
| EC2 SQL Server stand-in (`loopcapital_sqlserver_ec2` stack) | Blocking (validation target for §4 scenarios) | Live |
| Loop Capital real server access (DNS/IP, login, DB list, SSISDB/files) | Non-blocking to this spec | Not started (client-side) |

## 7. Correctness Properties

### Property 1: No shell injection through DbtCoreRunner

*For any* `PipelineSegment`/`ref` value passed to `DbtCoreRunner.run_segment`/`run_on_ref`, the
subprocess invocation SHALL use an argv list with no shell interpolation, so no input value can
alter the invoked command.

**Validates: §3 Invariant "DbtCoreRunner SHALL execute only the validated dbt subcommand...", §4
Scenario "dbt Core runner executes a real build against the EC2 stand-in"**

## 8. Eval Criteria

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| RunnerSelectionEvaluator | engineering-agent dbt-execution routing node | GATE | 100% correct runner chosen for warehouse_type="sql_server" fixtures | Deterministic |

## 9. Observability Contract

- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=warehouse_connect` (`warehouse.type=sql_server`)
- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=dbt_core_run`
- **Attributes**: `workspace.id`, `warehouse.type`, `runner.kind` (`dbt_cloud` | `dbt_core`), `gen_ai.usage.input_tokens` (if LLM-mediated routing)
- **Log events**: `warehouse_classification.sql_server`, `dbt_core_run.started`, `dbt_core_run.success`, `dbt_core_run.failed`, `runner_capability.unavailable`
- **Metrics**: none

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brightbot` | `brightbot/tests/` (unit/integration) + `brightbot/brightbot/evals/` | L0: one case asserting `"sql_server"` is a valid `WarehouseType` literal and registry key. L1: one case per §4 scenario asserting `DbtCoreRunner` vs `DbtCloudRunner` routing. L2: real-behavior test connecting `SqlServerConnection` to the EC2 stand-in (list_tables/list_databases), and a real `DbtCoreRunner.run_on_ref()` executing an actual dbt build against it — both real-backend, not mocked, per `test-behavior-real.md`. |
| `brighthive-e2e` | `brighthive-e2e/e2e/` | One feature test: workspace with `sql_server`-only warehouse triggers a real dbt build via the engineering agent end-to-end against the EC2 stand-in. |

**Real-behavior requirement**: the L2 brightbot cases above must hit the real EC2 SQL Server
stand-in and a real `dbt` process — construct-only tests asserting the Literal/dict shape don't
satisfy this row.

Before opening the implementation PR: run `brightbot`'s full suite + evals and the new
`brighthive-e2e` feature test, confirm each new §2/§3/§4/§8 entry has a corresponding new test
case, and confirm all suites are green.

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Warehouse types & connections | `brightbot` | Add `sql_server` `WarehouseType`, `SqlServerConnection` (shares TDS mixin with `SynapseConnection`), registry entry, secret-resolution fix |
| Pipeline execution | `brightbot` | New `DbtCoreRunner` adapter under `pipelines/adapters/dbt_core/`, capability-negotiated fallback from `DbtCloudRunner` |
| Warehouse provider surface | `brighthive-platform-core` | Already shipped (BH-1107) — no change required for this spec; confirm no regression |
| Sandbox target | `agentic-project-mgmt` (`clients/trials/loopcapital/sandbox/`, `infra/loopcapital_sqlserver_ec2`) | Validation target only, no changes required by this spec |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|---|---|---|---|
| BH-1075 | Refine and implement: add `sql_server` WarehouseType, `SqlServerConnection`, registry entry, fix secret-type aliasing | 5 | BH-1036 |
| — | Add `DbtCoreRunner` PipelineRunner adapter (local dbt CLI execution, capability-negotiated) | 5 | BH-1036 |
| — | Add capability-negotiated fallback + typed `RunnerCapabilityError` in dbt-execution routing | 3 | BH-1036 |
| — | Real-behavior L2 tests: SqlServerConnection + DbtCoreRunner against EC2 stand-in | 3 | BH-1036 |
| — | brighthive-e2e feature test: sql_server-only workspace end-to-end dbt build | 2 | BH-1036 |

## Related

- **Existing tickets**: BH-1075, BH-1107, BH-1036 (epic)
- **Trial docs**: `docs/specs/loopcapital-trial-readiness.md`, `clients/trials/loopcapital/TRIAL_STATEMENT.md`, `clients/trials/loopcapital/overview.md` (Track E)
- **Follow-on (out of scope)**: sandbox fixture realism under `clients/trials/loopcapital/sandbox/`
