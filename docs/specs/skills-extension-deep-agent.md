---
title: Skills Extension for deep_agent
epic: BH-860
tickets:
  - BH-861 (schema migration)
  - BH-862 (middleware)
  - BH-863 (skill content)
  - BH-864 (unit/integration tests)
  - BH-865 (e2e tests)
  - BH-866 (staging/demo)
status: draft
author: drchinca
created: 2026-06-29
last-reviewed: 2026-06-29
---

# SPEC: Skills Extension for deep_agent (Phase 1 — SSIS/SSRS Diagnostics POC)

> **Scope**: Port BrightAgent Studio's skills system to `deep_agent` with agent-affinity filtering and priority-based selection. Validate via SSIS/SSRS diagnostics skills for analyst agent.

## Jira Tickets

| Ticket | Summary | Phase | Estimate | Depends On |
|--------|---------|-------|----------|------------|
| [BH-860](https://brighthiveio.atlassian.net/browse/BH-860) | Epic: Skills Extension Framework | — | — | — |
| [BH-861](https://brighthiveio.atlassian.net/browse/BH-861) | Extend SkillModel schema | Phase 0 | 1 day | — |
| [BH-862](https://brighthiveio.atlassian.net/browse/BH-862) | Implement DeepAgentSkillsMiddleware | Phase 1 | 2-3 days | BH-861 |
| [BH-863](https://brighthiveio.atlassian.net/browse/BH-863) | Write 3 SSIS/SSRS skills | Phase 1 | 4 hours | BH-861 |
| [BH-864](https://brighthiveio.atlassian.net/browse/BH-864) | L0/L1/L2 test coverage | Phase 1 | 1 day | BH-862, BH-863 |
| [BH-865](https://brighthiveio.atlassian.net/browse/BH-865) | brighthive-e2e feature tests | Phase 1 | 1 day | BH-864 |
| [BH-866](https://brighthiveio.atlassian.net/browse/BH-866) | Staging validation + demo prep | Phase 2 | 1 day | BH-865 |

**Execution order**: BH-861 → (BH-862 + BH-863 parallel) → BH-864 → BH-865 → BH-866

---

## §1 Context

### Problem
Adding new prompting capabilities to BrightAgent's main orchestrator (`deep_agent`) requires Python code changes and redeployment. BrightAgent Studio ships a working skills system (markdown prompts, S3-backed, dynamically loaded) but it's isolated from `deep_agent`.

### What Exists Today
- **Studio skills**: `StudioSkillsMiddleware` (extends `deepagents.middleware.skills.SkillsMiddleware`), loads markdown skills from S3, revision-aware, CRUD API at `/manage/brightagent-studio/agents/{id}/skills`
- **deep_agent**: 5 hardcoded subagents in `deep_agent.py:init_agent_graphs()` (lines ~174-237), middleware stack includes `InitializationMiddleware`, `SubagentFeatureFlagMiddleware`, `OTelToolMiddleware`, no skills
- **Reusable patterns**: `sync_skills_to_s3()` / `read_skills_from_s3()` (storage.py), `StudioSharedS3Backend`, `resolve_workspace_s3_target()`, `BBState.skills_revision_applied` already exists (states.py:400)

### Goal
Extend `deep_agent` to load skills dynamically (system + workspace-scoped), filter by agent affinity, enforce token budgets. POC: 3 SSIS/SSRS diagnostic skills for analyst agent.

### Why Now
Customer demo requires SSIS/SSRS diagnostics capability. Skills system enables adding this without modifying agent graph code.

### POC Scope (from customer requirements)

**Demo target**: Legacy Analyst Analyzer Agent with 3 skills:
1. **SSIS** — Analyze SSIS packages, identify bottlenecks, suggest dbt migrations
2. **SSRS** — Analyze SSRS reports, find query bottlenecks, recommend improvements
3. **Storage Optimization** — Diagnose warehouse storage, recommend cost optimizations

**Deliverables for demo**:
- Synthetic SSIS file set (5 tables, Loop data model — Asset Management)
- Skills loaded into analyst agent
- End-to-end flow: upload SSIS → ask about bottlenecks → structured JSON response

---

## §2 Interface Contract (MDE)

### 2.1 Skill Schema (YAML Frontmatter)

**Extended `SkillModel`** (brightbot/agents/brightagent_studio/skills/models.py):
```python
class SkillModel(BaseModel):
    name: str  # existing
    description: str  # existing
    content: str  # existing
    affinity: list[str] = Field(default_factory=lambda: ["supervisor"])  # NEW
    priority: int = Field(default=50, ge=0, le=100)  # NEW
    token_estimate: int | None = None  # NEW (computed at save)
```

**SKILL.md format**:
```yaml
---
name: ssis-diagnostics
description: Analyze SSIS packages for performance bottlenecks
affinity: [analyst]
priority: 80
token_estimate: null  # auto-computed on save
version: "1.0.0"
---
# SSIS Diagnostics Skill
[markdown content]
```

### 2.2 Storage Paths

| Scope | Path | Mutability | Loaded |
|---|---|---|---|
| System | `brightbot/skills/system/{skill_name}/SKILL.md` | Immutable (repo) | Startup once |
| Workspace | `s3://{workspace_bucket}/skills/{skill_name}/SKILL.md` | Mutable (S3) | Per-turn if revision changed |

### 2.3 Middleware Hook Contract

**New middleware**: `DeepAgentSkillsMiddleware` (extends `deepagents.middleware.skills.SkillsMiddleware`)

```python
class DeepAgentSkillsMiddleware(SkillsMiddleware):
    def before_agent(self, state: BBState, runtime: Runtime, config: RunnableConfig) -> dict | None:
        """Load system + workspace skills, filter by agent, select top-N by priority within token budget."""
        # Returns: {"skills_metadata": [...], "skills_revision_applied": int}
```

**No before_model override** — reuse `SkillsMiddleware.wrap_model_call()` for progressive disclosure (already does description injection + `read_file()` pattern).

### 2.4 Token Budget Selection (Priority-Based Greedy)

```python
def select_skills(
    candidates: list[SkillMetadata],
    agent_name: str,
    token_budget: int = 6000  # reserve 2k for output
) -> list[SkillMetadata]:
    """
    Filter by affinity, sort by priority descending, greedy select until budget exhausted.
    """
    filtered = [s for s in candidates if agent_name in s.affinity or "supervisor" in s.affinity]
    filtered.sort(key=lambda s: s.priority, reverse=True)
    
    selected, consumed = [], 0
    for skill in filtered:
        tokens = skill.token_estimate or estimate_tokens_langchain(skill.content)
        if consumed + tokens <= token_budget:
            selected.append(skill)
            consumed += tokens
    
    return selected
```

**Token measurement**: Use `langchain_core.language_models.chat_models.count_tokens_approximately(text)` (exists) or `anthropic_client.messages.count_tokens(...)` (modern SDK). **Never** `anthropic.count_tokens()` (deprecated, doesn't exist in this codebase).

---

## §3 Invariants (DbC)

1. **Affinity filter correctness**: For any agent A, `state["skills_metadata"]` MUST contain only skills where `A in skill.affinity OR "supervisor" in skill.affinity`.

2. **Priority monotonicity**: Selected skills MUST be ordered by `priority` descending. If skill S1 is selected and S2 is dropped, then `S1.priority >= S2.priority OR (S1.priority == S2.priority AND S1.token_estimate <= S2.token_estimate)`.

3. **Budget enforcement**: Sum of `token_estimate` for selected skills MUST be ≤ 6000 tokens.

4. **Revision consistency**: If `state["skills_revision_applied"] == configurable["skills_revision"]`, skills MUST NOT be reloaded (cache hit).

5. **System skills immutability**: System skills (repo-versioned) MUST NOT change without a code deploy.

6. **Workspace isolation**: Workspace W1 skills MUST NOT appear in workspace W2 state.

7. **Graceful degradation**: If workspace skills S3 read fails, system skills MUST still load (fallback to system-only).

---

## §4 Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Skills Extension for deep_agent

  Scenario: System skills load at graph initialization
    Given deep_agent graph is initialized
    And system skills directory contains "ssis-diagnostics", "ssrs-diagnostics", "storage-optimization"
    When the first agent turn runs
    Then state["skills_metadata"] contains 3 system skills
    And each skill has "name", "description", "affinity", "priority", "token_estimate"

  Scenario: Agent affinity filtering
    Given analyst agent is active
    And system skills include "ssis-diagnostics" (affinity: [analyst]) and "dbt-preview" (affinity: [dbt])
    When skills are compiled for analyst agent
    Then state["skills_metadata"] includes "ssis-diagnostics"
    And state["skills_metadata"] does NOT include "dbt-preview"

  Scenario: Priority-based selection within token budget
    Given 5 skills with priorities [100, 80, 60, 40, 20] and token_estimate [2000, 2000, 2000, 2000, 2000]
    And token budget is 6000
    When skills are selected
    Then selected skills are [100, 80, 60] (total 6000 tokens)
    And skills [40, 20] are dropped

  Scenario: Workspace skills override system skills
    Given system skill "ssis-diagnostics" exists with priority 80
    And workspace uploads custom skill "ssis-diagnostics" with priority 90
    When skills are compiled
    Then workspace "ssis-diagnostics" is selected (higher priority)
    And system "ssis-diagnostics" is dropped

  Scenario: Revision-aware reload
    Given skills_revision_applied = 5
    And workspace uploads new skill (skills_revision bumps to 6)
    When next agent turn runs
    Then skills are reloaded from S3
    And skills_revision_applied = 6 in state

  Scenario: Graceful S3 failure
    Given system skills are loaded
    And workspace S3 bucket is unavailable
    When agent turn runs
    Then system skills are used
    And error is logged
    And agent turn does NOT fail

  Scenario: SSIS diagnostics execution (end-to-end)
    Given analyst agent is active
    And "ssis-diagnostics" skill is loaded
    And user uploads SSIS .dtsx file
    When user asks "Analyze this SSIS package for bottlenecks"
    Then agent reads "ssis-diagnostics" skill via read_file()
    And agent returns JSON with "bottlenecks", "dbt_migration_suggestions", "estimated_speedup"
```

---

## §5 Out of Scope

- Agent plugin registry (Phase 2)
- JSON schema → LangChain tool auto-wrapper (Phase 3)
- Semantic search for skills (no FAISS index; greedy priority selection only)
- Custom cache partitioning (reuse existing `BedrockPromptCachingMiddleware` behavior, don't override)
- Health checks / circuit breakers (Phase 2)
- CRUD API for system skills (system skills are repo-versioned only; workspace skills reuse Studio's existing API)

---

## §6 Dependencies

- ✅ `deepagents.middleware.skills.SkillsMiddleware` (exists, used by Studio)
- ✅ `StudioSkillsMiddleware` (exists, proven in prod)
- ✅ `sync_skills_to_s3()` / `read_skills_from_s3()` (storage.py)
- ✅ `BBState.skills_revision_applied` (states.py:400)
- ✅ `langchain_core.language_models.chat_models.count_tokens_approximately()` or `anthropic_client.messages.count_tokens()`
- ⚠️ **New**: Extend `SkillModel` Pydantic schema with `affinity`, `priority`, `token_estimate` (Phase 0 — schema migration first)

---

## §7 Correctness Properties

### Property 1: Affinity isolation
*For any* agent A and skill S, *if* S is in state["skills_metadata"] for agent A, *then* `A in S.affinity OR "supervisor" in S.affinity`.

**Validates: §3 Invariant 1, §4 Scenario "Agent affinity filtering"**

### Property 2: Priority dominance
*For any* two skills S1 and S2 where S1 is selected and S2 is dropped, *either* `S1.priority > S2.priority` *or* (`S1.priority == S2.priority` AND `S1.token_estimate <= S2.token_estimate`).

**Validates: §3 Invariant 2, §4 Scenario "Priority-based selection within token budget"**

### Property 3: Budget ceiling
*For all* selected skills in a given turn, `sum(s.token_estimate for s in selected) <= TOKEN_BUDGET`.

**Validates: §3 Invariant 3, §4 Scenario "Priority-based selection within token budget"**

### Property 4: Revision idempotence
*If* `state["skills_revision_applied"] == configurable["skills_revision"]`, *then* `before_agent()` returns `None` (cache hit, no rescan).

**Validates: §3 Invariant 4, §4 Scenario "Revision-aware reload"**

### Property 5: Fallback safety
*If* workspace S3 read raises exception, *then* system skills are selected AND error is logged AND agent turn completes (no crash).

**Validates: §3 Invariant 7, §4 Scenario "Graceful S3 failure"**

---

## §8 Eval Criteria

> Not applicable — skills are prompt fragments, not LLM-behavior surfaces. No LLM judge evaluators needed for this spec. Quality is verified by §10 test corpora (L0/L1/L2 assertions + e2e).

---

## §9 Observability Contract

### Spans (OTel GenAI semantic conventions)

**Span: `brightagent.skills.load`** (before_agent hook)
- **Attributes**:
  - `brightagent.agent.name` (current agent, e.g., "analyst")
  - `brightagent.skills.system_count` (# system skills loaded)
  - `brightagent.skills.workspace_count` (# workspace skills loaded)
  - `brightagent.skills.selected_count` (# skills selected after affinity + budget filter)
  - `brightagent.skills.dropped_count` (# skills dropped due to budget)
  - `brightagent.skills.revision_applied` (skills_revision after load)
  - `workspace.id`
- **Log events**:
  - `skills.load.started`
  - `skills.load.success` OR `skills.load.workspace_fallback` (S3 failure)
- **Metrics**: none (span duration is the metric)

**Span: `gen_ai.tool.execute` (existing, when agent calls `read_file()` for skill content)**
- **Attributes**:
  - `gen_ai.tool.name = "read_file"`
  - `gen_ai.tool.parameters = {"path": "/skills/system/ssis-diagnostics/SKILL.md"}`
  - `gen_ai.tool.output_size_bytes`

### Metrics

- `skills_dropped_total` (counter, labels: `agent_name`, `reason=budget_exceeded`)
- `skills_load_duration_ms` (histogram, p50/p95/p99)
- `workspace_s3_failure_total` (counter, labels: `workspace_id`)

---

## §10 Test Coverage Update

### a. In-repo layered evals (brightbot/tests/)

**L0 (surface) — `tests/unit/test_skills_schema.py`**:
- Assert `SkillModel` accepts `affinity`, `priority`, `token_estimate` fields
- Assert validation: `priority` ∈ [0, 100], `affinity` is list of strings

**L1 (routing / orchestration) — `tests/integration/test_skills_loading.py`**:
- `test_system_skills_loaded()`: Assert 3 system skills in state after graph init
- `test_affinity_filtering()`: Analyst agent sees analyst-affinity skills, dbt agent doesn't
- `test_priority_selection()`: 5 skills with total 10k tokens, budget 6k → top 3 by priority selected
- `test_revision_cache_hit()`: If revision unchanged, `before_agent()` returns None (no rescan)
- `test_workspace_s3_failure_fallback()`: Mock S3 error → system skills load, error logged, no crash

**L2 (behavior) — `tests/integration/test_skills_execution.py`**:
- `test_analyst_reads_ssis_skill()`: Analyst agent active → LLM calls `read_file(/skills/system/ssis-diagnostics/SKILL.md)` → skill content returned
- `test_token_budget_enforcement()`: Skills totaling 10k tokens offered → state contains ≤6k tokens of skills
- `test_observability_span_emitted()`: OTel span `brightagent.skills.load` present with correct attributes

### b. Cross-repo end-to-end tests (brighthive-e2e/)

**Feature test** (`brighthive-e2e/tests/features/skills_ssis_diagnostics.feature`):
```gherkin
Feature: SSIS Diagnostics via Skills

  Scenario: Analyst agent applies SSIS diagnostics skill
    Given analyst agent is available
    And "ssis-diagnostics" skill is loaded
    When user uploads SSIS .dtsx file
    And user asks "What are the performance bottlenecks?"
    Then response contains "bottlenecks" field (JSON)
    And response contains "dbt_migration_suggestions" field (JSON)
    And LangSmith trace shows read_file call for "ssis-diagnostics"
```

**Surface test** (`brighthive-e2e/tests/surfaces/test_mcp_skills.py`):
- `test_deep_agent_skills_endpoint()`: GET `/bh-mcp/.well-known/skills` returns 3 system skills (or equivalent introspection)
- `test_workspace_skills_crud()`: POST workspace skill → PUT update → GET list → DELETE → verify 404

**Error-path coverage** (`brighthive-e2e/tests/surfaces/test_skills_error_handling.py`):
- `test_invalid_skill_yaml()`: Upload skill with malformed frontmatter → 400 Bad Request
- `test_s3_unavailable()`: Disconnect S3 → deep_agent still works with system skills only

---

## Critical Files

### New Files (Phase 0 — schema migration)
1. **`brightbot/agents/brightagent_studio/skills/models.py`** — MODIFY: Add `affinity`, `priority`, `token_estimate` to `SkillModel`

### New Files (Phase 1 — skills loading)
1. **`brightbot/agents/shared_middleware/deep_agent_skills_middleware.py`** — `DeepAgentSkillsMiddleware` (extends `SkillsMiddleware`)
2. **`brightbot/skills/system_loader.py`** — Scans `brightbot/skills/system/` at startup, returns list of `SkillMetadata`
3. **`brightbot/skills/system/ssis-diagnostics/SKILL.md`** — SSIS bottleneck analysis skill
4. **`brightbot/skills/system/ssrs-diagnostics/SKILL.md`** — SSRS report optimization skill
5. **`brightbot/skills/system/storage-optimization/SKILL.md`** — Warehouse cost analysis skill

### Modified Files (Phase 1)
1. **`brightbot/agents/super_agent/deep_agent.py`** — Add `DeepAgentSkillsMiddleware()` to middleware stack (AFTER SubagentFeatureFlagMiddleware, BEFORE InitializationMiddleware — verify actual order via exploration first)
2. **`brightbot/workflows/states.py`** — VERIFY `skills_revision_applied` exists (it does, line 400); add `skills_metadata: list[dict]` if missing

### New Test Files
1. **`tests/unit/test_skills_schema.py`** — L0 schema validation
2. **`tests/integration/test_skills_loading.py`** — L1 loading + affinity + priority
3. **`tests/integration/test_skills_execution.py`** — L2 behavior + observability
4. **`brighthive-e2e/tests/features/skills_ssis_diagnostics.feature`** — e2e Gherkin
5. **`brighthive-e2e/tests/surfaces/test_mcp_skills.py`** — surface contract
6. **`brighthive-e2e/tests/surfaces/test_skills_error_handling.py`** — error paths

---

## Implementation Phases

### Phase 0: Schema Migration (1 day) — BH-861
- Extend `SkillModel` Pydantic schema with `affinity`, `priority`, `token_estimate`
- Update `sync_skills_to_s3()` / `read_skills_from_s3()` to serialize/deserialize new fields
- Update Studio CRUD routes to accept new fields (optional, default values)
- Write L0 unit tests for schema validation
- **Acceptance**: `SkillModel(name="test", description="test", content="test", affinity=["analyst"], priority=80, token_estimate=1200)` validates

### Phase 1: Skills Loading (2-3 days) — BH-862, BH-863, BH-864
- Write `brightbot/skills/system_loader.py` (scan `brightbot/skills/system/`)
- Write `DeepAgentSkillsMiddleware`:
  - `before_agent()`: Load system + workspace skills, filter by affinity, select by priority within 6k budget
  - Reuse `SkillsMiddleware.wrap_model_call()` (no override needed)
- Integrate into `deep_agent.py` middleware stack (insertion point: after SubagentFeatureFlagMiddleware, before InitializationMiddleware — **verify order via grep first**)
- Write 3 SSIS/SSRS skill markdown files
- Add OTel span `brightagent.skills.load` with attributes
- Write L1 + L2 integration tests
- **Acceptance**: All §4 Gherkin scenarios pass (unit + integration tests green)

### Phase 2: End-to-End Validation (1 day) — BH-865, BH-866
- Deploy to staging (`brightagent-staging`)
- Run `brighthive-e2e` feature test: upload SSIS file, invoke analyst, verify skill applied
- Monitor LangSmith trace: confirm `read_file(/skills/system/ssis-diagnostics/SKILL.md)` call present
- Monitor OTel: confirm `brightagent.skills.load` span emitted with correct attributes
- **Acceptance**: e2e feature test passes, zero regressions in existing `deep_agent` behavior (CI green)

---

## Anti-Patterns (What NOT To Do)

1. **Don't use `anthropic.count_tokens()`** — it's deprecated and doesn't exist in this codebase. Use `langchain_core.language_models.chat_models.count_tokens_approximately()` or `anthropic_client.messages.count_tokens()`.

2. **Don't run token counting at runtime** — pre-compute at save time (Lambda trigger on S3 PUT) or estimate via LangChain approximator. Runtime tokenization adds unacceptable latency (5-20ms per skill × 100 skills = 500ms+).

3. **Don't override `before_model()`** — reuse `SkillsMiddleware.wrap_model_call()` which already does progressive disclosure (description injection + `read_file()` tool). Adding a second compilation step duplicates work and fights the existing prompt caching.

4. **Don't invent parallel state fields** — Studio already uses `skills_metadata` (via deepagents). Don't add a separate `skills: list[dict]` field. Reuse the proven path.

5. **Don't touch `BedrockPromptCachingMiddleware`** — it already manages cache_control placement. Don't layer custom cache partitioning on top; it will cause cache-miss storms. Let the existing middleware handle caching.

6. **Don't add semantic search** — FAISS index, embeddings, retrieval = Phase 3 complexity. This spec is greedy priority selection only. If a skill is dropped, the LLM can call `list_available_skills()` tool to discover it.

7. **Don't hard-code middleware position "0"** — the real stack has SubagentFeatureFlagMiddleware and OTelToolMiddleware before InitializationMiddleware. Grep the actual order first, then insert AFTER feature flags, BEFORE initialization.

---

## Success Criteria (Verification)

### Pre-Merge Checklist
- [ ] All §4 Gherkin scenarios have corresponding test cases (unit + integration)
- [ ] All §10 L0/L1/L2 tests green locally
- [ ] OTel span `brightagent.skills.load` emitted with correct attributes (verified in test)
- [ ] Zero regressions: existing `deep_agent` tests green (run full `tests/integration/` suite)
- [ ] Staging deploy successful, `brighthive-e2e` feature test passes

### Demo-Ready Criteria
- [ ] 3 SSIS/SSRS system skills loaded into `deep_agent` state
- [ ] Analyst agent reads "ssis-diagnostics" skill via `read_file()` (LangSmith trace shows call)
- [ ] SSIS diagnostics execution returns JSON with "bottlenecks", "dbt_migration_suggestions" (e2e test passes)
- [ ] No >5s gaps in streamed reasoning (existing StreamingMiddleware behavior preserved)
