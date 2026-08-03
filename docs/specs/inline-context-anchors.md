# Spec: Context Anchors — inline entity references for BrightAgent chat

- **Epic**: BH-1353
- **Tickets**: BH-1354 (composer), BH-1355 (stream contract), BH-1356 (resolver), BH-1357 (data sources), BH-1358 (evals)
- **Status**: Draft
- **Last-Reviewed**: 2026-08-03
- **Repos touched**: `brighthive-webapp` (composer + stream input), `brightbot` (resolver + grounding + evals). Reference data read from `brighthive-platform-core` GraphQL (no new queries).

## Glossary

- **Context Anchor**: a user-selected entity (warehouse, table, knowledge-base asset, pipeline, or project) referenced inline in a chat message, resolved to a canonical id and threaded to the agent as preferred grounding context.
- **Sigil**: the trigger character that opens the picker — `@` (data), `#` (knowledge base), `/` (command), `[` (project).
- **Soft-hint grounding**: a resolved anchor becomes strong *preferred* context — the agent starts grounded on it and skips the guess-and-confirm loop — but MAY still branch to strongly related sources. Not a hard allowlist.
- **Reference**: the structured record for one anchor — `{type, id, name, fqn?}`.
- **`session_info`**: the JSON identity blob (`workspace_id`, `token`, `user_id`, optional `project_id`) that every brightbot tool reads out of graph state. The universal carrier we extend with `references`.
- **`data_assets_to_be_appended`**: existing `BBState` field consumed by `MetadataInjectionMiddleware` to pre-load specific asset metadata into the agent filesystem before it runs, short-circuiting vector search.
- **FQN**: fully-qualified table name (`db.schema.table`) — the canonical table identifier in platform-core (`DataAsset.tableFQN`).

## 1. Context

In BrightAgent sessions the agent frequently "trips" — it disambiguates incorrectly about *which* warehouse, table, knowledge base, pipeline, or project a question refers to. Grounding today is implicit: inbound state carries only `workspace_id` / `token` / `user_id` (+ optional `project_id`), and the agent resolves the target entity per-turn by running a vector search over the raw question text (`discover_data_assets`), then leans on disambiguation classifiers (BH-761), a data-presence check (BH-776/777), and a KB relevance floor (BH-777) to avoid answering the wrong reading. The user has no way to simply *say which one they mean*.

Context Anchors closes this: the user references entities inline with typed sigils, the frontend resolves them to canonical ids and sends a structured `references[]` channel, and the backend pre-grounds the run on those entities — skipping the guess. Grounding is soft-hint so the agent stays helpful (may pull strongly related data) without caging.

This is largely **wiring existing seams**, not greenfield: the webapp already ships a `pendingDataAssets` store + `data_assets_to_be_appended` channel + a modal `DataAssetSelector`; brightbot already ships `MetadataInjectionMiddleware` that pre-loads chosen assets and short-circuits vector search. V1 moves the selection inline, generalizes it to five entity types, and teaches the resolver to skip disambiguation when an entity is explicitly named.

```mermaid
sequenceDiagram
    actor U as User
    participant C as ChatField (webapp)
    participant S as useAgentStream
    participant I as InitializationMiddleware
    participant M as MetadataInjectionMiddleware
    participant A as Analyst/Retrieval agent
    U->>C: types "@snowflake.ORDERS trends?"
    C->>C: sigil picker → reference {type:table, id, fqn}
    C->>S: submit(message, references[])
    S->>I: session_info.references[] (SSE run)
    I->>I: resolve refs → canonical assets (Platform Core GraphQL)
    I->>M: data_assets_to_be_appended = resolved
    M->>A: pre-load ORDERS metadata; skip discover_data_assets guess
    A-->>U: grounded answer (soft-hint: may add related)
```

## 2. Interface Contract (MDE)

### 2.1 Reference (shared TS + wire shape)

```typescript
type ReferenceType = "warehouse" | "table" | "knowledge_base" | "pipeline" | "project";

interface Reference {
  type: ReferenceType;
  id: string;        // canonical id: DataAsset.id, warehouseService.id, resource id, dbt job id, project uuid
  name: string;      // display name shown in the chip
  fqn?: string;      // table only: DataAsset.tableFQN (db.schema.table)
}
```

### 2.2 Stream input (webapp → brightbot)

Extends `baseInput` in `src/BrightAgent/hooks/useAgentStream.ts` (~line 518):

```
input: {
  hitl_enabled: boolean,
  messages: [humanMessage],
  page_context: PageContext,
  persona?: Persona,
  references?: Reference[],          // NEW — omitted/[] when user anchors nothing
  ...dataAssetsInput
}
```

### 2.3 session_info carrier (brightbot)

`session_info` JSON gains an optional key; parser stays backward-compatible:

```
session_info = {
  workspace_id: str,
  token: str,
  user_id: str,
  project_id?: str,
  references?: [ { type, id, name, fqn? } ]   // NEW
}
```

`parse_session_info` (`brightbot/utils/session_info.py`) MUST return `references == []` when the key is absent — never raise.

### 2.4 Resolution (brightbot, at turn start)

```
resolve_references(references: list[Reference], workspace_id: str, token: str)
  -> ResolvedContext {
       assets: list[DataAssetMeta],   # feeds data_assets_to_be_appended
       project_id: str | None,        # from a project reference
       kb_file_ids: list[str],        # from knowledge_base references
       pipeline_ids: list[str],       # from pipeline references
     }
  raises: none (unresolvable refs are dropped + logged, never fail the turn)
```

## 3. Invariants (DbC)

1. `references` absent/empty ⇒ agent behavior is byte-for-byte the current behavior (no regression). — EARS: `IF references is empty, THEN THE System SHALL run the existing discover-and-confirm flow unchanged.`
2. A resolved table reference pre-loads that asset's metadata via `data_assets_to_be_appended` before the agent runs. — `WHEN a table reference resolves, THE System SHALL inject its metadata and SHALL NOT vector-search to rediscover it.`
3. Grounding is soft-hint: a resolved reference is preferred context, never a hard allowlist. — `WHERE a reference resolves, THE System SHALL prefer it AND MAY use strongly-related assets.`
4. Disambiguation (`classify_question`) is suppressed for an entity that an explicit reference already resolved. — `WHEN an entity is explicitly referenced, THE System SHALL NOT emit a clarifying ASK about which entity was meant.`
5. Reference ids and tokens are never accepted as tool arguments — they arrive only via `session_info` from the authenticated principal. — preserves the existing MCP invariant (`test_no_principal_fields_in_tool_args`).
6. An unresolvable reference (deleted/renamed/no-access) is dropped and logged; the turn proceeds as if it were not present — never a hard failure.
7. References are workspace-scoped: a reference id that does not belong to the caller's `workspace_id` is dropped (no cross-workspace grounding).
8. References clear on message send and on thread switch (frontend) — an anchor is per-message, not sticky, in V1.

## 4. Acceptance Criteria (BDD)

```gherkin
Feature: Context Anchors — inline entity references

  Scenario: Anchor a table, skip the guess
    Given a workspace with a Snowflake table ORDERS
    When the user types "@snowflake.ORDERS what were last month's trends?" and sends
    Then the stream input carries references[] with a table reference for ORDERS
    And ORDERS metadata is pre-loaded before the agent runs
    And the agent does not run discover_data_assets to rediscover ORDERS

  Scenario: Soft-hint allows related data
    Given the user anchored @ORDERS
    When the agent finds a strongly related table ORDER_ITEMS is needed
    Then the agent MAY use ORDER_ITEMS in addition to ORDERS

  Scenario: Disambiguation suppressed on explicit reference
    Given a question that would normally trigger a "which table did you mean?" ASK
    When the user anchored the exact table with @
    Then the agent answers without asking which entity was meant

  Scenario: No reference — unchanged behavior
    Given the user sends a message with no sigils
    When the turn runs
    Then behavior is identical to the current discover-and-confirm flow

  Scenario: Anchor a knowledge base
    When the user types "#churn-kb summarize the retention policy" and sends
    Then references[] carries a knowledge_base reference
    And query_knowledge_base is scoped to that KB's file ids

  Scenario: Run a pipeline via command
    When the user types "/run daily-etl" and selects the dbt job
    Then references[] carries a pipeline reference with the dbt job id
    And the agent schedules/triggers that job (existing run path)

  Scenario: Scope to a project
    When the user types "[project: Q3-close]" and selects it
    Then references[] carries a project reference
    And the turn is project-scoped (project_id set)

  Scenario: Unresolvable reference is dropped
    Given the user anchored a table that was since deleted
    When the turn starts
    Then the reference is dropped and logged
    And the turn proceeds without failing

  Scenario: Cross-workspace reference rejected
    Given a reference id that belongs to another workspace
    When the turn starts
    Then the reference is dropped (workspace-scoped grounding only)
```

## 5. Out of Scope

- Cross-workspace / cross-org references.
- Freeform natural-language entity linking without a sigil — still handled by existing vector search.
- Sticky/pinned anchors that persist across messages (V1 anchors are per-message).
- Hard-scope allowlisting (V1 is soft-hint only; a future toggle could add hard scope).
- Write-path actions beyond running an existing pipeline/dbt job.
- New GraphQL queries — V1 reuses existing generated Apollo hooks.

## 6. Dependencies

- **Entity data (read-only, existing)**: `GetWarehouseServicesDocument`, `GetDataAssetsForBrightAgentDocument` / `SearchDataAssetsDocument`, `GetResourcesDocument`, `GetDbtJobsDocument`, `GetProjectsDocument` (all in `brighthive-webapp/src/generated.ts`).
- **Canonical ids**: platform-core `schema.graphql` — `DataAsset.id`/`tableFQN` (794–808), `Project.uuid`, `WarehouseServiceOutput.id` (2905), KB `file_id`, dbt job id.
- **Grounding path**: `MetadataInjectionMiddleware` (`brightbot/agents/super_agent/middleware/metadata_injection_middleware.py:44`), `data_assets_to_be_appended` (`brightbot/workflows/states.py:364`).
- **Ordering**: BH-1355 (contract) can land first; BH-1354 (composer) + BH-1357 (sources) build the UI; BH-1356 (resolver) depends on the contract; BH-1358 (evals) depends on the resolver.

## 7. Correctness Properties

### Property 1: No-regression on unreferenced turns

*For any* message with no `references`, the agent's execution path, tool calls, and output are identical to the pre-feature behavior.

**Validates: §3 Invariant 1, §4 Scenario "No reference — unchanged behavior"**

### Property 2: Referenced entity is grounded, not re-discovered

*For any* resolved table reference, the agent runs with that asset's metadata pre-loaded and does not issue a vector search to rediscover the same entity.

**Validates: §3 Invariant 2, §4 Scenario "Anchor a table, skip the guess"**

### Property 3: Soft-hint, not cage

*For any* resolved reference, the agent is free to use strongly-related assets in addition to the referenced one.

**Validates: §3 Invariant 3, §4 Scenario "Soft-hint allows related data"**

### Property 4: Workspace isolation

*For any* reference whose id does not belong to the caller's workspace, the reference is dropped before grounding.

**Validates: §3 Invariant 7, §4 Scenario "Cross-workspace reference rejected"**

### Property 5: Graceful degradation on unresolvable references

*For any* reference that cannot be resolved, the turn proceeds without error and logs the drop.

**Validates: §3 Invariant 6, §4 Scenario "Unresolvable reference is dropped"**

## 8. Eval Criteria

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| ReferenceGroundingEvaluator | initialization_middleware | GATE | referenced asset pre-loaded == true | deterministic |
| DisambiguationSuppressionEvaluator | analyst_agent | GATE | no ASK when entity referenced | deterministic |
| NoRegressionEvaluator | deep_agent | GATE | unreferenced path unchanged | deterministic (golden replay) |
| SoftHintEvaluator | retrieval_agent | OBSERVE | related-asset use allowed | LLM judge |

## 9. Observability Contract

- **Span**: `gen_ai.agent.turn` gains attribute `brightagent.references.count` and `brightagent.references.types`.
- **Attributes**: `workspace.id`, `brightagent.references.count`, `brightagent.references.resolved`, `brightagent.references.dropped`.
- **Log events**: `context_anchor.resolved` (per reference), `context_anchor.dropped` (unresolvable/cross-workspace, with reason), `context_anchor.disambiguation_suppressed`.
- **Metrics**: none in V1.

## 10. Test Coverage Update

### a. In-repo layered evals (`brightbot/evals`)

- **L0 (surface):** `references[]` present/absent in stream input; `session_info` parse with and without `references` (§2.2, §2.3); reference type shape (§2.1). One case per §2 contract entry.
- **L1 (routing):** a message with a resolvable table reference reaches `resolve_references` and pre-loads the asset (§4 "Anchor a table"); `#kb` reference scopes `query_knowledge_base`; `[project:]` sets project scope. One case per §4 routing-observable scenario.
- **L2 (behavior):** one case per §3 invariant — pre-grounding (Inv 2), disambiguation suppression (Inv 4), soft-hint branching (Inv 3), no-regression golden replay (Inv 1), unresolvable drop (Inv 6), cross-workspace drop (Inv 7). One case per §8 evaluator at its threshold. Span/log assertions (§9) alongside the behavior.
- **Real-behavior (mandatory):** at least one L2 that boots the real deep-agent graph with a real session_info carrying a real captured reference and asserts the observable pre-grounding side effect — not a mock.

### b. Cross-repo e2e (`brighthive-e2e`)

- One feature test: user anchors `@table` in the composer → SSE payload carries `references[]` → agent answers grounded, against the real staging backend.
- One surface test per changed boundary: stream input shape with `references[]`; session_info parse.
- One error-path: unresolvable reference against the real backend proceeds without 500.

### Fixtures

The `references[]` payload fixture MUST be captured from a real stream run (mint a real message with an anchor, record the actual `input`), not hand-typed — per `test-behavior-real` and the fixtures-mirror-reality rule.
