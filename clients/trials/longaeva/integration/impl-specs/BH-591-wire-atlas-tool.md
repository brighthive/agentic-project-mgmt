---
ticket: BH-591
title: "Wire scaffold_atlas_semantic_view_tool into dbt_agent + LLM enrichment prompt"
owner: "Marwan / Kuri"
estimated: "30 min wiring + 1d prompt iteration + tests = ~1.5 days"
depends_on: ["BH-531 (bb#489) on develop", "BH-590 on develop (for live introspection)"]
last_reviewed: "2026-06-05"
---

# BH-591 — paste-ready implementation spec

> **Goal**: make the orphaned Atlas YAML scaffold tool callable by the dbt
> ReAct agent, with system-prompt guidance steering the LLM to enrich
> `custom_instructions` and `verified_queries` after the deterministic
> scaffold returns.
>
> **Branch**: `marwan/BH-591/wire-atlas-into-dbt-agent` (or `kuri/...`) off
> **post-merge `develop`** (after bb#489 squashes).

## What's already there (verified)

- `brightbot/agents/dbt_agent/tools/atlas_semantic_view/__init__.py` exports `scaffold_atlas_semantic_view`, `ScaffoldResult`, `SilverSchema`, `SilverColumn`, `ATLAS_TARGET_REGISTRY`, `DEFAULT_AGGREGATIONS`, `SVW_NAME_PREFIX`.
- `brightbot/agents/dbt_agent/tools/atlas_semantic_view/langchain_tool.py` defines `@tool def scaffold_atlas_semantic_view_tool(input_json: str) -> str` (line 30-31). Already JSON-in / JSON-out, returns `{error: ...}` on failure.

**Conclusion**: the `@tool` already exists. BH-591 is wire-up + prompt, not new tool code.

## Diff 1 — `brightbot/agents/dbt_agent/tools/__init__.py`

Add the export so `dbt_agent_react.py` can import it from one place.

```python
# Add this import alongside the other tools imports (line ~52, alphabetical-ish):
from brightbot.agents.dbt_agent.tools.atlas_semantic_view.langchain_tool import (
    scaffold_atlas_semantic_view_tool,
)
```

If there's an explicit `__all__` at the bottom of the file, append `"scaffold_atlas_semantic_view_tool"` to it.

## Diff 2 — `brightbot/agents/dbt_agent/dbt_agent_react.py`

Two edits.

### Edit 2a — add to the import block (line 107-130)

```python
from brightbot.agents.dbt_agent.tools import (
    analyze_dbt_error,
    analyze_model_impact,
    convert_sql_to_dbt,
    explore_dbt_project,
    fetch_dbt_sources,
    generate_sql_model,
    get_job_run_error,
    github_commit_file,
    github_commit_multiple_files,
    github_create_branch,
    github_create_pull_request,
    github_list_branches,
    github_list_files,
    github_merge_pull_request,
    preview_transformation_sample,
    github_read_file,
    list_jobs,
    register_transformation,
    review_sql_code,
    run_dbt_cloud_command,
+   scaffold_atlas_semantic_view_tool,
    search_available_tools,
    validate_dbt_refs,
)
```

### Edit 2b — add to `DBT_REACT_TOOLS` list (line 132-165)

Place under "Sources & LLM-powered SQL/dbt generation" group, since it's a generation tool:

```python
DBT_REACT_TOOLS: list = [
    # Tool search
    search_available_tools,
    # Project exploration
    explore_dbt_project,
    # Sources & LLM-powered SQL/dbt generation
    fetch_dbt_sources,
    generate_sql_model,
    review_sql_code,
    convert_sql_to_dbt,
+   scaffold_atlas_semantic_view_tool,
    analyze_dbt_error,
    # ...rest unchanged
]
```

### Edit 2c — pin it (line 190-229)

Atlas scaffolding is a one-shot per task, NOT every turn. Per the pinning criteria in the file ("≥75% of dbt runs" or "called in first 3 turns"), it's deferred — **do not pin**. Leave `_DBT_PINNED_TOOLS` unchanged. The model will discover it via `search_available_tools` when the user asks for semantic-view scaffolding.

> **Optional pin if Marwan disagrees**: Atlas scaffolding is a Day-6-8 trial centerpiece — pinning saves a tool_search round-trip on the demo. If pinned, add `"scaffold_atlas_semantic_view_tool"` to `_DBT_PINNED_TOOLS`. Default: keep deferred (LLM-eng review on the multi-agent assessment said don't pin until token-cost data exists).

## Diff 3 — `brightbot/agents/dbt_agent/prompts/dbt_react_system_prompt.py`

Add a new section AFTER `## Scope guardrails — what is and isn't your job` (line 109) and BEFORE `## Your toolset` (line 137).

```python
## Snowflake semantic-view enrollment (Atlas YAML)

When the user asks to **enroll a Silver table as a semantic view**, **scaffold
an Atlas YAML**, or **build a semantic view from a Silver table**, the workflow
is:

1. **Introspect the Silver table.** Use the warehouse-introspection path to
   pull the columns, data types, primary key, and (if the workspace exposes
   them) sample values. Pass this to the scaffold tool as `silver_schema`.

2. **Call `scaffold_atlas_semantic_view_tool`.** The tool is **deterministic**
   — it produces the YAML skeleton with all required Atlas blocks
   (`name`, `description`, `tables`, `atlas` top-level, field-level
   `atlas.target` bindings, `atlas.metric.aggregations` defaults). It does
   **NOT** populate `custom_instructions` or `verified_queries` — that is
   YOUR job (the LLM enrichment step below).

3. **Read the scaffold report.** The tool returns a `ScaffoldReport` with two
   lists: `grounded` (fields backed by catalog data) and `guesses` (fields
   the tool inferred and want human review). Surface the `guesses` list to
   the user so they can sanity-check before commit.

4. **Enrich `custom_instructions` (LLM-only — you write this).** Add UPPERCASE
   section headers followed by rules. Required sections per the Atlas
   contract:
   - **GRAIN** — when multiple grains coexist in one table, the WHERE rules
     to filter to one grain
   - **CHANNEL / PLATFORM / GEOGRAPHY** — anti-double-count rules across
     rollup dimensions
   - **PERIODS** — supported `PERIOD_TYPE` values, weekly-boundary caveats
   - **MEASURES / METRICS** — which facts are additive vs pre-computed
   - **STANDARD QUERY** — recommended `WHERE` predicate template (single-table
     views) OR **TABLE SELECTION** (multi-table views — explain when to use
     which table)

5. **Enrich `verified_queries[]` (LLM-only — you write this).** At least one
   `verified_query` per major use-case implied by the user's description.
   SQL must use Snowflake's native `SEMANTIC_VIEW(...)` syntax with three
   sections: `DIMENSIONS <table>.<dim>, ...`, `FACTS <table>.<fact>, ...`,
   and optional `METRICS`. Every column reference is **table-qualified**
   (`UNIFIED_SPEND.PERIOD_START_DATE`) — this works for both single- and
   multi-table views.

6. **Validate the verified_query.** Once the validation harness lands
   (BH-596), call it; until then, hand the YAML to the user with a "verify
   in Snowflake before commit" flag.

7. **Commit + PR.** Write the YAML to `models/semantic/<svw_name>.yml` (or
   wherever the project's semantic views live — confirm via
   `explore_dbt_project`). Use the standard commit + PR flow.

### Atlas vocabulary you MUST stay inside

Field-level `atlas.target` values must come from the registry. Common targets:
- `entity_name` — primary entity column
- `bloomberg_ticker`, `lngv_issuer_id` — issuer identifiers (Longaeva)
- `period_type`, `period_start_date`, `period_end_date`, `data_knowledge_ts`
- `metric_attributes.geography.region`, `metric_attributes.dataset_attributes.app_id`, etc. (dotted-namespace, supports nesting)

If you find yourself wanting to use a target name not in this list, the
correct action is to **bind the field WITHOUT an atlas.target** (let the
deterministic tool's default handle it) rather than invent a target. Hallucinated
targets fail the grounding validator (BH-596) and break the Atlas SDK.

### What you must NOT do

- **Never emit `CREATE SEMANTIC VIEW` DDL.** The Atlas SDK strips `atlas.*`
  keys and owns DDL. You emit YAML only.
- **Never invent `sample_values`.** They must come from `SELECT DISTINCT col
  LIMIT N` against the actual Silver table — if you don't have them, leave
  the field empty and flag for human review.
- **Never invent column names** in `expr:` fields. They must reference real
  introspected columns.
```

## Diff 4 — tests

New file: `tests/unit/agents/dbt_agent/test_atlas_tool_wired.py`

```python
"""BH-591 — verify scaffold_atlas_semantic_view_tool is registered in the dbt ReAct agent."""

from brightbot.agents.dbt_agent.dbt_agent_react import DBT_REACT_TOOLS
from brightbot.agents.dbt_agent.tools import scaffold_atlas_semantic_view_tool


def test_atlas_tool_in_react_tool_list() -> None:
    """The scaffold tool must be in DBT_REACT_TOOLS so the agent can call it."""
    tool_names = [t.name for t in DBT_REACT_TOOLS]
    assert "scaffold_atlas_semantic_view_tool" in tool_names


def test_atlas_tool_importable_from_package() -> None:
    """The tool must be exported from brightbot.agents.dbt_agent.tools."""
    assert scaffold_atlas_semantic_view_tool is not None
    assert callable(scaffold_atlas_semantic_view_tool)
```

Existing tests at `tests/unit/test_atlas_semantic_view_scaffold.py` (35 tests) cover the scaffold function itself — no changes needed.

## Acceptance criteria (Gherkin)

```gherkin
Feature: Atlas scaffold tool wired into dbt_agent

  Scenario: Tool registered in agent
    Given the dbt ReAct agent is initialised
    Then DBT_REACT_TOOLS contains scaffold_atlas_semantic_view_tool

  Scenario: Agent calls the tool when asked to scaffold a semantic view
    Given a workspace pointed at LONGAEVA_POC
    And the agent has access to int_enriched_holdings's schema
    When the user asks "scaffold a semantic view for int_enriched_holdings"
    Then the agent invokes scaffold_atlas_semantic_view_tool
    And the YAML returned contains `name`, `tables`, `atlas` top-level blocks
    And the LLM populates `custom_instructions` with at least one UPPERCASE section header
    And the LLM emits at least one `verified_query` using SEMANTIC_VIEW(...) syntax
    And the scaffold report's `guesses` list is surfaced to the user
```

## Multi-agent review chain (per global rules)

Before opening PR:
1. solutions-architect — confirms wire-up doesn't break the ReAct loop
2. senior-python — reviews the prompt section for LLM steerability
3. qa-agent — confirms test coverage adequate; flags need for BH-596 validator
4. junior-developer — fresh-eyes pass on prompt clarity

## Out of scope (separate tickets)

- Hallucination guardrails: BH-596 (vocabulary validator + verified_query compile harness)
- E2E demo: BH-597 (full 6-step DAG eval)
- LLM-evaluation rubric for `custom_instructions` quality: rolls into BH-597

## Effort breakdown

| Phase | Hours |
|---|---|
| Diffs 1-3 (wiring + prompt) | 1 |
| Diff 4 (tests) | 0.5 |
| Multi-agent review iterations | 2-3 |
| Manual validation against bb#489 sandbox tests | 1 |
| Prompt iteration with Marwan + 1-2 dry runs against `LONGAEVA_POC` | 4-6 |
| **Total** | **~1.5 days** |
