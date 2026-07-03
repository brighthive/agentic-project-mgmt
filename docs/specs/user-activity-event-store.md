---
title: "Canonical UserActivityEvent Store"
epic: "BH-942"
author: "drchinca"
status: "Draft"
created: "2026-07-03"
generates: "epic"
tags: ["foundational", "storage", "brightroutines", "observability"]
related:
  features: ["BH-876 BrightRoutines intent-loop", "BH-885 Suggested Routines webapp", "BH-926 Prompt Catalog (proposed)"]
  pocs: []
  bedrock: []
---

# Canonical UserActivityEvent Store

> Draft spec — architectural review required with Marwan + Sherbiny + Nano
> before an implementation ticket is created. This document produces the
> artifact that review needs and no more.

## 1. Context

BrightHive today has NO canonical cross-workspace, cross-thread,
user-usage-over-time store. What exists is fragmented and asset-shaped
rather than user-shaped:

| Signal | Where it lands | User-queryable over time? |
|---|---|---|
| Chat turns | LangGraph checkpoint (per deployment) | Per-thread only |
| Tool mutations | CloudWatch JSON (`brightbot.audit`) | Only via Logs Insights ad-hoc |
| Semantic facts | Mem0 | Facts, not events |
| Quality-check runs | Neo4j `QualityRuleExecutionNode` | Per data-asset |
| Metric history | Neo4j `MetricSnapshotNode` | Per data-asset |
| Notifications | Neo4j BrightSignals | Per-user read-state, not activity |
| LLM cost/tokens | DynamoDB `LangsmithTokenUsage` | "Never exported or aggregated" (usage-metering-pipeline.md) |
| **Repeated schedulable intent** | **NEW** DynamoDB `brightroutines-{env}` (BH-882) | First user-shaped store — this ticket generalizes it |

`ProactiveSignal` (`brightbot/routines/dtos.py`, BH-883) is effectively
the platform's first user-shaped longitudinal record — it carries
`workspace_id`/`user_id`/`thread_id`/`turn_id`/`observed_at`/`outcome_ok`
+ a normalized `AutomationIntent`. Every future feature that needs a
per-user activity history (analytics dashboards, cost attribution, HITL
replay, saved-thread promotion, Kuri's prompt-catalog proposal) will
either duplicate this shape into its own silo, or share this rail.

### Use Case / Goal

One canonical per-user event log every feature reads from and writes to.
Consumers today:

1. **BrightRoutines detector** (BH-876) — reads schedulable signals in
   28-day windows, groups by intent fingerprint.
2. **W/P/U scoring** (BH-950) — aggregates over the same signals with
   scope + activation counts.
3. **Prompt catalog / value-shaped detection** (proposed, follows from
   Kuri's "1-shot 95%-value prompts" question) — reads every meaningful
   turn, not just schedulable-classified ones; scores by value not just
   repetition.
4. **Platform analytics + cost attribution** (per `usage-metering-pipeline.md`
   and `platform-analytics-dashboard.md` — both explicitly named as
   unbuilt today).

### How It Works Today

`brightroutines-{env}` DynamoDB table under `PK=WORKSPACE#<id>` with
`SK=SIGNAL#…` for `ProactiveSignal` rows, GSI2 for by-user reads, 35-day
TTL. Written by (not yet built) capture middleware in BH-883 part 2;
read by (BH-884) detector and (BH-950) scoring aggregator. Non-schedulable
turns are captured but not GSI-indexed for retrieval.

### Hard Limitations

- **Silo shape**: `brightroutines-{env}` is named for one consumer.
  Adding cost attribution or a prompt catalog means either a new table
  (fragmentation) or hijacking a domain-named store.
- **35-day TTL** on `ProactiveSignal` truncates the tail — one-shot but
  valuable prompts that resurface in month 3 are already gone.
- **`intent.schedulable=true` filter at capture** trims non-schedulable
  turns to a non-indexed path — retroactively rescoring a "1-shot 95%"
  prompt (Kuri's ask) requires re-scanning cold storage.
- **No cross-workspace read pattern** for platform-level analytics.

### Gaps

- No canonical "give me user X's activity in the last 90 days" query.
- No canonical "give me the top-K prompts by value in workspace W"
  query.
- No shared retention/redaction contract — each silo would re-derive.

---

## 2. Interface Contract (MDE)

### 2.1 Core DTO — `UserActivityEvent`

```python
class ActivitySource(str, Enum):
    BRIGHTBOT_CHAT = "brightbot_chat"
    SLACK = "slack"
    WEBAPP = "webapp"
    MCP = "mcp"
    SCHEDULED_JOB = "scheduled_job"

class ActivityKind(str, Enum):
    # Growth over time. Start small; adding a kind is backward-compatible.
    CHAT_TURN = "chat_turn"
    TOOL_CALL = "tool_call"
    WORKFLOW_RUN = "workflow_run"
    SUGGESTION_EMITTED = "suggestion_emitted"
    SUGGESTION_ACTIONED = "suggestion_actioned"

class UserActivityEvent(BaseModel):
    """Every meaningful user action, one row per event.

    Superset of ProactiveSignal — that DTO becomes a `CHAT_TURN`-kind
    event with `payload.intent` populated by the capture extractor.
    """
    model_config = ConfigDict(frozen=True, serialize_by_alias=True)
    event_id: str                    # ULID
    workspace_id: str
    user_id: str
    project_id: str | None
    thread_id: str | None
    turn_id: str | None
    kind: ActivityKind
    source: ActivitySource
    observed_at: datetime            # UTC, capture-time
    outcome_ok: bool | None          # None when unknown at capture
    duration_ms: int | None
    # Redacted, normalized payload — kind-specific shape lives here.
    # Never carries raw user text; the extractor produces a redacted
    # summary/title, or an aggregate. Enforced by kind-specific
    # Pydantic sub-DTOs (registered per ActivityKind).
    payload: dict[str, Any]
    # Optional pre-computed embedding of the payload's summary. Populated
    # by capture when the extractor emits one; consumed by detectors
    # (BH-946) without re-embedding.
    embedding: list[float] | None
    # Value/priority proxy — captured by extractor from ambient signals
    # (audience size, artifact opened/shared, retry count, latency).
    # Enables the "1-shot 95%-value" case Kuri surfaced. 0.0–1.0.
    value_hint: float | None
```

### 2.2 Store Protocol

```python
class UserActivityEventStore(Protocol):
    async def write(self, event: UserActivityEvent) -> None: ...

    async def read_workspace_window(
        self, *, workspace_id: str, since: datetime,
        kinds: set[ActivityKind] | None = None,
    ) -> AsyncIterator[UserActivityEvent]: ...

    async def read_user_window(
        self, *, workspace_id: str, user_id: str, since: datetime,
    ) -> AsyncIterator[UserActivityEvent]: ...

    async def read_by_fingerprint(
        self, *, workspace_id: str, fingerprint: str, since: datetime,
    ) -> AsyncIterator[UserActivityEvent]: ...
```

Returns an async iterator so callers can process 1M-row workspaces
without materializing the full result set.

---

## 3. Invariants (DbC)

1. **Every write is workspace-scoped**. No cross-workspace event
   ever exists; cross-workspace analytics is a downstream aggregation
   over N workspace reads, never a query across workspaces.
2. **`payload` never carries raw user text**. Extractor emits redacted
   `summary` + `title` fields; PII redaction is enforced by
   kind-specific sub-DTOs (no `raw_text` field on any of them).
3. **`event_id` is monotonic within a `(workspace_id, thread_id)` pair**.
   Enables trivial "next event after X" reads without a sort.
4. **`kind` is append-only** — a new kind is a schema addition, never
   a mutation of existing rows. Old readers survive by ignoring
   unknown kinds.
5. **Retention is indefinite by default** (see §4.3). TTL applies
   only to rows with a `payload.pii_class` field set to a
   high-sensitivity value (case-by-case).
6. **Read paths never scan cross-`workspace_id`** — GSI keys are
   always partitioned by workspace to prevent noisy-neighbor and
   tenant-leak risks.
7. **`ProactiveSignal` is a projection over `CHAT_TURN`-kind rows**
   with `payload.intent.schedulable=true` — the store never
   materializes `ProactiveSignal` rows separately once the migration
   in §11 lands.

---

## 4. Data Model

### 4.1 Storage engine — DynamoDB single-table extension

**Recommendation**: extend the existing `brightroutines-{env}` table
(rename → `brightplatform-activity-{env}` per §11) rather than creating
a new store.

Rationale:
- Every existing brightroutines row already lives in this table with
  `PK=WORKSPACE#<id>`.
- Adding new SK spaces (`EVENT#…`) alongside the existing SK spaces
  (`SIGNAL#…`, `PATTERN#…`, `SUGGESTION#…`, `SCORE#…`) has no
  operational cost and no schema conflict.
- One CDK stack, one IAM boundary, one operational surface.

### 4.2 Key layout

```
PK      = WORKSPACE#<workspace_id>
SK      = EVENT#<kind>#<iso_timestamp>#<event_id>

# GSI6 — by user, all kinds, chronologically
GSI6PK  = USER#<workspace_id>#<user_id>
GSI6SK  = <iso_timestamp>#<kind>#<event_id>

# GSI7 — by (kind, fingerprint) for detector-style lookups
GSI7PK  = KIND_FP#<workspace_id>#<kind>#<fingerprint>
GSI7SK  = <iso_timestamp>#<event_id>

# GSI8 — by value_hint, DESC, per (workspace, kind)
#         for prompt-catalog "top value in W" reads
GSI8PK  = VALUE#<workspace_id>#<kind>
GSI8SK  = <inverted_value_hint_5-digit>#<event_id>
```

GSI numbers continue from BH-950's GSI5. Row shape is JSON-safe
(nested `payload` dict).

### 4.3 Retention

- Default: indefinite. The whole point of this store is to enable
  month-3-and-later analysis.
- Per-row TTL is opt-in via a `payload.retention_days` field written
  by the extractor when a high-sensitivity kind demands it (e.g.
  future PII-classification signals).
- Compaction: a nightly batch drops `chat_turn` events whose
  `outcome_ok=false` and `value_hint < 0.1` after 180 days
  (configurable) — bounds storage growth without losing anything
  worth remembering. Cheap because it's a targeted delete via the
  same value GSI.

### 4.4 Cost model

At 100k events per workspace per year with an average 8kB payload,
one workspace = ~800MB/year at ~$0.20/GB/mo DynamoDB storage =
~$1.92/workspace-year, plus $0.28 per million writes = negligible for
current fleet size. Cross-checked against the audit's per-adapter
`max_cost_per_call` budget from `pluggable-scalable.md` — well under.

---

## 5. Capture Contract

Captured by:
- **brightbot deep-agent middleware** (BH-883 part 2, still not built)
  — writes one `CHAT_TURN`-kind event per user turn, after
  `EndProcessingMiddleware`. Extractor lives here; produces
  `payload.intent`, `payload.summary` (redacted), and `value_hint`.
- **Tool wrappers** in `brightbot/audit/decorator.py` — write one
  `TOOL_CALL`-kind event per non-READONLY mutation (superset of the
  current CloudWatch audit log; that path stays for compliance
  observability, this is the queryable product surface).
- **Scheduler run hooks** — one `WORKFLOW_RUN`-kind event per
  scheduled job dispatch + completion.
- **Suggestion emit/action** — the routines suggestion pipeline
  writes `SUGGESTION_EMITTED` at offer time, `SUGGESTION_ACTIONED`
  when the user accepts/adjusts/dismisses. Feeds §11 activation-rate
  computation directly without a separate schema.

Capture is fire-and-forget — writes are async, failures log a
warning and drop the event. Detector/scoring loss is bounded by the
promotion gates in the corpus eval (BH-944); it's never a request-path
failure.

---

## 6. Read Contract

Four canonical query shapes, all indexed:

- **Workspace window** (detector, aggregator): PK partition query
  with SK `EVENT#<kind>#…` prefix and `since` filter.
- **User window** (per-user dashboards, activity feed): GSI6.
- **By kind + fingerprint** (BH-884 detector recurrence grouping):
  GSI7 — replaces the current fingerprint-only grouping with a
  server-side range query.
- **Top-K by value** (prompt catalog, "1-shot 95%-value"): GSI8 with
  `Limit=K` and inverted-score SK.

No consumer scans the whole partition; every read declares a
`(scope, since, [kind|fingerprint|value])` triple upfront.

---

## 7. Correctness Properties

### Property 1: Cross-workspace isolation

*For any* pair of workspaces `W_a`, `W_b`, no read query issued by
either surfaces events belonging to the other. Enforced by the
per-workspace GSI PK.

**Validates: §3 Invariant 1, §3 Invariant 6**

### Property 2: No raw text on any wire

*For any* consumer of the read API, no field of any returned event
carries un-redacted user text. Enforced by the capture-time
extractor's redaction contract + kind-specific sub-DTOs.

**Validates: §3 Invariant 2**

### Property 3: Append-only kind evolution

*For any* new `ActivityKind`, existing readers that filter by known
kinds see the same row set they did before the addition.

**Validates: §3 Invariant 4**

---

## 8. Eval Criteria

L1 (Pydantic): every kind's sub-DTO validates against captured samples
at test time, gate on every PR.

L2 (redaction): a corpus of hand-crafted "prompt-injection in summary"
cases must pass the extractor without leaking raw fragments —
extension of BH-944's adversarial subset. Gate when
`BH_RUN_LIVE_EVALS=1`.

L3 (E2E): the BH-947 chain test extends to seed events, run detector,
score aggregator, and prompt-catalog reader; asserts all three
consumers see the same underlying rows.

L4 (online): capture write success rate ≥ 99.9% per workspace-day;
alert on drops. Feed into the online-precision circuit-breaker from
BH-945.

---

## 9. Governance Invariants

1. Every capture site is registered in a single `_CAPTURE_KINDS`
   dict — no ad-hoc `store.write(...)` calls scattered through the
   codebase.
2. Any new `ActivityKind` requires: (a) a sub-DTO in
   `brightbot/routines/activity/kinds/`; (b) a redaction contract
   test; (c) a §5 doc update in this spec.
3. Retention overrides (`payload.retention_days`) require a comment
   citing the sensitivity rationale.

---

## 10. Test Coverage Update

Extend the existing brightbot corpora:
- **L0 surface**: schema-round-trip for every kind.
- **L1 routing**: capture middleware invoked at
  `after_agent` writes exactly one event per turn.
- **L2 behavior**: read APIs return exactly the events matching
  their filter, in chronological order, across workspaces.
- **Cross-repo**: brighthive-e2e adds a `useractivity` marker, one
  test that seeds N events across workspaces and asserts isolation
  properties #1 and #2.

---

## 11. Migration ADR — `ProactiveSignal` as projection

The concrete migration path when this spec is approved:

1. **Rename the table**: `brightroutines-{env}` →
   `brightplatform-activity-{env}` (CDK change). Aliases retained
   for 90 days.
2. **Add GSI6/7/8** alongside the existing GSI1–GSI5.
3. **Introduce `UserActivityEvent`** as the canonical DTO;
   `ProactiveSignal` remains as a Pydantic view constructed from a
   `CHAT_TURN`-kind row (never persisted separately).
4. **Migrate the capture middleware** (BH-883 part 2) to write
   `UserActivityEvent` rows directly; the detector's read path
   becomes `read_by_fingerprint(...)` filtered to
   `payload.intent.schedulable=true`.
5. **Backfill**: none required — 35-day TTL on existing signals
   means the corpus rolls over inside 6 weeks post-deploy.

No consumer breakage: the detector (BH-884), aggregator (BH-950),
and MCP tool (BH-950) all consume shapes that survive the rename
because they take `ProactiveSignal` as an already-constructed DTO,
not raw table rows.

---

## 12. Areas Involved

| Component | Repo | Change |
|---|---|---|
| CDK table | `brighthive-platform-core` | Rename + GSI6/7/8 |
| DTO + store | `brightbot` | New `brightbot/routines/activity/` package |
| Capture middleware | `brightbot` | BH-883 part 2 rewritten against new shape |
| Detector / scorer | `brightbot` | Read path adjusted to GSI7 grouping |
| MCP tools | `brightbot` | New `get_activity_events`, `top_value_prompts` |
| E2e | `brighthive-e2e` | New `useractivity` marker |
| Spec updates | `agentic-project-mgmt` | This spec + note in `brightroutines-intent-loop.md` §2 |

---

## 13. PR Split (once approved)

| PR | Repo | Scope | Ticket | Size |
|---|---|---|---:|---:|
| 1 | `brighthive-platform-core` | CDK rename + GSI6/7/8 + 90-day alias | BH-XXX | <400 lines |
| 2 | `brightbot` | `UserActivityEvent` DTO + Protocol + adapters | BH-XXX | <500 lines |
| 3 | `brightbot` | Capture middleware (BH-883 part 2 rewrite) | BH-883 | <500 lines |
| 4 | `brightbot` | Detector/aggregator read-path migration | BH-XXX | <300 lines |
| 5 | `brightbot` | New MCP tools (`get_activity_events`, `top_value_prompts`) | BH-XXX | <400 lines |
| 6 | `agentic-project-mgmt` | This spec + intent-loop §2 update | BH-942 | (this PR) |
| 7 | `brighthive-e2e` | `useractivity` marker + isolation test | BH-XXX | <300 lines |

---

## 14. Explicit non-goals for this ticket

- No implementation code in this PR — spec-only.
- No decision on the "prompt catalog UI/API" surface — that's a
  separate design pass once this store is live.
- No decision on BH-943 (SQS fan-out for scale). The store spec is
  neutral on capture concurrency; the fan-out ticket can proceed
  against either the current or the migrated table.
- No product-side changes to §9 (BH-949) — those live on a
  parallel product-decision path.
