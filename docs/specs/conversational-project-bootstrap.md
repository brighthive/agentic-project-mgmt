---
title: "Conversational Project Bootstrap"
epic: "Project-2.0"
author: "platform-team"
status: "Approved"
created: "2026-09-15"
generates: "tickets"
tags:
  - projects
  - brightagent
  - project-spec
  - workflow-spec
related:
  features:
    - project-2-spec-driven-pipelines.md
---

# Conversational Project Bootstrap

> From workspace-level BrightAgent chat, a user describes a new data project in natural
> language. The agent drafts a project spec, matched catalog assets, optional schema files,
> and an optional pipeline preview — then creates the project after explicit confirmation.

## 1. Context

Project 2.0 adds spec documents and spec-driven pipelines inside an existing project.
Customers also want to **start** a project from a workspace conversation: goals, sources,
target schema, and pipeline intent captured in chat, materialized as a real project without
manual UI steps.

### Goal

User in **main BrightAgent** (no `project_id` in session) says: "Create a Student 360 project
using our SIS and LMS tables…" → agent previews name, spec markdown, linked assets, files,
schemas, optional pipeline → user confirms → platform creates project + spec + links +
optional applied WorkflowSpec.

### Gaps (before this spec)

- No MCP or deep_agent tool for `createProject`
- Project MCP tools require an existing `project_id`
- No orchestrated bootstrap (create → spec → assets → files → schemas → propose/apply)
- `apply_pipeline_from_spec` missing from brightbot MCP surface

## 2. Interface Contract

### BrightAgent deep_agent tool (workspace chat)

| Tool | Gate | Description |
|------|------|-------------|
| `create_project_from_conversation` | confirm | Draft + create project from `conversation_summary` |

Args:

- `conversation_summary` (required): concise recap of user goals, sources, outputs
- `confirm` (default false): preview vs execute
- `apply_pipeline` (default false): when `confirm=true`, also apply proposed pipeline steps

Rejected when `project_id` is set in session (project-scoped chat).

### MCP (brightbot)

| Tool | Scope | Description |
|------|-------|-------------|
| `create_project_from_conversation` | write + confirm | Same as deep_agent tool |
| `apply_pipeline_from_spec` | write + confirm | Apply preview steps to WorkflowSpec |

### GraphQL (platform-core — existing, orchestrated from brightbot)

- `createProject`
- `upsertProjectSpecDocument`
- `addDataAssetToProject`
- `onboardResource` (+ presigned PUT)
- `createTargetSchema`
- `proposePipelineFromSpec`
- `applyPipelineFromSpec`

No new platform-core mutations in P0 — brightbot orchestrates existing APIs.

## 3. Invariants (DbC)

1. Bootstrap runs only in **workspace** chat (`project_id` absent in session).
2. `confirm=false` performs **zero** mutations (LLM draft + asset matching only).
3. `confirm=true` requires explicit user approval in the same conversation turn sequence.
4. `apply_pipeline=true` only runs after project + primary spec exist; uses
   `proposePipelineFromSpec` then `applyPipelineFromSpec` — never auto-executes warehouse jobs.
5. `workspaceId` derived from authenticated session — never from model args.
6. Unmatched asset hints are listed in preview; linking skips unresolved refs (no silent wrong links).

## 4. Acceptance Criteria (Gherkin)

```gherkin
Feature: Conversational project bootstrap

  Scenario: Preview from workspace chat
    Given a workspace collaborator with no project_id in session
    When create_project_from_conversation is called with confirm false
    Then status is preview
    And the response includes project name, spec excerpt, matched assets
    And no project was created in Platform Core

  Scenario: Confirm creates project with spec
    Given a preview the user approved
    When create_project_from_conversation is called with confirm true
    Then a new project id is returned
    And getProjectSpec returns primary markdown matching the draft

  Scenario: Reject in project-scoped chat
    Given session_info includes project_id
    When create_project_from_conversation is called
    Then the tool returns an error directing the user to workspace chat

  Scenario: Optional pipeline apply
    Given confirm true and apply_pipeline true
    When bootstrap completes
    Then getWorkflowSpec returns steps matching the propose preview

Feature: MCP apply pipeline

  Scenario: Apply preview steps
    Given a project with a primary spec and a propose preview
    When apply_pipeline_from_spec is called with confirm true
    Then WorkflowSpec steps are persisted
```

## 5. Out of Scope

- Editing an existing project via conversation (use project-scoped spec/pipeline tools).
- Auto-execute compiled workflow without human review.
- Bulk project creation.

## 6. Areas Involved

| Repo | Files |
|------|-------|
| agentic-project-mgmt | this spec |
| brightbot | project_author, project_bootstrap, project_pipeline, MCP + deep_agent wiring |
| brighthive-platform-core | (no change P0) existing mutations |
| brighthive-webapp | (no change P0) user navigates to new project via returned id |
