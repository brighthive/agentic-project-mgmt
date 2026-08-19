---
title: "BrightAgent Local Plugin — v1"
epic: "BH-XXX"
author: "drchinca"
status: Parked
created: "2026-08-12"
generates: "epic"
tags: ["agent-plugins", "mcp", "local-plugin", "loop-capital", "offline", "sql-server"]
related:
  features: []
  pocs: []
  bedrock: []
roadmap: closed — half its scenarios @blocked-pending-confirmation
---

# BrightAgent Local Plugin — v1

> Full contract: `~/.claude/rules/spec-driven.md`. Sections 7–9 are conditional — keep them only
> when they apply. §10 is mandatory. Engine-agnostic-by-default rule (`docs/CLAUDE.md`) applies:
> the on-prem connection is a port with SQL Server as the first adapter, not a bespoke connector.

## 1. Context

Loop Capital's real environment (three SQL Servers — Dev/UAT/Prod, each with multiple databases,
no cloud warehouse, no dbt Cloud) can't use BrightAgent's governed context today because the MCP
server is cloud-only: every tool call requires a live Cognito-federated session validated against
Platform Core GraphQL (`brightbot/brightbot/mcp/auth.py:1-16`). Frank's actual workflow — building
database projects with Codex against Dev/UAT, and diagnosing failed SQL Agent jobs by hand today
— has no governed-context assist, and no metadata/lineage/quality signal ever reaches Brighthive's
cloud because nothing currently bridges an on-prem-only environment to it. This spec defines a
locally-run BrightAgent package, conformant to the open **Agent Plugins 1.0.0** standard
(`agent-plugins.org`), that runs the governed-context surface and data-engineering skills entirely
against local files + a single on-prem SQL Server, syncing only metadata (never data) back to
Brighthive Cloud.

### Use Case / Goal

Two goals, both from Frank's own workflow description:

1. **Development** — building data models against current on-prem state, faster and more
   accurately, with Codex/Claude Code as the interface (create tables/procs/views as a SQL
   Database Project, publish to Dev → UAT → Prod, whole project including a .NET/C# application
   pushed to GitHub).
2. **Operations** — instead of Frank getting a bare failure email from a SQL Agent job and
   manually opening SSMS/Azure webUI to find the error code, BrightAgent connects with his
   credentials, runs a read-only diagnostic, pinpoints which stored proc/SSIS package failed, and
   proposes a fix — without ever installing an agent on the SQL Server or modifying a running job's
   source.

Success: Codex (and, once confirmed, Claude Code) loads this plugin, the developer gets governed
catalog/glossary/lineage context locally, skills profile and diagnose the local SQL Server, and
zero data rows ever leave the box.

### How It Works Today

- **BrightAgent's MCP server is real but cloud-only.** `brightbot/brightbot/mcp/server.py:11`
  builds a `FastMCP` instance, mounted at `/bh-mcp` on the main FastAPI app
  (`brightbot/http/app.py:60,119`). Auth is two-layer: Cognito Hosted UI federated to the
  customer's IdP (configured in `brighthive-platform-core` CDK), then the bearer JWT is validated
  against Platform Core GraphQL's `currentUser` (`brightbot/brightbot/mcp/auth.py:1-16`). The only
  non-cloud path is `LOCAL_DEV_USER`/`is_local_dev_mode` (`auth.py:30-33`) — an internal dev
  shortcut, not a supported offline product mode.
- **The tool surface differs from what's commonly assumed.** Real tools: `get_workspace_context`
  and `get_schema_details` (`brightbot/brightbot/mcp/tools/workspace_governance.py:161-286`).
  Names like `analyze_change_impact`, `search_catalog`, `query_governed_data`, `get_asset_quality`,
  `list_policies`, `request_quality_suite`, `propose_transformation`, `register_data_product` do
  **not** exist under those names — closest real analogues are `list_workspace_policies`,
  `discover_data_assets`, `analyze_dtsx_package`, `execute_library_quality_rules`,
  `register_transformation` (`brightbot/brightbot/mcp/server.py:56-150`, several gated behind
  default-off `FeatureFlag`s). `get_lineage` exists only as a name BrightAgent calls *on*
  OpenMetadata's own MCP server (`brightbot/brightbot/tools/mcp/servers/openmetadata_config.py:64-65`),
  not a tool BrightAgent itself exposes.
- **A portable skills convention already ships.** `brightbot/brightbot/skills/system/{ssis-diagnostics,
  ssrs-diagnostics,storage-optimization,xsd-table-schema,xsd-nested-document}/SKILL.md` — YAML
  frontmatter (`name`, `description`, `affinity`, `priority`) + markdown body referencing a tool
  call, e.g. `ssis-diagnostics/SKILL.md:1-6` → `analyze_dtsx_package`. This is reusable, not
  greenfield, and is a different thing from Claude Code's own `.claude/skills/` directory.
- **No "agentless" read-only SQL Server pattern exists under that name.** Grepped
  `../brightbot` and `clients/trials/loopcapital/` for "agentless" — zero matches. The read-only,
  no-agent-installed-on-target connection this spec needs is new work, built on the
  `WarehousePort`/`SqlServerConnection` adapter from `docs/specs/on-prem-sql-server-warehouse.md`
  (§2 of that spec) — this spec reuses that port rather than inventing a second connector.
- **No dbt-sqlserver adapter is vendored anywhere.** Grepped for `dbt-sqlserver`/`dbt_sqlserver` —
  zero matches; only `dbt-snowflake`/`dbt-postgres` references exist in test/lineage code. Ties
  directly to [`on-prem-sql-server-warehouse.md`](./on-prem-sql-server-warehouse.md)'s `DbtCoreRunner` gap (dbt Cloud cannot target
  SQL Server at all).
- **agent-plugins.org is real; some proposal claims about it are not corroborated.** Verified via
  direct fetch: the manifest schema requires only `$schema` + `name` (additional properties
  disallowed) — confirmed against `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`.
  The two-component-type claim (Agent Skills in `skills/`, MCP servers via `mcp.json`) is
  confirmed from the homepage text. **However**: the specific "launch-supported clients" list
  (ChatGPT/Codex/Cursor/GitHub Copilot/Kiro/VS Code) and the claim that Claude Code is excluded
  are **not found anywhere on the fetched site** — the only named organizations are Technical
  Steering Committee members (Amazon, Cursor, Microsoft, OpenAI, Vercel); no client-application
  support matrix exists on the pages fetched to check Claude Code against. Treat §0's "dual-package
  for Claude Code" requirement as **unverified**, not a confirmed constraint, until re-checked
  against `agent-plugins.org/client-implementers` (or equivalent) at spec-approval time — building
  a Claude-Code-native wrapper based on an unsubstantiated exclusion claim is exactly the kind of
  premise this rule set (`test-behavior-real.md`) exists to catch.

### Hard Limitations

- No offline/local auth path exists in brightbot's MCP server today — every tool call assumes a
  live Cognito + Platform Core round trip. This is the single largest blocker to "local-cache mode."
- No zero-copy sync channel (context down / metadata-lineage-quality up) exists anywhere in
  brightbot or platform-core — it would be entirely new infrastructure.
- No local governance degradation path exists — today's write-gate tools (e.g.
  `register_transformation`) assume an always-on cloud connection; there is no "local dbt PR +
  queued cloud review" mode.
- dbt Cloud cannot target SQL Server (established in [`on-prem-sql-server-warehouse.md`](./on-prem-sql-server-warehouse.md)) — the
  `dbt-model-proposal` skill inherits this limitation until `DbtCoreRunner` ships.
- We do not have Loop Capital's real Dev/UAT/Prod server details — same client-side blockers
  listed in `TRIAL_STATEMENT.md` §3 apply here. This spec is validated against a local Docker SQL
  Server / the existing EC2 stand-in, never a live connection to Frank's real servers.
- The T-SQL dialect coverage of BrightAgent's existing NL→query generator against on-prem SQL
  Server specifically has **not been verified by this spec's research** (carried over from the
  proposal doc as an open question, not a confirmed fact) — flagged in Dependencies, not asserted.

### Gaps

- Local/offline auth mode for `brightagent-context` MCP server (net new).
- Zero-copy sync channel, both directions (net new).
- Local governance degradation mode (net new).
- `mssql-local` MCP server: read-only T-SQL/SSMS transactions over the on-prem connection,
  reusing the `WarehousePort`/`SqlServerConnection` adapter (net new wiring, not net new
  connection logic).
- Root plugin packaging (`plugin.json`, `mcp.json`) + Codex wiring (net new).
- Claude Code loading path — blocked on the unverified exclusion claim above; needs its own
  investigation before committing to a native-wrapper design.
- New skills: `sqlserver-health`, `nl-to-tsql-query`, `change-impact`, `dbt-model-proposal` — the
  first three can likely follow the existing `SKILL.md` convention directly; `dbt-model-proposal`
  is blocked on the `DbtCoreRunner`/dbt-sqlserver adapter gap.
- Physical home for the plugin package itself is undecided — neither `brightbot` nor
  `agentic-project-mgmt` is described anywhere as the customer-facing plugin package location;
  this needs a decision before implementation (see Dependencies).

## 2. Interface Contract (MDE)

```
# Port (this spec's on-prem connection is NOT a new connector — it reuses the port from
# docs/specs/on-prem-sql-server-warehouse.md):
WarehousePort.capabilities() -> frozenset[Capability]   # SqlServerConnection is the adapter

# Portable plugin manifest (root, confirmed shape via agent-plugins.org schema fetch)
plugin.json:
  { "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": "brightagent-local" }

# Portable MCP config (root) — shape inferred from homepage text, [CONFIRM] full field schema
mcp.json:
  {
    "mcpServers": {
      "brightagent-context": { "command": "brightagent-context", "args": ["--mode", "local", "--cache", "${BRIGHTAGENT_CACHE}"] },
      "mssql-local":         { "command": "mssql-local-mcp",     "args": ["--dialect", "tsql", "--read-default"] }
    }
  }

# Portable skill (extends the EXISTING convention at brightbot/brightbot/skills/system/*/SKILL.md)
skills/sqlserver-health/SKILL.md:
  ---
  name: sqlserver-health
  description: "Diagnose SQL Agent job failures, disk pressure, blocked/long-running queries"
  affinity: [analyst]
  priority: 80
  ---

# New local-cache auth mode (net new, distinct from mcp/auth.py's Cognito path)
BRIGHTAGENT_MODE=local-cache
  Request:  MCP tool call with no Authorization header (local stdio transport)
  Response: served from context-cache/ files; 4xx if a tool requires cloud-only capability
```

## 3. Invariants (DbC)

- WHILE running in local-cache mode, THE System SHALL NOT transmit row-level data across the sync
  channel — only metadata, lineage edges, and quality results cross the boundary.
- WHEN `mssql-local` is configured without an explicit write-gate override, THE System SHALL
  execute read-only T-SQL only — mirroring `SynapseConnection`'s existing read-only enforcement
  (`warehouse_connections.py:404-420`) as the enforcement precedent, applied identically here.
- WHEN the confirmed-safe slice is deployed (Codex, offline, no sync), THE System SHALL require
  zero live Brighthive-cloud connectivity for skill execution against the local SQL Server.
- IF a skill or MCP tool call requires a capability outside the confirmed-safe slice (sync,
  governance write, Claude Code native loading), THEN THE System SHALL return a typed
  "capability not available in local-only mode" response — never a silent no-op or a fabricated
  success.
- `mssql-local-mcp` SHALL NOT require any agent, extended stored procedure, or service installed
  on the target SQL Server — the connection is a standard TDS client connection only.

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: BrightAgent Local Plugin — confirmed-safe slice

  Scenario: Local-cache MCP serves governed context offline
    Given the brightagent-context MCP server running in --mode local against a populated cache
    When Codex calls get_workspace_context with no cloud connectivity
    Then the response is served from the local cache with no outbound Brighthive API call

  Scenario: mssql-local connects without installing anything on the server
    Given a local Docker SQL Server (or the EC2 stand-in) with no agent installed on it
    When mssql-local-mcp opens a TDS connection and calls list_tables/list_databases
    Then results return successfully using only a standard client connection

  Scenario: Read-only enforcement holds
    Given mssql-local-mcp configured with --read-default
    When a skill attempts a DDL/DML statement
    Then the call is rejected before reaching the server, mirroring SynapseConnection's existing enforcement

  Scenario: sqlserver-health skill diagnoses a failed job
    Given a SQL Agent job seeded to a Failed state (loopcapital sandbox reset.py --scenario cancelled-run or equivalent)
    When the sqlserver-health skill is invoked
    Then it identifies the failed step and proposes a fix without modifying the job's source

  Scenario: Unsupported capability fails typed, not silent
    Given the confirmed-safe slice deployment (no sync configured)
    When a tool call requires the sync channel
    Then the response is a typed capability-not-available error, not a hang or fabricated result

  @blocked-pending-confirmation
  Scenario: Zero-copy sync pushes only metadata
    Given local-cache mode with sync enabled
    When new metadata, lineage, or quality results are produced locally
    Then only those (never row data) are pushed to Brighthive Cloud

  @blocked-pending-confirmation
  Scenario: Claude Code loads the plugin natively
    Given the portable plugin package (plugin.json, mcp.json, skills/)
    When Claude Code is pointed at the plugin directory
    Then it loads without a client-specific wrapper
```

## 5. Out of Scope

- **Zero-copy sync channel** (context down / metadata up) — needs confirmation (Dependency #8).
  Not implemented in the confirmed-safe slice.
- **Claude Code native wrapper / dual-packaging** — blocked on re-verifying the exclusion claim
  against `agent-plugins.org` directly (Dependency #3). Not implemented in the confirmed-safe
  slice; Codex-only for v1.
- **Write-gated governance in local mode** (`propose_transformation`-equivalent, local dbt PR +
  queued cloud review) — needs confirmation (Dependencies #2, #9). Confirmed-safe slice is
  read-only end to end.
- **`dbt-model-proposal` skill** — blocked on a dbt-sqlserver adapter / `DbtCoreRunner`
  (`on-prem-sql-server-warehouse.md`). Tracked there, not here.
- **Any connection to Loop Capital's real Dev/UAT/Prod SQL Servers** — validated only against a
  local Docker SQL Server or the existing Brighthive-owned EC2 stand-in. No real client data,
  credentials, or server access in this spec.
- **New repo creation for the plugin package** — this spec identifies the need for a decision
  (Dependency #10) but does not create one.

## 6. Dependencies

| Dependency | Type | Status |
|---|---|---|
| #1 Exact `mcp.json` field-level schema (agent-plugins.org) | Blocking (root config can't be finalized without it) | Not started |
| #2 `mssql-local` write posture (read-only vs gated DML/DDL) sign-off | Non-blocking for confirmed-safe slice (ships read-only-only) | Not started |
| #3 Re-verify Claude Code's actual support/exclusion against agent-plugins.org directly | Blocking (for Claude Code wrapper work only, not for Codex slice) | Not started — prior claim unverified |
| #4 Local/edge build of `brightagent-context` MCP (auth mode, cache format) sign-off | Blocking (confirmed-safe slice requires this) | Not started |
| #5 dbt-sqlserver adapter for `dbt-model-proposal` | Blocking (for that skill only) | Not started — tracked in `on-prem-sql-server-warehouse.md` |
| #6 T-SQL dialect coverage in the NL→query generator | Non-blocking for confirmed-safe slice's other skills | Not started — unverified, needs its own check |
| #7 Zero-copy sync mechanism design | Blocking (for sync only) | Not started |
| #8 Offline governance degradation preserves no-self-merge | Blocking (for write-gated governance only) | Not started |
| #9 Physical home for the plugin package (new repo vs subdir of `brightbot`/`agentic-project-mgmt`) | Blocking (implementation can't start without a location) | Not started |
| `on-prem-sql-server-warehouse.md` (`SqlServerConnection`, `WarehousePort` adapter) | Blocking (this spec's connection layer depends on it) | Draft |

## 7. Correctness Properties

### Property 1: Zero-copy holds under sync

*For any* sync event emitted while local-cache mode is active, the payload SHALL contain only
metadata/lineage/quality fields — never a row value from the target SQL Server.

**Validates: §3 Invariant "WHILE running in local-cache mode...", §4 Scenario "Zero-copy sync
pushes only metadata"**

### Property 2: No agent footprint on target server

*For any* `mssql-local-mcp` deployment, the target SQL Server SHALL have no additional installed
service, extended stored procedure, or agent beyond what SSMS itself requires to connect.

**Validates: §3 Invariant "mssql-local-mcp SHALL NOT require any agent...", §4 Scenario
"mssql-local connects without installing anything on the server"**

## 8. Eval Criteria

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| CapabilityRoutingEvaluator | local-plugin skill/tool dispatch | GATE | 100% of cloud-only-capability calls return typed not-available, 0% silent no-op | Deterministic |
| SqlServerHealthDiagnosisEvaluator | `sqlserver-health` skill | OBSERVE | score >= 0.8 on "correctly identifies failed step" against sandbox fixtures | LLM judge |

## 9. Observability Contract

- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=mssql_local_query`, attribute
  `plugin.mode=local-cache`
- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=sqlserver_health_diagnose`
- **Attributes**: `workspace.id` (if bound), `plugin.mode`, `runner.capability_available`
  (bool), `sync.enabled` (bool)
- **Log events**: `local_plugin.capability_unavailable`, `sqlserver_health.job_failure_diagnosed`,
  `mssql_local.readonly_violation_blocked`
- **Metrics**: none

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brightbot` | `brightbot/tests/` + `brightbot/brightbot/evals/` | L0: one case asserting `plugin.json`/`mcp.json` round-trip against the fetched agent-plugins.org schema. L1: one case per §4 non-blocked scenario for skill/tool routing (local-cache served from cache, capability-not-available typed response). L2: real-behavior test — `mssql-local-mcp` against a real local Docker SQL Server (or the EC2 stand-in), asserting read-only enforcement and a real `sqlserver-health` diagnosis against a seeded failed-job fixture. |
| `brighthive-e2e` | `brighthive-e2e/e2e/` | One feature test: Codex-style MCP client loads the plugin package, calls `get_workspace_context` in local-cache mode with cloud connectivity disabled, then calls `mssql-local` against the real sandbox SQL Server end-to-end. |

**Real-behavior requirement**: the L2 case must hit a real SQL Server (local Docker or EC2
stand-in) and real skill execution — construct-only tests asserting `plugin.json` shape alone
don't satisfy this row.

Before opening the implementation PR: run `brightbot`'s full suite + evals and the new
`brighthive-e2e` feature test, confirm each new §2/§3/§4/§8 entry (for the confirmed-safe slice
only) has a corresponding new test case, and confirm all suites are green.

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| MCP server local-cache mode | `brightbot` | New auth mode, new resource-serving path from `context-cache/` files, alongside existing Cognito-gated cloud mode |
| `mssql-local` MCP server | `brightbot` | New MCP server wired to the existing `WarehousePort`/`SqlServerConnection` adapter (`on-prem-sql-server-warehouse.md`) |
| New skills | `brightbot` | `sqlserver-health`, `nl-to-tsql-query`, `change-impact` added under the existing `skills/system/` convention |
| Plugin packaging root | TBD — new repo or subdir (Dependency #9) | `plugin.json`, `mcp.json`, Codex wiring |
| Governance / sync | `brighthive-platform-core` | Phase 2, needs confirmation — no change in confirmed-safe slice |
| Validation target | `agentic-project-mgmt` (`clients/trials/loopcapital/sandbox/`, `infra/loopcapital_sqlserver_ec2`) | Validation only, no real client connection |

## Ticket Breakdown

**Confirmed-safe slice (implementable now):**

| Ticket | Summary | Points | Epic |
|---|---|---|---|
| — | Decide + provision physical home for the plugin package (Dependency #9) | 1 | BH-XXX |
| — | Build `brightagent-context` MCP local-cache auth mode + file-backed resource serving | 5 | BH-XXX |
| — | Build `mssql-local` MCP server wired to `WarehousePort`/`SqlServerConnection`, read-only enforced | 5 | BH-XXX |
| — | Author `sqlserver-health` and `change-impact` skills under existing `skills/system/` convention | 3 | BH-XXX |
| — | Root `plugin.json` + `mcp.json` + Codex wiring, validated against agent-plugins.org schema | 2 | BH-XXX |
| — | Real-behavior L2 tests + `brighthive-e2e` feature test against local Docker SQL Server / EC2 stand-in | 3 | BH-XXX |

**Blocked pending confirmation (do not start until the linked Dependency clears):**

| Ticket | Summary | Points | Epic | Blocked on |
|---|---|---|---|---|
| — | Zero-copy sync channel (context down / metadata up) | 8 | BH-XXX | #7 |
| — | Local governance degradation mode (local dbt PR + queued cloud review) | 5 | BH-XXX | #8 |
| — | Claude Code native wrapper (or: confirm none needed) | 3 | BH-XXX | #3 |
| — | `nl-to-tsql-query` skill (T-SQL dialect coverage check first) | 2 | BH-XXX | #6 |
| — | `dbt-model-proposal` skill | 3 | BH-XXX | #5 (tracked in `on-prem-sql-server-warehouse.md`) |

## Related

- **Dependency spec**: `docs/specs/on-prem-sql-server-warehouse.md` (`WarehousePort`/`SqlServerConnection`, `DbtCoreRunner`)
- **Existing skills convention**: `brightbot/brightbot/skills/system/*/SKILL.md`
- **Trial docs**: `docs/specs/loopcapital-trial-readiness.md`, `clients/trials/loopcapital/TRIAL_STATEMENT.md`
- **Standard**: `https://agent-plugins.org` (verified 2026-08-12 — manifest + component-type claims confirmed; client-support-matrix claims NOT corroborated)
