---
title: "Tenant-scoped dbt Cloud project listing + reliable project↔service↔repo linkage"
epic: "BH-1323"
author: "drchinca"
status: "Draft"
created: "2026-07-31"
generates: "tickets"
tags: [dbt, transformation, multi-tenant, platform-core, engineering-agent]
related:
  features: []
  pocs: []
  bedrock: []
---

# Tenant-scoped dbt Cloud project listing + reliable project↔service↔repo linkage

> Full contract: `~/.claude/rules/spec-driven.md`. Reference architecture (verified live
> 2026-07-31): `platform-saas-ai-context/docs/architecture/DBT_CLOUD_ACCOUNT_AND_PROJECT_LINKS.md`.

## 1. Context

BrightHive runs a **single shared dbt Cloud account** (`26133`). To let a user point the
engineering agent at "a project" and run a simple transformation, three boundaries have to be
trustworthy: listing the tenant's dbt Cloud projects, creating a BrightHive `Project`, and
binding that project to a transformation service + repo. All three are currently unreliable —
proven live on the Loop Capital staging workspace.

### Use Case / Goal

A data lead opens a workspace, sees **only their own** dbt Cloud projects, creates a BrightHive
project, links it to a transformation service + GitHub repo, and the engineering agent runs a
transformation against it — with every step's success verifiable from the API response.

### How It Works Today

- `getDbtJobs(transformationServiceId, workspaceId)` calls the shared account credential and
  returns **every job in the account** — including other tenants' projects
  (Cooperators, Indiana Tech, CCGEF observed in Loop Capital's response).
- `createProject` writes a bare `ProjectNode`; live it returned `null` for `success`/`projectId`
  while only 1 of 3 calls persisted (workspace count 12→13).
- `updateProject` stamps the `transformationServiceId`/`gitRepoUrl` **scalars** but writes no
  `CONFIGURES` graph edge; `addGitHubRepo` creates the `HAS_REPO` edge separately.
- The engineering agent resolves the dbt Cloud `project_id` from the linked repo URL
  (`brightbot/agents/dbt_agent/tools/credentials_tools.py:277`), never from a `ProjectNode`.

### Hard Limitations

- No tenant boundary at the dbt Cloud layer — isolation is naming-convention only. A UI listing
  `getDbtJobs` output leaks cross-tenant project names.
- `createProject`'s return payload can't be trusted; callers must re-list to know what landed.
- A project's `transformationService` relationship is not queryable — `ProjectOutput` exposes
  only the scalar, so the missing `CONFIGURES` edge is invisible through GraphQL.

### Gaps

- Tenant filter on dbt Cloud project/job listing.
- Deterministic `createProject` result (populated `success`/`projectId`, atomic persist).
- A single mutation (or documented sequence) that leaves a project fully bound: service scalar +
  `CONFIGURES` edge + `HAS_REPO` repo edge, all consistent.
- A `ProjectOutput.transformationService` relationship field so binding is verifiable.

## 2. Interface Contract (MDE)

```graphql
# Tenant-scoped listing — filters the shared account to this workspace's projects
getDbtProjects(transformationServiceId: ID!, workspaceId: ID!): [DbtCloudProjectOutput!]!
# DbtCloudProjectOutput { id: ID!, name: String!, ownedByWorkspace: Boolean! }

# getDbtJobs gains a tenant filter (default true = only this workspace's projects)
getDbtJobs(
  transformationServiceId: ID!, workspaceId: ID!, ownedOnly: Boolean = true
): [DbtCloudJobOutput!]!

# createProject returns a populated, reliable result (never null on success)
createProject(input: CreateProjectInput!): CreateProjectOutput!
#   CreateProjectOutput { success: Boolean!, projectId: ID! }   # both always non-null on 2xx

# One call binds a project end-to-end: service scalar + CONFIGURES edge + repo HAS_REPO edge
linkProjectTransformation(input: LinkProjectTransformationInput!): ProjectOutput!
#   LinkProjectTransformationInput {
#     workspaceId: ID!, projectId: ID!, transformationServiceId: ID!, repoUrl: String!, branch: String
#   }

# ProjectOutput exposes the relationship, not just the scalar
type ProjectOutput {
  id: ID!
  transformationServiceId: String        # scalar (existing)
  transformationService: TransformationServiceOutput   # NEW — resolves the CONFIGURES edge
  gitRepoUrl: String
}
```

## 3. Invariants (DbC)

```
WHEN getDbtProjects/getDbtJobs is called with ownedOnly=true, THE System SHALL return only
  projects whose naming/ownership resolves to the given workspaceId — never another tenant's.
WHEN createProject returns success=true, THE System SHALL return a non-null projectId that
  resolves to a persisted ProjectNode in the workspace.
IF createProject cannot persist, THEN THE System SHALL return success=false (never null on 2xx).
WHEN linkProjectTransformation succeeds, THE System SHALL have written ALL THREE of: the
  transformationServiceId scalar, the CONFIGURES edge, and the repo HAS_REPO edge — atomically.
IF ProjectOutput.transformationServiceId is set, THEN ProjectOutput.transformationService
  SHALL resolve to the same service (scalar and edge never disagree).
```

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Tenant-scoped dbt project listing + reliable project linkage

  Scenario: Listing shows only the tenant's projects
    Given a workspace on the shared dbt Cloud account
    When I call getDbtProjects for that workspace
    Then I see only projects owned by that workspace
    And no other tenant's project name appears

  Scenario: createProject result is trustworthy
    Given a workspace
    When I call createProject with a name
    Then success is true and projectId is non-null
    And re-listing the workspace shows exactly that new project

  Scenario: Linking binds a project end-to-end
    Given a bare project and a transformation service with a repo URL
    When I call linkProjectTransformation
    Then ProjectOutput.transformationService resolves to that service
    And ProjectOutput.gitRepoUrl equals the repo URL
    And a CONFIGURES edge exists from the project to the service

  Scenario: Engineering agent runs against a linked project
    Given a project bound via linkProjectTransformation
    When the engineering agent is pointed at that project
    Then it resolves the dbt Cloud project_id from the linked repo and runs

  Scenario: Agent errors clearly on an unlinked project
    Given a bare project with no linked repo
    When the engineering agent is pointed at it
    Then it returns a typed "no repo linked — add one in Settings > Transformations" error
```

## 5. Out of Scope

- Auto-provisioning new dbt Cloud projects/jobs (that's BH-332 — the agent triggers EXISTING jobs).
- Migrating to per-tenant dbt Cloud accounts (hard isolation) — a separate infra decision.
- The webapp Settings > Transformations UI (BH-1244 owns the surface; this spec owns the backend contract).

## 6. Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `addGitHubRepo` mutation (HAS_REPO edge) | Non-blocking | Ready |
| BH-1244 (webapp project↔repo linkage UI) | Non-blocking | In progress |
| dbt Cloud Admin API project ownership signal | Blocking (for `ownedOnly`) | Needs spike — no native tenant field; resolve via naming convention |

## 7. Correctness Properties

### Property 1: No cross-tenant leakage

*For any* `getDbtProjects`/`getDbtJobs` call with `ownedOnly=true`, every returned project
resolves to the calling `workspaceId`.

**Validates: §3 Invariant 1, §4 Scenario "Listing shows only the tenant's projects"**

### Property 2: Binding consistency

*For any* project where the `transformationServiceId` scalar is set, the `CONFIGURES` edge and
`transformationService` relationship resolve to the same service.

**Validates: §3 Invariant 4 & 5, §4 Scenario "Linking binds a project end-to-end"**

## 8. Eval Criteria

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| ProjectRunReadiness | dbt_initialise | GATE | resolves repo→project_id on a linked project, errors typed on unlinked | deterministic |

## 9. Observability Contract

- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=dbt_transformation`
- **Attributes**: `workspace.id`, `transformation_service.id`, `dbt.project_id`, `dbt.repo_url`
- **Log events**: `dbt_project.listed`, `project.created`, `project.linked`, `project.link_failed`, `dbt.run_no_repo`
- **Metrics**: none

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brighthive-platform-core` | `brighthive-platform-core/tests/` | One test per §2 entry: `getDbtProjects` tenant filter, `getDbtJobs ownedOnly`, `createProject` non-null result, `linkProjectTransformation` writes all three, `ProjectOutput.transformationService` resolves; one per §3 invariant observable via the API |
| `brightbot` | `brightbot/tests/` + `brightbot/brightbot/evals/` | L0: dbt agent reads a linked project's repo→project_id; L1: agent routes to a typed error on an unlinked project; L2 (real-behavior): agent resolves + triggers an existing job against a genuinely linked staging project |
| `brighthive-e2e` | `brighthive-e2e/e2e/` | One feature test: create → link → agent runs, end-to-end against live staging; one error-path test: agent on an unlinked project returns the typed error |

**Real-behavior requirement** (`~/.claude/rules/test-behavior-real.md`): the platform-core
`linkProjectTransformation` test hits the real Neo4j (asserts the `CONFIGURES` edge exists via a
Cypher read-back, not a scalar); the brightbot L2 hits the real dbt Cloud account credential.

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| Platform Core | `brighthive-platform-core` | New `getDbtProjects`, `ownedOnly` filter, reliable `createProject`, `linkProjectTransformation`, `ProjectOutput.transformationService` |
| BrightBot | `brightbot` | dbt agent typed-error on unlinked project; run against linked project |
| Web App | `brighthive-webapp` | (BH-1244) consumes the new listing + link mutation |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| — | `getDbtProjects` + `getDbtJobs ownedOnly` tenant filter (resolve ownership via naming convention) | 5 | BH-1323 |
| — | Make `createProject` return non-null `success`/`projectId`; atomic persist | 2 | BH-1323 |
| — | `linkProjectTransformation` — one mutation writes scalar + `CONFIGURES` edge + repo edge atomically | 3 | BH-1323 |
| — | `ProjectOutput.transformationService` relationship resolver | 2 | BH-1323 |
| — | dbt agent typed "no repo linked" error + run-readiness eval | 2 | BH-1323 |
| — | e2e: create→link→run happy path + unlinked error path on live staging | 3 | BH-1323 |

## Related

- **Reference architecture**: `platform-saas-ai-context/docs/architecture/DBT_CLOUD_ACCOUNT_AND_PROJECT_LINKS.md`
- **Data model / execution**: `platform-saas-ai-context/docs/architecture/DBT_TRANSFORMATION_ARCHITECTURE.md`
- **Debugging checklist**: `platform-saas-ai-context/docs/architecture/DBT_CLOUD_LEARNINGS.md`
- **Related ticket**: BH-1244 (webapp project↔repo linkage UI)
