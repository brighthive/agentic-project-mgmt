---
title: "Project 2.0 — Spec-Driven Pipelines"
epic: "Project-2.0"
author: "platform-team"
status: "Approved"
created: "2026-09-11"
generates: "tickets"
tags:
  - projects
  - workflow-spec
  - brightagent
  - pipeline-visualization
related:
  features:
    - brightroutines-ai-authored-workflowspec.md
  pocs:
    - clients/trials/longaeva
---

# Project 2.0 — Spec-Driven Pipelines

> Replaces the legacy project workflow canvas. Projects are managed against markdown
> specification documents; BrightAgent reads the spec and authors a WorkflowSpec pipeline
> graph that humans inspect, edit, and execute.

## 1. Context

Data teams (Longaeva, Indiana Tech, Virginia, 360-view customers) want to manage data
pipelines against English specs — not hand-wire ETL columns or write dbt by default.
BrightHive already ships WorkflowSpec (compile/execute DAG) and a React Flow visualization
hidden behind the `Project Flow` feature flag. Project 2.0 promotes that path, adds a
first-class **Project Spec** document primitive, and exposes pipeline authoring to
BrightAgent via MCP.

### Use Case / Goal

A project owner writes a README-style spec ("Student 360: unify SIS + LMS records…").
BrightAgent reads it, proposes a pipeline graph (sources → transforms → tests → mart),
the user reviews the visualization, approves, and the platform executes via WorkflowSpec.
Unsupported capabilities (e.g. SQL Server without a connector) render as blocked nodes.

### How It Works Today

- **WorkflowSpec** — full GraphQL CRUD, compile, execute (`getWorkflowSpec`, `createWorkflowSpec`, …).
- **WorkflowSpecPage** — React Flow canvas for steps; hidden unless `Project Flow` is whitelisted.
- **Legacy `ProjectWorkflow`** — fixed-column ETL canvas; **deprecated, out of scope**.
- **Workspace context** — markdown `WorkspaceContextNode`; pattern for project spec docs.
- **platform-core `workflow/mcp-tools.ts`** — read/propose workflow spec (not wired to brightbot MCP yet).

### Hard Limitations

- WorkflowSpec compiler only validates SQL/AGENT/INGEST runtimes safely today (see BH-897).
- Agent-authored pipelines require human review before execute (non-negotiable).
- Verifier agents against spec are parallel work (brightbot); not blocking P0 UI/API.

### Gaps

- No `ProjectSpecDocument` storage or GraphQL surface.
- No pipeline **node catalog** with workspace capability gating.
- Project Flow tab whitelist-only; spec tab missing.
- BrightAgent lacks MCP tools for project spec + pipeline graph.

## 2. Interface Contract (MDE)

### GraphQL (platform-core)

```
Query getProjectSpec(input: ProjectSpecRefInput!): ProjectSpecOutput!
Query getPipelineNodeCatalog(input: PipelineNodeCatalogInput!): [PipelineNodeTypeOutput!]!

Mutation upsertProjectSpecDocument(input: UpsertProjectSpecDocumentInput!): ProjectSpecDocumentOutput!
Mutation deleteProjectSpecDocument(input: DeleteProjectSpecDocumentInput!): DeleteProjectSpecDocumentOutput!
```

`ProjectSpecRefInput`: `{ workspaceId: ID!, projectId: ID! }`

`UpsertProjectSpecDocumentInput`: `{ workspaceId, projectId, documentId?, title, slug, content, isPrimary }`

`ProjectSpecDocumentOutput`: `{ id, title, slug, content, isPrimary, sortOrder, createdAt, modifiedAt }`

`PipelineNodeTypeOutput`: `{ type, label, description, category, inputs, outputs, allowedConnections, requiredCapabilities, mappedRuntime, supported }`

### MCP (brightbot)

| Tool | Scope | Description |
|------|-------|-------------|
| `read_project_spec` | read | List spec documents for a project |
| `upsert_project_spec` | write + confirm | Create/update a spec document |
| `read_project_pipeline` | read | Read WorkflowSpec for project |
| `get_pipeline_node_catalog` | read | Available node types + support status |
| `propose_pipeline_from_spec` | write preview | Draft WorkflowSpec steps from spec text (returns preview, does not mutate) |

## 3. Invariants (DbC)

1. `workspaceId` on every mutation is validated against the caller's workspace membership — never trust client-supplied workspace alone.
2. A project has at most one `isPrimary: true` spec document; upsert clears primary on siblings when setting primary.
3. `slug` is unique per project (lowercase alphanumeric + hyphens).
4. Legacy `workflow` query and `ProjectWorkflow` canvas are not used by the webapp Project Flow tab.
5. `proposePipelineFromSpec` / `propose_pipeline_from_spec` never auto-executes; returns `status: preview` until a human confirms via `applyPipelineFromSpec` (or individual WorkflowSpec mutations).
6. Pipeline node catalog `supported: false` when required workspace capabilities are missing.

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Project specification documents

  Scenario: Create primary spec on new project
    Given a collaborator on workspace W and project P
    When they upsert a spec document with isPrimary true
    Then getProjectSpec returns one document with that content

  Scenario: Agent reads spec
    Given a project with a primary spec document
    When BrightAgent calls read_project_spec for P
    Then the response includes the markdown content

Feature: Pipeline visualization (WorkflowSpec only)

  Scenario: Project Flow tab shows WorkflowSpec canvas
    Given Project Flow is visible (default on)
    When the user opens project P workflow tab
    Then WorkflowSpecPage renders (not legacy canvas)

  Scenario: Empty project shows create-spec CTA
    Given project P has no WorkflowSpec
    When the user opens the workflow tab
    Then they see an empty state with create-workflow action

Feature: Pipeline node catalog

  Scenario: Unsupported connector flagged
    Given workspace W has no SQL Server ingestion source
    When get_pipeline_node_catalog is queried for W
    Then the source node for sql_server shows supported false

Feature: Agent pipeline proposal

  Scenario: Propose from spec returns preview
    Given a primary spec describing a two-source 360 mart
    When propose_pipeline_from_spec is called
    Then status is preview and steps array is non-empty
    And no WorkflowSpec mutation was applied

  Scenario: Apply preview to WorkflowSpec
    Given a preview with N steps from proposePipelineFromSpec
    When applyPipelineFromSpec is called with those steps
    Then getWorkflowSpec returns N steps with dependencies wired
    And compileWorkflow may run as part of apply
```

## 5. Out of Scope

- Legacy `ProjectWorkflow` canvas and `workflow()` query UI usage.
- Full verifier-agent loop against spec (brightbot follow-up).
- Multi-doc organizer UI beyond list + primary flag (P1).
- Auto-execute pipeline from agent without human approval.

## 6. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| WorkflowSpec API | Blocking | Done |
| WorkflowSpecPage UI | Blocking | Done |
| Workspace context pattern | Non-blocking | Done |
| BH-897 AI WorkflowSpec authoring | Done | Platform Core assembles spec + catalog context, delegates LLM authoring to BrightAgent (`POST /project/propose-pipeline-from-spec`), falls back to spec parser when agent seam unavailable. MCP `propose_pipeline_from_spec` calls Platform Core GraphQL for parity. |

## 10. Test Coverage Update

- platform-core: unit tests for `pipeline-node-catalog`, `project-spec-document` service
- brightbot: unit tests for MCP tools (mock Platform API)
- webapp: Spec tab generate/apply flow; Pipeline empty-state "Generate from spec"; codegen for project-spec GraphQL
- platform-core: `applyPipelineFromSpec` orchestration + unit tests

## Areas Involved

| Repo | Files |
|------|-------|
| agentic-project-mgmt | this spec |
| brighthive-platform-core | OGM, GraphQL, resolvers, catalog |
| brighthive-webapp | ProjectSpecPage, ProjectWorkflowPage, routes, flags |
| brightbot | mcp/tools/project_pipeline.py, platform queries |

## Related

- `brightroutines-ai-authored-workflowspec.md` — agent draft → validate → compile
- `brightroutines-execute-workflow-schedule.md` — schedule compiled specs
