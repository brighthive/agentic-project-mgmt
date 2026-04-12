---
title: "dbt Agent ReAct Migration"
epic: "BH-172"
author: "drchinca"
status: "In Progress"
created: "2026-04-12"
generates: "tickets"
tags: [dbt, react, migration, agents, langgraph]
related:
  features: []
  pocs: []
  bedrock: []
---

# dbt Agent ReAct Migration

## Problem

The dbt agent is the only BrightBot subagent still using the legacy deterministic StateGraph pattern. Every other agent (retrieval, analyst, governance, visualization, ingestion) has been migrated to the modern ReAct pattern using `create_agent()` with `@tool`-decorated functions and `ToolRuntime`.

The current implementation spans 4,403 lines across 5 files with a hardcoded 4-node workflow (`dbt_credentials -> dbt_processing -> dbt_commit -> register_transformation`). Each "node" internally contains multiple sequential stages that cannot be reordered, retried, or skipped. The LLM has zero autonomy over the pipeline -- it generates SQL inside a fixed stage but cannot decide to re-validate, skip credential checks for cached sessions, or adapt the workflow based on errors.

This causes three concrete problems:

1. **Brittleness** -- Any failure in the linear pipeline requires restarting from scratch. The agent cannot retry a single stage or skip ahead when state is already populated from a previous attempt.
2. **Maintenance cost** -- Modifying one stage (e.g., adding Snowflake dbt support) requires touching monolithic 1,300-line files where concerns are entangled. Contrast with retrieval agent: adding a new tool is a single file with zero coupling.
3. **Pattern divergence** -- The dbt agent cannot use shared middleware (OTel instrumentation, tool limiters, streaming middleware, filesystem access) that every other agent benefits from. New platform capabilities bypass dbt entirely.

## Use Case / Goal

Success is a dbt agent that follows the exact same architecture as every other BrightBot subagent:

- Single ReAct agent created via `create_agent()` with 10 standalone tools
- LLM autonomously decides which tools to call and in what order
- Each tool is independently testable with mocked externals
- Shared middleware stack (OTel, limiters, streaming) works out of the box
- Supervisor integration unchanged -- `CompiledSubAgent(name="dbt", ...)` still works
- HITL (human-in-the-loop) PR approval interrupt still works with the webapp
- Backward-compatible state: `dbt_result`, `github_pr_url`, `platform_transformation_id` still populate in `BBState`
- Total agent code drops from ~4,400 lines to ~800 lines (tools + agent + prompt)

## Current Situation

### How It Works Today

**4-node deterministic StateGraph** defined in `deep_agent.py` via `create_dbt_workflow()`:

```
START -> dbt_credentials -> dbt_processing -> dbt_commit -> register_transformation -> END
```

Each node is a monolithic function that runs multiple stages sequentially:

| Node | File | Lines | Internal Stages |
|------|------|-------|-----------------|
| `dbt_credentials_engine` | `super_agent/nodes/agents/dbt.py` | 411-688 | Fetch workspace config, validate GitHub PAT, fetch dbt project sources.yaml |
| `call_dbt_agent` | `dbt_agent/dbt_agent.py` | Full file | SQL generation, code review, dbt conversion, dbt validation (MCP), error analysis |
| `commit_models_to_github` | `super_agent/nodes/agents/dbt.py` | 126-408 | Update sources.yaml, commit files, create PR (HITL interrupt) |
| `register_transformation` | `super_agent/nodes/agents/dbt.py` | 1112-1301 | Register transformation via Platform Core GraphQL |

**Supporting files:**

| File | Lines | Purpose |
|------|-------|---------|
| `super_agent/nodes/agents/dbt.py` | 1,335 | Credentials, commit, registration, orchestration |
| `dbt_agent/dbt_agent.py` | 1,251 | SQL gen, code review, dbt conversion, validation |
| `super_agent/dbt_github_utils.py` | 1,104 | GitHub interactive flows, branch management |
| `dbt_agent/utils.py` | 428 | Schema embedding, helper functions |
| `prompts/dbt_agent_prompts.py` | 285 | System prompts for each stage |
| **Total** | **4,403** | |

### Hard Limitations

1. **No retry granularity** -- If dbt validation fails after SQL generation succeeds, the entire pipeline must restart. The LLM cannot decide to just re-run validation with a fix.
2. **No middleware support** -- The deterministic graph bypasses the `create_agent()` middleware stack. No OTel tool-level tracing, no tool call limits, no filesystem middleware.
3. **No tool reuse** -- Individual capabilities (e.g., "validate this dbt model") cannot be exposed to other agents or composed into new workflows.
4. **Hardcoded iteration limits** -- Code review runs exactly once, validation retries are baked into loop counters inside node functions, not configurable via system prompt or middleware.

### Gaps

- No unit tests for individual stages (only integration tests for the full pipeline)
- No way to add new dbt capabilities (e.g., dbt test generation, incremental model support) without modifying monolithic files
- HITL interrupt implementation in `dbt.py:307-332` is tightly coupled to the graph node, not extractable as a tool pattern
- No feature flag to toggle between old and new implementations during migration

## Proposals / Solutions

### Recommended Approach

Rewrite as a standard ReAct subagent following `docs/CREATING_SUBAGENTS.md`, extracting each stage into a standalone `@tool`-decorated function. The LLM calls tools autonomously via the ReAct loop, with iteration limits enforced by the system prompt and `create_tool_limiter()` middleware.

**Target file structure:**

```
brightbot/agents/dbt_agent/
├── dbt_agent_react.py              # Main agent (~130 lines) [Phase 0 - EXISTS]
├── state.py                        # DbtReactState schema [Phase 0 - EXISTS]
├── tools/
│   ├── __init__.py
│   ├── credentials_tools.py        # validate_dbt_credentials
│   ├── source_tools.py             # fetch_dbt_sources
│   ├── sql_tools.py                # generate_sql_model, review_sql_code
│   ├── dbt_tools.py                # convert_sql_to_dbt, validate_dbt_model, analyze_dbt_error
│   ├── github_tools.py             # update_dbt_sources_yaml, create_dbt_pull_request
│   └── registration_tools.py       # register_transformation
├── prompts/
│   └── dbt_react_system_prompt.py  # Tool-aware system prompt
├── models.py                       # LLM model definitions (existing)
└── utils.py                        # Schema embedding only (pruned)
```

**Stage-to-tool mapping:**

| # | Old Stage | New Tool | Source Lines | External APIs | HITL |
|---|-----------|----------|-------------|---------------|------|
| 1 | `dbt_credentials_engine` | `validate_dbt_credentials` | `dbt.py:411-688` | Platform Core GraphQL, Secrets Manager | No |
| 2 | sources.yaml fetch | `fetch_dbt_sources` | `dbt.py:770-810` | GitHub API | No |
| 3 | `draft_sql_generation` | `generate_sql_model` | `dbt_agent.py:221-348` | Platform Core (schema), LLM (Sonnet) | No |
| 4 | `code_review` + `code_editing` | `review_sql_code` | `dbt_agent.py:351-546` | LLM (Haiku review) | No |
| 5 | `dbt_writer` | `convert_sql_to_dbt` | `dbt_agent.py:572-682` | LLM (Sonnet) | No |
| 6 | `dbt_validator` | `validate_dbt_model` | `dbt_agent.py:856-967` | dbt MCP Server | No |
| 7 | `dbt_code_review` | `analyze_dbt_error` | `dbt_agent.py:995-1096` | LLM (Haiku) | No |
| 8 | finalize + schema embed | `update_dbt_sources_yaml` | `dbt_agent.py:1099-1210` + `utils.py:44-202` | GitHub API, LLM | No |
| 9 | commit + PR | `create_dbt_pull_request` | `dbt.py:221-408` + `dbt.py:126-218` | GitHub (PyGithub), LLM | **Yes** |
| 10 | `register_transformation` | `register_transformation` | `dbt.py:1112-1301` | Platform Core GraphQL | No |

**Phased rollout with feature flag:**

- **Phase 0 (done):** Skeleton `dbt_agent_react.py` and `DbtReactState` in `state.py`. Compiles but has no tools. Toggle via `USE_DBT_REACT` env var in `deep_agent.py`.
- **Phase 1:** Extract stages 1-7 as tools. Write system prompt. Wire middleware. Unit test each tool.
- **Phase 2:** Extract stages 8-10 (GitHub + registration). Add `finalize_dbt_output` tool for backward-compat state fields. Integration test full pipeline.
- **Phase 3:** Flip `USE_DBT_REACT=true` as default. Delete old files (`dbt.py`, `dbt_github_utils.py`, old `dbt_agent.py`). Remove feature flag.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| Refactor in-place (keep StateGraph, clean up nodes) | Less risk, no pattern change | Still diverges from every other agent, no middleware, no tool reuse | Maintains the root cause of all problems |
| Hybrid (ReAct for SQL gen, StateGraph for commit) | Lower blast radius on HITL | Two patterns in one agent, complex routing | Adds complexity without solving the full problem |
| Full ReAct (recommended) | Consistent with all agents, full middleware, testable tools | Requires HITL pattern migration | HITL is well-documented in other agents, manageable risk |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| dbt Agent | `brightbot` | Rewrite: 10 new tool files, new system prompt, new state schema |
| Super Agent | `brightbot` | Modify: `deep_agent.py` swap workflow import (3 lines) |
| Constants | `brightbot` | Modify: add `NODE_TITLE.DBT_RESPONSE` |
| Tests | `brightbot` | Create: `tests/unit/agents/test_dbt_react_tools.py` |
| Old dbt files | `brightbot` | Delete: 3 files (~3,700 lines) in Phase 3 |

No changes to webapp, platform-core, or other repos. The supervisor routing, `CompiledSubAgent` registration, and HITL interrupt contract remain identical.

## Acceptance Criteria

- [ ] All 10 tools exist as standalone `@tool`-decorated functions returning `Command(update={...})`
- [ ] Each tool is independently unit-testable with mocked external dependencies
- [ ] `dbt_agent_react.py` uses `create_agent()` with standard middleware stack (OTel, limiters, streaming)
- [ ] `DbtReactState` extends `BBState` with working fields for tool state transfer
- [ ] System prompt documents all tools, workflow order, and iteration limits (max 3 validation retries, max 2 code review rounds)
- [ ] HITL interrupt for PR approval works identically to current behavior (same payload shape consumed by webapp)
- [ ] Backward-compatible state fields populated: `dbt_result`, `github_pr_url`, `platform_transformation_id`
- [ ] Feature flag `USE_DBT_REACT` toggles between old and new in `deep_agent.py`
- [ ] Unit tests pass: `uv run pytest tests/unit/agents/test_dbt_react_tools.py -v`
- [ ] Integration test passes: full dbt pipeline from user request to PR creation on staging
- [ ] Old files deleted after successful staging validation: `dbt.py`, `dbt_github_utils.py`, old `dbt_agent.py`
- [ ] Total new code < 1,000 lines (tools + agent + prompt + state)

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| BH-360 | dbt ReAct migration: Phase 0 scaffolding (agent skeleton, state schema, feature flag) | 2 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 1 credentials + source tools (`validate_dbt_credentials`, `fetch_dbt_sources`) | 3 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 1 SQL tools (`generate_sql_model`, `review_sql_code`) | 5 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 1 dbt tools (`convert_sql_to_dbt`, `validate_dbt_model`, `analyze_dbt_error`) | 5 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 1 system prompt + middleware wiring | 3 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 2 GitHub tools (`update_dbt_sources_yaml`, `create_dbt_pull_request` with HITL) | 5 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 2 registration tool + finalize output tool | 3 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 2 integration tests (full pipeline) | 3 | BH-172 |
| BH-TBD | dbt ReAct migration: Phase 3 switchover + old code deletion | 2 | BH-172 |
| **Total** | | **31** | |

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `create_agent()` + `ToolRuntime` API (LangChain/deepagents) | Blocking | Ready (used by all other agents) |
| dbt MCP Server (for `validate_dbt_model` tool) | Blocking | Ready (already used by old agent) |
| Platform Core GraphQL (credentials, registration) | Blocking | Ready (no changes needed) |
| GitHub App (PyGithub, OAuth tokens) | Blocking | Ready (no changes needed) |
| Webapp HITL interrupt handler | Non-blocking | Ready (must match existing payload contract) |
| `USE_DBT_REACT` feature flag in `deep_agent.py` | Blocking | Done (Phase 0) |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| HITL interrupt payload mismatch (webapp expects exact format) | Copy interrupt payload verbatim from `dbt.py:307-332`, verify with webapp team |
| LLM loops indefinitely without graph-enforced iteration limits | System prompt codifies max iterations + `create_tool_limiter()` middleware enforces hard cap |
| Backward state compatibility (supervisor reads `dbt_result`, `github_pr_url`) | `finalize_dbt_output` tool writes these fields via `Command(update={...})` |
| Async tool calls (validate_dbt_model calls async MCP server) | Define tool as `async def` -- ReAct agents support async tools natively |
| Feature flag toggle during migration | `USE_DBT_REACT` env var switches between old/new in `deep_agent.py`; both paths coexist until Phase 3 |
