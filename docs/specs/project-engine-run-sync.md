---
title: "Sync a project with its transformation engine's existing jobs, runs, and logs — through the PipelineRunner port"
epic: "BH-1255"
ticket: "BH-1330"
author: "Kuri"
status: "Draft"
created: "2026-08-01"
generates: "tickets"
tags: [pipeline, sync, observability, data-products, engine-agnostic, dbt, snowflake, loopcapital]
related:
  features: []
  pocs: []
  bedrock: []
  specs: ["pipeline-run-lifecycle.md", "remediation-pr-engine-run-logs.md", "self-healing-pipelines.md"]
---

# Sync a project with its transformation engine's existing jobs, runs, and logs

> A project linked to a transformation engine shows "0 runs / Last run Never / no data
> products" even when the engine already has jobs, run history, and logs — because nothing
> pulls that history into the project. This spec adds ONE capability: an engine-agnostic
> **Sync** that enumerates the connected engine's jobs, pulls their runs + logs through the
> `PipelineRunner` port (`pipeline-run-lifecycle.md`, BH-1255), persists them to the project's
> run store, and registers data products from each synced run. Every claim in §1 is anchored
> to traced `file:line` so no ticket re-derives the gap.

## 1. Context

Observability for a project can only ever show runs **Brighthive itself triggered**. There is
no path that pulls a connected engine's *existing* jobs/runs/logs into the project. Traced
live, read-only, across three repos:

- **webapp** — no sync/import action anywhere. The Observability tab's only control is a
  client-side Apollo `refetch()` of the same query
  (`brighthive-webapp/src/Projects/ProjectObservabilityPage/index.tsx:162`). Engine job
  enumeration (`GetDbtJobs`) is used only in the create-transformation job picker
  (`src/Sheets/Transformation/CreateTransformation.tsx:52`), never a project backfill. The
  Flow-tab "Run" button works but on a fresh project silently no-ops and shows a false "Data
  flow has been triggered." toast (`src/ProjectWorkflow/ProjectWorkflowPage.tsx:430`).
- **platform-core** — run data is either a live *single-latest-run* lookup per already-bound
  `jobId` (`src/graphql/models/transformation.ts:155-259`) or an internal Neo4j
  `WorkflowRunNode` store filled **only** on Brighthive-triggered executions
  (`src/graphql/models/workflow-spec.ts:816-828`; `service/workflow/poller.ts:60-77` only
  advances already-`RUNNING` rows). Engine-enumeration methods (`getAllJobs`, `getJobs`,
  `getRun`, `dbt-api.ts:305,350,602`) feed only the job picker + a connection test — never a
  backfill.
- **platform-core** — data-product registration (`registerDbtOutputDataAssets`,
  `src/graphql/models/project.ts:335`) has exactly ONE caller: the `getTransformationRunStatus`
  poll query (`project.ts:2798`), and only fires when a run's `job_definition_id` string-equals
  a project `TransformationNode.jobId` (`project.ts:2896`). A freshly-linked project has no such
  binding → 0 products, silently, no error.
- **brightbot** — the port verbs that could enumerate history — `list_pipelines`,
  `get_run_detail`, `get_run_logs` (`brightbot/pipelines/runner_port.py:223,251,265`) — are
  reachable ONLY from chat tools (`agents/dbt_agent/tools/pipeline_lifecycle_tools.py`) and MCP
  (`mcp/tools/pipeline_lifecycle.py`). Platform-core never calls them.

**Verdict: the sync capability is entirely absent (not broken).** All building blocks exist —
`list_pipelines`/`get_run_detail`/`get_run_logs` on the port, `registerDbtOutputDataAssets` in
core — nothing wires them into a project-level sync.

### Use Case / Goal

A Loop Capital operator links a project to their dbt Cloud engine (which already runs nightly
jobs), clicks **Sync**, and the project's Observability tab fills with the engine's real runs
(models, run count, success rate, last run) and the Data Products / Data Asset views populate
from those runs' produced outputs. The same Sync works for a Snowflake-native engine
because the logic depends only on the `PipelineRunner` port. Success = a freshly-linked project
reflects its engine's real history without Brighthive having triggered a single run.

```mermaid
sequenceDiagram
    participant U as Operator
    participant C as Platform-core (SyncProject resolver)
    participant P as PipelineRunner (port)
    participant E as Engine (dbt Cloud / Snowflake-native)
    participant S as Project run store + DataAssets (Neo4j)
    U->>C: syncProjectRuns(projectId)
    C->>P: list_pipelines(owned)         %% enumerate the engine's jobs
    P->>E: list jobs
    E-->>C: jobs
    loop per job, recent runs
        C->>P: get_run_detail(run_id)
        C->>P: get_run_logs(run_id)
        P->>E: fetch detail + logs
        E-->>C: RunDetail + RunLogs
        C->>S: upsert run (idempotent)
        C->>P: get_run_outputs(run_id)      %% RUN_OUTPUTS-gated; () if unsupported
        C->>S: register data products from the run's produced outputs
    end
    C-->>U: synced N runs, M data products (or stated reason for 0)
```

## 2. Interface Contract (MDE)

**Port first (the design), then platform-core's sync surface — per docs/CLAUDE.md.** Most of the
sync is a *composition* of existing observe verbs (BH-1255). It adds **two capability-negotiated
port verbs** — one to discover historical run ids, one to read what a run produced — because
neither is derivable from the existing verbs without parsing engine-shaped logs, which would put a
vendor-shaped concern in the engine-agnostic path (INV-1). Both are guarded by a capability flag so
an engine that lacks them degrades, never errors.

### 2.1 Port — reused verbs, plus two capability-negotiated additions

```python
# brightbot/pipelines/core/port.py — reused verbs (unchanged):
async def list_pipelines(self, *, ctx, owned_only: bool) -> tuple[Pipeline, ...]: ...      # :224
async def get_run_detail(self, *, run_id: str, ctx) -> RunDetail: ...                       # :266
async def get_run_logs(self, *, run_id: str, ctx) -> RunLogs: ...                           # :252

# Additions — two capability flags + two verbs, engine-agnostic domain types only:
class RunnerCapability(Enum):
    ...
    LIST_RUNS = "list_runs"        # engine can enumerate a pipeline's run HISTORY, not just latest
    RUN_OUTPUTS = "run_outputs"    # engine can report the data outputs a run produced

@dataclass(frozen=True, slots=True)
class RunOutput:                   # engine-agnostic — NOT a dbt 'model'; any engine's produced table
    output_id: str                 # engine-stable id for the produced output (dbt unique_id, etc.)
    status: str                    # RunDetail-grain status for this output ('success'/'error'/…)
    relation_name: str | None      # fully-qualified table/view name, when the engine reports one

async def list_runs(               # verb 1 — history, not the single latest run
    self, *, pipeline_id: str, limit: int, ctx: RequestContext
) -> tuple[RunHandle, ...]:
    """Return the most recent `limit` runs for a pipeline (newest first).

    Raises:
        NotImplementedError: LIST_RUNS not in capabilities()
        ValueError: pipeline_id not found
    """
    ...

async def get_run_outputs(         # verb 2 — the data-product candidates a run produced
    self, *, run_id: str, ctx: RequestContext
) -> tuple[RunOutput, ...]:
    """Return the data outputs a run produced (engine-agnostic; empty when none).

    Raises:
        NotImplementedError: RUN_OUTPUTS not in capabilities()
        ValueError: run_id not found
    """
    ...
```

Two genuine gaps the existing verbs can't fill:

- **`list_runs`** — today the port exposes `get_run_detail(run_id)` but no way to *discover*
  historical run ids for a pipeline (platform-core only ever had the single latest run via
  `getLatestRun`). Sync needs the last N runs per job.
- **`get_run_outputs`** — sync must register the data products a run produced (INV-5), but the port
  had no verb that reports them. The only alternative — regex-parsing `get_run_logs` output — would
  bake a vendor's log format into the engine-agnostic sync path, violating INV-1. The adapter reads
  the engine's own run-result record (dbt Cloud: the `run_results.json` artifact via the existing
  `_fetch_artifact` helper) and translates it to `RunOutput`; the sync path only ever sees the
  domain type. Engines that can't report outputs simply omit `RUN_OUTPUTS` and sync registers none.

### 2.2 Sync orchestration (engine-agnostic, brightbot)

```python
# brightbot/pipelines/sync/project_runs.py
@dataclass(frozen=True, slots=True)
class SyncedRun:
    run_id: str
    pipeline_id: str
    status: str                        # RunDetail.status.value
    started_at: str | None
    finished_at: str | None
    duration_s: float | None
    log_excerpt: str                   # bounded, tail-preserving (_MAX_LOG_CHARS_PER_RUN)
    run_outputs: tuple[RunOutput, ...] # data-product candidates from get_run_outputs (INV-5); () when RUN_OUTPUTS absent

@dataclass(frozen=True, slots=True)
class SyncResult:
    runs: tuple[SyncedRun, ...]
    pipelines_seen: int
    degraded: bool = False             # LIST_RUNS absent → latest-only backfill (INV-6)
    reason_if_empty: str | None = None # NEVER silently empty (INV-4)

async def sync_project_runs(
    *, runner: PipelineRunner, runs_per_pipeline: int, ctx: RequestContext
) -> SyncResult:
    """Enumerate the engine's pipelines, pull recent runs + logs + outputs, return a SyncResult.

    Depends only on the port; branches on capabilities(), never adapter identity. Reads
    run outputs only when RUN_OUTPUTS is advertised — otherwise run_outputs is ().
    """
    ...
```

### 2.3 Platform-core sync surface (persist + register)

**Direction (ADR-015): brightbot → platform-core, not the reverse.** brightbot has no
direct-to-Neo4j path, so the graph write goes through this mutation — the SAME grain
`updateWorkflowRunStep` / `updateTransformationRunStatus` already use. brightbot's
`sync_project_runs` (which owns the `PipelineRunner` port + adapters, §2.2) enumerates the
engine, pulls the runs + their produced outputs, and POSTs the assembled `SyncResult` here. Platform-core
persists what it receives; it never re-enumerates the engine (that would hardcode a vendor and
violate INV-1). The mutation is service-key guarded (`x-service-key`), not `@authorized` — an
internal service with no Cognito session calls it.

```graphql
# src/graphql/schema/project-run-sync-typedefs.ts (own file — typedefs.ts is over the size limit)
extend type Mutation {
  syncProjectRuns(input: SyncProjectRunsInput!): SyncProjectRunsResult!
}
# Carries the pulled runs (brightbot → platform-core), not a fetch request.
input SyncProjectRunsInput {
  workspaceId: ID!
  projectId: ID!
  runs: [SyncedRunInput!]!
  pipelinesSeen: Int!
  reasonIfEmpty: String        # set by brightbot when the pull produced 0 runs
}
input SyncedRunInput {
  runId: ID!
  pipelineId: ID!
  status: String!
  startedAt: String
  finishedAt: String
  runOutputs: [SyncedRunOutputInput!]   # data-product candidates for INV-5
}
input SyncedRunOutputInput { outputId: String!, status: String!, relationName: String }
type SyncProjectRunsResult {
  runsSynced: Int!
  dataProductsRegistered: Int!
  pipelinesSeen: Int!
  reasonIfEmpty: String        # passed through when runsSynced == 0
}
```

The resolver **upserts** each received run (updates `lastRunStatus`/`lastRunAt` per matched
`TransformationNode` by `dbtModelName`), and for each synced run with successful model outputs
calls the existing `registerDbtOutputDataAssets` (`project.ts:335`) — bridging the
`jobId`↔`TransformationNode` binding gap so registration is reachable from sync, not only from a
Brighthive-triggered run.

## 3. Invariants (DbC)

Budget: 6.

- **INV-1** — `sync_project_runs` depends ONLY on `PipelineRunner` + domain types. No vendor SDK,
  no `dbt`-named symbol in `pipelines/sync/project_runs.py`. (Grep test PS-3/PS-4.)
- **INV-2** — Idempotent. `IF a run with the same run_id was already synced, THEN re-sync updates
  it in place and creates no duplicate run and no duplicate data product.`
- **INV-3** — Multi-tenant. `WHERE a run belongs to another workspace, THE System SHALL NOT
  surface it in this project's sync.`
- **INV-4** — No silent empty. `IF sync produces 0 runs, THEN reasonIfEmpty states why (engine
  empty / LIST_RUNS unsupported / no pipelines).` A bare empty tab is a contract violation.
- **INV-5** — Registration reachable from sync. `IF a synced run has ≥1 successful produced output,
  THEN registerDbtOutputDataAssets is invoked for it` — not gated behind the
  `job_definition_id == TransformationNode.jobId` match that blocks fresh projects today
  (`project.ts:2896`). Outputs come from `get_run_outputs` (the port verb), never from parsing logs.
- **INV-6** — Capability-negotiated. `WHERE the engine does not advertise LIST_RUNS, THE System
  SHALL degrade (best-effort: latest run only) and state the limit — never error out.` Likewise,
  `WHERE the engine does not advertise RUN_OUTPUTS, THE System SHALL sync runs with no produced
  outputs (run_outputs = ()) and register no data products — never error out.`

## 4. Acceptance Criteria (BDD)

```gherkin
Feature: Sync a project with its transformation engine's existing runs (engine-agnostic)

  Scenario: dbt Cloud engine with existing history backfills the project
    Given a project linked to a dbt Cloud engine that already has jobs and run history
    When the operator triggers Sync
    Then the Observability tab shows those runs (models, run count, success rate, last run)
    And the runs were pulled from the engine, not triggered by Brighthive

  Scenario: synced successful run populates data products
    Given a synced run whose engine reports ≥1 successful produced output via get_run_outputs
    When sync registers data products for it
    Then the Data Products tab and Data Asset view are populated for that project

  Scenario: engine cannot report produced outputs — runs still sync, no data products
    Given the project's engine does not advertise RUN_OUTPUTS
    When Sync runs
    Then the runs sync with empty run_outputs and no data products are registered
    And no error is raised

  Scenario: engine-agnostic — a non-dbt engine syncs through the same port
    Given the project's engine is snowflake-native
    When Sync runs against its adapter
    Then the project shows that engine's runs via the same port verbs
    And no dbt-specific code executed on the sync path

  Scenario: sync is idempotent
    Given a project already synced once
    When Sync runs a second time
    Then no duplicate runs and no duplicate data products are created

  Scenario: engine cannot enumerate run history — degrade, don't error
    Given an engine that does not advertise LIST_RUNS
    When Sync runs
    Then the project shows the latest run per pipeline (best-effort)
    And the result states that full history could not be pulled

  Scenario: nothing to sync — say why
    Given a linked engine with zero jobs
    When Sync runs
    Then runsSynced is 0
    And reasonIfEmpty states the engine has no pipelines
```

## 5. Out of Scope

- **Triggering new runs** — the Flow-tab `runTransformationsInProject` already does this
  (`project.ts:2701`). The false "triggered" toast on a project with no `jobId`-bound
  transformations (`ProjectWorkflowPage.tsx:430`) is a separate precondition bug — filed as a
  follow-up, not fixed here.
- **Real-time streaming of in-flight runs** — sync is pull-on-demand (+ optionally scheduled);
  live status stays the existing poller's job (`poller.ts`).
- **before+after remediation-PR logs** — BH-1329, separate spec.
- **New engine adapters** — BH-1330 ships dbt Cloud + Snowflake-native (live on staging). The
  rest of the §6 matrix (Databricks, dbt Core, SSIS/SSRS, Redshift-target semantic `.yml`s) are
  registry entries added per client engine — each is its own ticket, none touch the sync path.

## 6. Dependencies

- `PipelineRunner` port + `list_pipelines`/`get_run_detail`/`get_run_logs` (BH-1255) — reused;
  this spec adds two capability-negotiated verbs: `list_runs` (+ `LIST_RUNS`) and
  `get_run_outputs` (+ `RUN_OUTPUTS`) with the `RunOutput` domain type.
- `registerDbtOutputDataAssets` (`project.ts:335`) — reused, made reachable from sync (INV-5).
- dbt Cloud `run_results.json` artifact via the existing `_fetch_artifact` helper
  (`dbt_agent/tools/dbt_cloud_tools.py`) — the adapter's source for `get_run_outputs`; already used
  by the remediation path, so no new dbt surface.

### Engine / warehouse / source matrix the port must cover

Sync is designed against the whole known Brighthive matrix — the reason it is a port composition,
not a dbt function. Each engine is one adapter behind the registry (PS-3); adding one is a
registry entry, never a change to `pipelines/sync/project_runs.py` (INV-1). Sync's `list_runs`/`get_run_detail`/
`get_run_logs` map onto each engine's native run/job history; where an engine has no enumerable
run history, its adapter advertises `LIST_RUNS` absent and sync degrades (INV-6).

| Engine (pipelines) | Run history via | Warehouse it writes to | Source feeding it |
|---|---|---|---|
| dbt Cloud | dbt Cloud runs API | Snowflake · Redshift · Databricks | Airbyte / BYOW upload |
| dbt Core (self-hosted) | run artifacts (`run_results.json`) | same | same |
| Snowflake-native pipes | Snowflake task/pipe history | Snowflake | Airbyte / BYOW Snowflake upload |
| Databricks | Databricks Jobs run history | Databricks | Airbyte |
| SSIS / SSRS (MSSQL, XSD/Azure) | SQL Agent / execution log | Azure SQL / MSSQL | on-prem / Azure |

Redshift is also a warehouse target of user-requested transformations expressed as semantic
`.yml`s — those transformations run *through* one of the engines above, so they surface through
the same sync path, not a separate one. First adapters implemented under BH-1330: dbt Cloud +
Snowflake-native (the two engines live on staging today). The rest are registry entries added as
each client engine comes online — no sync-path code change.

## 7. Correctness Properties

Multi-tenant isolation boundary + a no-silent-failure guarantee, so this section applies.

### Property 1: tenant isolation
*For any* run surfaced by sync, its workspace equals the requesting project's workspace.
**Validates: §3 INV-3, §4 (all — scoped to the project's workspace)**

### Property 2: idempotence
*For any* run synced twice, the store contains exactly one run node and one set of data products
for it.
**Validates: §3 INV-2, §4 Scenario "sync is idempotent"**

### Property 3: no silent empty
*For any* sync producing 0 runs, `reasonIfEmpty` is non-null.
**Validates: §3 INV-4, INV-6, §4 Scenarios "cannot enumerate", "nothing to sync"**

## 8. Eval Criteria

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| SyncBackfillEvaluator | sync_project_runs | GATE | synced run count == engine run count (capped) == 1.0 | deterministic |
| SyncEmptyReasonEvaluator | syncProjectRuns | GATE | reasonIfEmpty set whenever runsSynced==0 == 1.0 | deterministic |

Deterministic — no LLM judge (mirrors BH-1329 / BH-1092 evaluator design).

## 9. Observability Contract

- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=sync_project_runs` (reuses the BH-1324
  `pipeline_verb_telemetry` seam).
- **Attributes**: `workspace.id`, `project.id`, `brightagent.pipeline.engine`,
  `pipeline.count`, `pipeline.runs_synced`, `pipeline.products_registered`, `correlation_id`.
- **Log events**: `sync.started`, `sync.pipelines_enumerated`, `sync.run_upserted`,
  `sync.outputs_read` (with count), `sync.products_registered`, `sync.empty` (with reason),
  `sync.capability_degraded` (which capability: `LIST_RUNS` / `RUN_OUTPUTS`).
- **Metrics**: reuse `brightagent.pipeline.verb.executions` / `.duration_ms` with `verb=sync`.

## 10. Test Coverage Update

### a. In-repo layered evals

**brightbot (`tests/`):**
- **L0** — `list_runs` + `LIST_RUNS` and `get_run_outputs` + `RUN_OUTPUTS` + `RunOutput` present on
  `PipelineRunner` + `FakePipelineRunner`; `SyncedRun` carries `run_outputs`; `SyncResult` shape
  (reason_if_empty present when empty).
- **L1** — sync composes list_pipelines → list_runs → get_run_detail/get_run_logs/get_run_outputs
  in order; degrades to latest-only when `LIST_RUNS` absent; skips output reads (run_outputs = ())
  when `RUN_OUTPUTS` absent.
- **L2 (real FakePipelineRunner, no patch())** — one case per §4 scenario using `FakePipelineRunner`
  seeded with a run history + produced outputs + `InjectedFault` for the empty / no-LIST_RUNS /
  no-RUN_OUTPUTS paths. Assert on the `SyncResult` (including `run_outputs`) + §9 spans/events.

**platform-core (`tests/`):**
- **L0** — `syncProjectRuns` mutation shape per §2.3.
- **L2** — resolver upserts runs idempotently (INV-2) and reaches `registerDbtOutputDataAssets`
  for a synced successful run (INV-5), scoped to the project's workspace (INV-3). Against a real
  Neo4j test instance where the suite provides one.

### b. Cross-repo e2e (`brighthive-e2e/`)

- One feature test: link a project to a dbt Cloud sandbox that has run history, call
  `syncProjectRuns`, assert Observability shows the runs and Data Products populate.
- Idempotence: run sync twice, assert no duplicates.
- Error-path: engine with zero jobs → `runsSynced: 0` + non-null `reasonIfEmpty`.

### Self-verification

All suites green with new cases before the implementation PR opens; each §2/§3/§4/§8 entry has a
matching new test.

## Ticket Breakdown

| Ticket | Repo | Gate |
|---|---|---|
| `list_runs` verb + `LIST_RUNS` capability on port + FakePipelineRunner | brightbot | L0 + contract |
| dbt Cloud adapter: `list_runs` (map dbt Cloud run history) | brightbot | adapter test + live |
| Snowflake-native adapter: `list_runs` (or advertise unsupported) | brightbot | adapter test |
| `pipelines/sync/project_runs.py` — enumerate + pull + assemble SyncResult (engine-agnostic) | brightbot | L2 real-behavior |
| `syncProjectRuns` mutation + resolver: upsert runs + reach registration | platform-core | L2 (idempotent, INV-5) |
| Webapp "Sync" action on Observability tab + refresh | brighthive-webapp | component + e2e |
| e2e: link → sync → runs + data products populate | brighthive-e2e | full Gherkin |
| (follow-up) Flow-tab false "triggered" toast when no jobId-bound transformations | brighthive-webapp | bug |

## Related

- `pipeline-run-lifecycle.md` — owns the `PipelineRunner` port (BH-1255) this extends with `list_runs`.
- `remediation-pr-engine-run-logs.md` — BH-1329; shares the bounded tail-preserving log-excerpt
  convention + the port-first pattern.
- `self-healing-pipelines.md` — BH-526; consumes the same run/observability substrate.
