---
title: "Detach BrightAgent from LangGraph Cloud / LangSmith — two-track execution"
epic: "BH-453"
author: "Kuri Chinca"
status: "Draft"
created: "2026-07-09"
generates: "tickets"
tags: ["langgraph-cloud", "langsmith", "cemaf", "agentcore", "migration", "detach"]
related:
  features: []
  pocs: []
  bedrock: ["docs/bedrock/"]
---

# Detach BrightAgent from LangGraph Cloud / LangSmith — two-track execution

> This spec **updates and reconciles** [`agentcore-deployment-migration.md`](agentcore-deployment-migration.md) (BH-453, v3, 2026-05-27) rather than replacing it. That spec's AgentCore architecture (supervisor stays LangGraph, leaf sub-agents become AgentCore runtimes) is still correct and still in flight (4 runtimes live in staging). What changed since v3: (1) a second, faster track was opened — a brightbot-local wrapper replacement that removes the LangGraph Cloud SaaS dependency without waiting on AgentCore's supervisor-hosting/checkpointer work; (2) the CEMAF rewrite (`brightagent-v3`), previously parked for 2026, was un-parked and is now the chosen path for the *supervisor's* eventual replacement, not raw AgentCore alone. Both tracks reuse the same 4 deployed AgentCore leaf runtimes as compute — they are not competing architectures, they operate at different layers and different timelines.

## Context

LangGraph Cloud / LangSmith's hosted SaaS is being cut off. `agentcore-deployment-migration.md` v3 already tracks the target end-state (AgentCore leaf runtimes + a to-be-decided supervisor host, BH-454, still open) but that path's two hardest pieces — the supervisor's own host and the DynamoDB checkpointer (BH-456) — had zero code as of this spec's writing, and no timeline that fits an urgent SaaS shutoff. Two tracks were opened in parallel to close that gap without regressing production behavior:

- **Track A (fast path, `brightbot`)**: replace the ~10 `langgraph_sdk.get_client()` call sites with a DynamoDB-backed `ThreadStore`/`AssistantStore` and an in-process SSE endpoint, leaving `BBState`, the deepagents middleware stack, and the LangGraph supervisor completely untouched. This removes the SaaS dependency without redesigning working production behavior.
- **Track B (CEMAF pivot, `brightagent-v3`)**: un-park the CEMAF rewrite as the actual long-term supervisor replacement. Real progress already exists here that AgentCore-alone doesn't have: a working `DAGExecutor`, an already-built webapp-compatible SSE endpoint, and (as of this session) a wired DynamoDB `SessionStore` and a ported AgentCore-invocation transport client.

### Use Case / Goal

**Success**: LangGraph Cloud / LangSmith's hosted SaaS is decommissioned with zero customer-visible regression in webapp chat, BrightAgent Studio, and scheduled agent runs. Both tracks converge: Track A removes the immediate outage risk; Track B becomes the durable replacement for the supervisor once its remaining gaps (below) close.

**Who benefits**: Same audiences as `agentcore-deployment-migration.md` (Sales/GTM co-sell unlock, AWS partnership) plus immediate risk reduction for whoever owns the LangGraph Cloud contract/shutdown timeline.

## Current Situation

### How It Works Today

**Track A status (`brightbot`, branch `drchinca/BH-477/langgraph-cloud-detach`, PR #803, draft):**
- Confirmed every `get_client()` call site is a metadata-filtered CRUD or state get/patch — no LangGraph Cloud feature beyond basic thread/assistant persistence is used.
- Confirmed `deep_agent_graph.ainvoke()` already runs in-process today (`brightbot/mcp/tools/analyst_ask.py`) and `stream_mode=["custom","values"]` is the proven streaming pattern (`shared_middleware/stream_forwarding.py`).
- Confirmed the webapp's actual SSE contract (`useChatStream.ts`): only `metadata`, `updates` (interrupt only), `error`, `custom*` are read live; final state always comes from a separate `GET /get_state` call on stream close, never from an `end`/`on_chat_model_stream` frame.
- No code has landed on this branch yet beyond the draft PR scaffold — DynamoDB store, SSE endpoint, and route replacements are still to be built (§ Acceptance Criteria).

**Track B status (`brightagent-v3`, branch `drchinca/BH-453/cemaf-pivot-unpark`, PR #126, draft):**
- Un-parked 2026-07-09 (supersedes the 2026-06-17 "parked for 2026" decision).
- `make migration-coverage` on this branch: **38.7% overall** (155 rows: 36 done, 37 partial, 4 stubbed, 63 missing, 15 superseded; completion 45.5%, spec 63.2%, Jira 42.6%, **parity 10.3%** — the binding constraint).
- `SessionStore` contract (`bright_contracts/session_store.py`) already matches its own spec (`SPEC-CONTRACT-session-store.md`) verbatim — a stale note claiming disagreement was corrected this session.
- `DynamoDBSessionStoreAdapter` is already wired via `SESSION_STORE_PROVIDER=dynamodb` config (`bright_runtime/tenant_services.py`) — real, not a stub.
- `ThreadStore` (`consumer_interfaces/http/thread_store.py`) already wraps `SessionStore` generically and backs a real `POST /threads/{id}/runs/stream` implementation that calls the actual `DAGExecutor` via `execute_chat_dag()`.
- New this session: `services/clients/aws.py` gained `invoke_agentcore_runtime_sync`/`ainvoke_agentcore_runtime`/`normalize_agentcore_session_id`, ported from brightbot's `agentcore_client.py` — transport-layer only, runtime-verified, not yet wired to a CEMAF Tool/Agent.
- Per-agent status against brightbot parity: **retrieval and analyst are `done`** (captured fixtures `run1_retrieval.sse`, `run3_analyst.sse`, proven live streaming UX) — no rewrap needed. **Governance is `partial`** with real native work + fixture (`run2_governance.sse`) in progress. **Engineering (dbt) is `missing`** (stubs only) — the only agent where wrapping the deployed AgentCore runtime is the right call, since no CEMAF-native alternative exists.
- New DynamoDB table (`BrightagentSessionsDataStack`, `brighthive-platform-core`, branch `drchinca/BH-453/brightagent-sessions-dynamodb-stack`, PR #1033, draft) synth-verified this session — partition key `session_id`, GSI `tenant_id-updated_at-index`, TTL on `ttl_epoch_seconds` — not deployed yet.

**AgentCore leaf runtimes (unchanged from `agentcore-deployment-migration.md`):** 4 sub-agents (retrieval, analyst, governance, dbt) live in Staging on branch `origin/agentcore-migration` in `brightbot`, unmerged, diverged 209 commits from `develop` since 2026-05-11.

### Hard Limitations

1. **CEMAF's `DAGExecutor` has no interrupt/pause/resume primitive.** The webapp's `streamHITLHandler` sends `command.resume` to `POST /threads/{id}/runs/stream`; today that path hits `_resume_stub()` — a no-op stream. This is the same gap already tracked as `hitl_approval` (`missing`, BH-172, 3D estimate) in `brightagent-v3/docs/MIGRATION_MAP.md`, now cross-referenced.
2. **Track B's test suite is currently uncollectable.** `MemoryScope.BRAND` (referenced in `bright_autonomy/context_health/computers.py`) does not exist in `cemaf` v3.0.1 (only `GLOBAL/TENANT/PROJECT/USER/SESSION/STRATEGY`) — introduced by this session's `cemaf>=3.0.0` dependency bump. Blocks `pytest` collection for the entire repo until fixed.
3. **Track B's `BBState`/middleware parity gap is real and unscoped.** Brightbot's ~40-field `BBState` and its 12-entry middleware stack (feature flags, OTel, streaming, prompt-caching, intent-capture) have no CEMAF equivalent — needs redesign as Goal/Result DTOs + `AgentRoutingTable`, not mechanical port. Parity-fixture coverage (10.3%) is the honest measure of how much of this remains.
4. **Track A does not by itself close the June-1-class business deadline** in `agentcore-deployment-migration.md` (AWS co-sell "Deployed on AWS" badge) — it removes the LangGraph Cloud *SaaS* dependency but keeps the `langgraph`/`deepagents` Python libraries and the existing LangGraph supervisor topology. That AWS-native badge still depends on Track B (or AgentCore's supervisor-hosting work, BH-454) landing.
5. **`brighthive-platform-core`'s scheduled-agent dispatcher Lambda** (`lambdas/scheduled_agent_dispatcher/actions/langgraph_action.py`) creates a real LangGraph thread + relies on a completion webhook for `quality_check_task`/`profiler_task` dispatch — this is a *third*, separate LangGraph Cloud dependency, in a third repo, not covered by either track in this spec.

### Gaps

- Track A: DynamoDB `ThreadStore`/`AssistantStore` for brightbot, the new SSE endpoint, the `_resume_stub`-equivalent reconnect path (`joinExistingStream` is real, used webapp code — not deferrable), auth conversion (`auth_handler.py` → `Depends(authenticate_request)`) — none built yet, only researched and planned.
- Track B: HITL/interrupt resume (Hard Limitation 1), test-collection fix (Hard Limitation 2), the BBState/middleware redesign (Hard Limitation 3), and per-agent DAG wiring for the AgentCore-wrapped dbt leaf (transport exists, Tool/Agent adaptation doesn't).
- Both tracks: no end-to-end verification yet against a real staging JWT: this spec's own §10 test-coverage requirement is unmet as of this writing.

## Proposals / Solutions

### Recommended Approach

Run both tracks to completion, in the order that removes risk fastest:

1. **Track A ships first** — it is the smaller, lower-risk change (no business-logic rewrite) and removes the actual SaaS-shutdown exposure. Cut brightbot's webapp-facing routes over to the new DynamoDB store + SSE endpoint; decommission is per-graph, not big-bang (`http/app.py` can serve both old and new endpoints during transition).
2. **Track B continues at a sustainable pace**, not compressed to Track A's deadline. Its own migration-coverage gate (`make migration-coverage-gate GATE=100`) is the mechanical readiness signal — do not cut over based on "mostly done."
3. **AgentCore leaf runtimes serve both tracks** as shared infrastructure: Track A doesn't touch them (brightbot's existing supervisor already has the wiring, unmerged on `origin/agentcore-migration`); Track B adopts the same transport client for the one agent (dbt) that needs it.
4. Fold this spec's tickets under the existing **BH-453** epic rather than opening a new one — the parent epic name ("BrightAgent Runtime Migration to Amazon Bedrock AgentCore — remove LangGraph Cloud / LangSmith service dependency") already covers the goal; only the *path* has widened to two tracks.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|---|---|---|---|
| AgentCore-only (as v3 of `agentcore-deployment-migration.md` originally scoped) | Single target architecture, AWS-native end to end | Supervisor host (BH-454) and checkpointer (BH-456) were both zero-code with no near-term timeline; doesn't solve an urgent shutoff | Too slow for the forcing deadline |
| CEMAF-only, skip Track A | Converges directly on the real long-term target | `BBState`/middleware redesign (Hard Limitation 3) is unscoped and risks behavior drift under time pressure | Too risky to rush |
| Self-host OSS `langgraph-api` (considered and dropped this session) | Zero webapp changes, identical wire protocol | No self-hosting infra exists anywhere in the org; still leaves the org on `langgraph`/`deepagents` as the permanent architecture, not aligned with the AWS-native goal | Solves the SaaS problem but not the strategic one |
| **Track A + Track B in parallel** ✅ | De-risks the urgent deadline immediately (Track A) without forcing the long-term rewrite (Track B) to rush | Two active branches/PRs to keep in sync; some duplicate DynamoDB table design work (brightbot's ThreadStore vs. brightagent-v3's SessionStore are separate tables) | Best trade-off; duplication is small and each table serves a different service |

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| BrightBot (Track A) | `brightbot` | New `ThreadStore`/`AssistantStore` (DynamoDB), new in-process SSE streaming endpoint, `get_client()` call-site replacement across `http/app.py`/`brightagent_studio_routes.py`/`agent_run_routes.py`/`file_routes.py`/`token_validator.py`, auth conversion (`auth_handler.py` → `authenticate_request`) |
| BrightAgent v2 / CEMAF (Track B) | `brightagent-v3` | Fix `MemoryScope.BRAND` collection break, implement HITL/interrupt resume in `DAGExecutor`, wire the ported AgentCore transport into a CEMAF Tool/Agent for `dbt`, continue BBState/middleware parity work per `MIGRATION_MAP.md` |
| Platform Core (infra) | `brighthive-platform-core` | New `BrightagentSessionsDataStack` (Track B's session table, drafted this session) + a separate new stack for Track A's brightbot thread/assistant tables (not yet built); scheduled-agent dispatcher's own LangGraph dependency (Hard Limitation 5) is a follow-up, not in this spec's scope |
| Web App | `brighthive-webapp` | No code changes expected for Track A if the SSE contract is matched exactly (confirmed field-for-field this session); Track B's webapp-facing behavior is already designed to match the same contract |
| CI/CD, canary, MCP Fargate, egress audit, cost, DR | `brighthive-platform-core`, `brightbot`, `brightbot-slack-server` | Unchanged from `agentcore-deployment-migration.md` — those tickets (BH-459–BH-476) proceed independently of this spec |

## Acceptance Criteria

- [ ] **AC-1 (Track A)** All `langgraph_sdk.get_client()` call sites in `brightbot` are replaced with `ThreadStore`/`AssistantStore` calls or direct `.ainvoke()` (for fire-and-forget graphs); zero remaining imports of `langgraph_sdk` outside of `langgraph.json`'s own deploy config.
- [ ] **AC-2 (Track A)** New SSE endpoint emits exactly the event set the webapp actually consumes (`metadata`, `updates` with `__interrupt__`, `error`, `custom*`) and supports reconnect (`GET /runs/{run_id}/stream` with `Last-Event-ID`) — verified against `useChatStream.ts` directly, not assumed.
- [ ] **AC-3 (Track A)** Thread state (messages, outputs, artifacts, thread_title, stream_workflows) survives a brightbot process restart when backed by the new DynamoDB store — this is the literal LangGraph Cloud dependency being replaced.
- [ ] **AC-4 (Track B)** `pytest` collection succeeds repo-wide (Hard Limitation 2 resolved) before any further Track B verification is trusted.
- [ ] **AC-5 (Track B)** `POST /threads/{id}/runs/stream`'s `command.resume` path actually resumes DAG execution (Hard Limitation 1 resolved) — no more `_resume_stub` no-op.
- [ ] **AC-6 (Track B)** The `dbt` CEMAF DAG node invokes the deployed AgentCore `dbt` runtime via the ported transport client and round-trips a real chat turn in staging.
- [ ] **AC-7 (both tracks)** End-to-end verification against a real staging JWT (not mocked): webapp chat send/receive, thread history reload, BrightAgent Studio CRUD, ad-hoc agent runs — for whichever track is being cut over.
- [ ] **AC-8** LangGraph Cloud's three hosted deployments (`brightbot-develop`, `brightagent-staging`, `brightagent-prod`) are decommissioned only after AC-1 through AC-3 (Track A) are verified in production — do not decommission speculatively.

## Out of Scope

- The scheduled-agent dispatcher Lambda's own LangGraph Cloud dependency (`brighthive-platform-core/lambdas/scheduled_agent_dispatcher/actions/langgraph_action.py`) — tracked separately, not blocking either track here.
- Full BBState/middleware parity completion for Track B — that's the multi-week continuation tracked in `brightagent-v3/docs/MIGRATION_MAP.md`/`MIGRATION_STATE.md`, not a deliverable of this spec.
- AgentCore's own AC-1 through AC-14 (canary routing, MCP Fargate, cost/DR, CI/CD tag-driven deploys) — those remain exactly as scoped in `agentcore-deployment-migration.md` and are unaffected by this spec.
- Merging `origin/agentcore-migration` into `brightbot/develop` — tracked separately given the 209-commit divergence; not a dependency of either track's near-term acceptance criteria.

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| `agentcore-deployment-migration.md` (BH-453 v3) | Non-blocking | Live, this spec updates rather than replaces it |
| 4 AgentCore leaf runtimes in Staging (`origin/agentcore-migration`) | Non-blocking | Live, reused by both tracks |
| `BrightagentSessionsDataStack` CDK stack (Track B's DynamoDB table) | Blocking (Track B AC-3 equivalent) | Drafted, synth-verified, not deployed |
| New brightbot thread/assistant DynamoDB table (Track A) | Blocking (AC-1, AC-3) | Not yet designed/built |
| `MemoryScope.BRAND` fix | Blocking (AC-4) | Not started |
| HITL/interrupt resume in CEMAF `DAGExecutor` | Blocking (AC-5) | Not started, BH-172 |

## Ticket Breakdown

Parent epic: **BH-453** (existing, live). New tickets fold in alongside BH-454–476.

| Ticket | Summary | Points | Epic |
|---|---|---|---|
| — | Track A: build brightbot `ThreadStore`/`AssistantStore` (DynamoDB) | 5 | BH-453 |
| — | Track A: new CDK stack for brightbot thread/assistant table | 3 | BH-453 |
| — | Track A: build in-process SSE streaming endpoint matching webapp contract | 5 | BH-453 |
| — | Track A: replace `get_client()` call sites across 5 files | 5 | BH-453 |
| — | Track A: implement reconnect stream (`Last-Event-ID` replay) | 3 | BH-453 |
| — | Track A: convert `auth_handler.py` to `Depends(authenticate_request)` | 2 | BH-453 |
| — | Track A: end-to-end verify + cutover + decommission | 3 | BH-453 |
| — | Track B: fix `MemoryScope.BRAND` test-collection break | 2 | BH-453 |
| — | Track B: implement HITL/interrupt resume in `DAGExecutor` | 8 | BH-172 |
| — | Track B: wire AgentCore transport into a CEMAF `dbt` Tool/Agent | 5 | BH-453 |

## Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brightbot` | `brightbot/tests/` (unit/integration) + `brightbot/brightbot/evals/` (L0/L1/L2 per `brightbot/CLAUDE.md`) | L0: one case per new `ThreadStore`/`AssistantStore` method signature (AC-1). L1: one case routing a `POST /threads/{id}/runs/stream` request to the new in-process handler instead of `langgraph_sdk` (AC-2). L2: one case proving thread state survives a process restart (AC-3) — real DynamoDB (or local-stack equivalent), not mocked. |
| `brightagent-v3` | `tests/unit/`, `tests/parity/fixtures/`, `make migration-coverage` | One contract test proving `pytest` collection succeeds repo-wide (AC-4). One test exercising `command.resume` end-to-end through a real DAG run (AC-5) — captures a new parity fixture per this repo's own convention. One test invoking the real deployed `dbt` AgentCore runtime via the ported transport client (AC-6) — real staging ARN, not a mock. |
| `brighthive-e2e` | `brighthive-e2e/e2e/` (cross-repo) | One feature test per track exercising webapp chat send/receive against a real staging JWT (AC-7), for whichever track is closer to cutover at implementation time. |

**Real-behavior requirement**: AC-3, AC-5, and AC-6 above each require at least one test hitting a real backend (DynamoDB, the real `DAGExecutor`, the real deployed AgentCore ARN) or a captured replay — construct/mock-only tests do not satisfy this spec's §10.

## Related

- **Supersedes/updates in part**: [`agentcore-deployment-migration.md`](agentcore-deployment-migration.md) (BH-453 v3) — this spec does not invalidate it; §"How It Works Today" above documents exactly which of its open questions (BH-454 supervisor host) this spec's Track B answers.
- **brightagent-v3 tracking docs**: `docs/MIGRATION_STATE.md`, `docs/MIGRATION_MAP.md`, `docs/AGENT_MIGRATION_STATE.md` — row-level ground truth for Track B, updated this session.
- **Plan file (this session)**: `/Users/bado/.claude/plans/yes-we-need-to-dazzling-bonbon.md`
- **Branches/PRs**: `brightbot` `drchinca/BH-477/langgraph-cloud-detach` (PR #803, draft); `brightagent-v3` `drchinca/BH-453/cemaf-pivot-unpark` (PR #126, draft); `brighthive-platform-core` `drchinca/BH-453/brightagent-sessions-dynamodb-stack` (PR #1033, draft)
