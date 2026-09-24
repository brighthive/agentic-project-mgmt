---
title: "Project 2.0 — dbt Engineering Pipeline"
epic: "Project-2.0"
author: "platform-team"
status: "Approved"
created: "2026-09-24"
generates: "tickets"
tags:
  - projects
  - workflow-spec
  - dbt
  - pipeline
related:
  features:
    - project-2-spec-driven-pipelines.md
---

# Project 2.0 — dbt Engineering Pipeline

> Additive expansion of WorkflowSpec pipelines for complicated dbt workflows.
> SQL-first propose/apply/compile/run behavior is unchanged unless the workspace
> explicitly disables `Pipeline DBT Engineering` via runtime feature flags.

## 1. Context

Project 2.0 ships SQL-first spec-driven pipelines. Complicated dbt engineering
(medallion layers, selectors, dbt Cloud runs) requires stage-level orchestration
nodes, selector-scoped job triggers, and manifest/run-result sync — without
replacing the existing SQL path.

## 2. Invariants

1. When `Pipeline DBT Engineering` is disabled via runtime feature flags, behavior matches pre-change SQL-only pipelines.
2. When enabled (default), existing SQL node types and propose logic remain valid for specs without dbt signals.
3. dbt stage nodes require `transformationServiceId` and (`selector` or `stepsOverride`) plus a base `jobId` for dbt Cloud trigger API.
4. DBT runtime steps compile only when runtime config passes validation; adapter polling is used (not UNPOLLABLE blanket BLOCKER).
5. Manifest/run-result sync is post-run only and never blocks SQL execution.

## 3. Node types (additive)

| type | runtime | purpose |
|------|---------|---------|
| `dbt_build` | DBT | `dbt build` for a selector |
| `dbt_stage` | DBT | medallion layer (`tag:bronze`, etc.) |
| `dbt_test_gate` | DBT | dbt tests gate downstream steps |
| `dbt_snapshot` | DBT | snapshot maintenance |

Legacy `dbt_transform` / `dbt_test` unchanged.

## 4. Feature flag

Route name: `Pipeline DBT Engineering`. **Enabled by default** — off only when listed in `disabledRoutes` (global or workspace).

## 5. Gherkin

```gherkin
Scenario: SQL pipeline unchanged when flag disabled
  Given runtime feature flags disable "Pipeline DBT Engineering"
  When the user proposes a pipeline from a SQL spec
  Then all transform steps use sql_transform

Scenario: dbt stage pipeline when spec signals dbt
  Given "Pipeline DBT Engineering" is enabled
  And the project spec mentions medallion layers without inline SQL
  When the user proposes a pipeline from spec
  Then transform steps use dbt_stage with selector bindings

Scenario: dbt step compiles with selector config
  Given a WorkflowSpec step with runtime DBT and selector "tag:gold"
  When compileWorkflow runs
  Then no POLICY BLOCKER is emitted for DBT polling
```
