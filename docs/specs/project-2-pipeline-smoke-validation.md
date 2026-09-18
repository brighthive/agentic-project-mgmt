# SPEC — Project 2.0 Pipeline Smoke Validation (Option A)

**Status:** Draft  
**Ticket:** Project 2 follow-up  
**Repos:** `brighthive-platform-core`, `brightbot`, `brighthive-webapp` (UI optional v1)

## 1. Problem

After applying a pipeline from a project spec, users discover SQL/runtime failures only when they click **Run** on the Pipeline tab. Common failures include unresolved `{{ inputs.* }}` placeholders, invalid join keys, and missing warehouse tables. These are fixable deterministically or via conversational clarification, but today there is no bounded validation step between **Apply** and **Run**.

## 2. Solution (Option A)

A project-scoped **`pipeline_verifier`** BrightAgent subagent that:

1. Compiles the applied `WorkflowSpec` and runs a **smoke validation** pass (bounded row probes, no mart overwrite).
2. Applies deterministic repairs where possible (bindings, join SQL — reuses existing enrichment/runtime fixes).
3. Proposes step SQL fixes via confirm-gated tools when the agent can infer a correction.
4. Asks the user in chat when the spec is ambiguous (missing join keys, wrong table names).

Human-initiated **Run** remains the only path that materializes full pipeline outputs.

## 3. Invariants

1. **Smoke ≠ Run** — smoke executes `SELECT … LIMIT N` probes (default N=5); never runs `CREATE OR REPLACE TABLE` / CTAS materialization.
2. **No silent production writes** — smoke validation creates a `WorkflowRun` tagged via `triggeredBy` prefix `smoke:` for audit; scheduler bridge is not notified.
3. **PAUSED workflows** — smoke validation is allowed when the project workflow is PAUSED; full Run still requires ACTIVE.
4. **Auth** — `validatePipelineSmoke` requires workspace `memberUpdate` (same as apply/run).
5. **Stop on first failure** — smoke run stops at the first failing step; downstream steps are SKIPPED.
6. **Non-SQL runtimes** — async/non-warehouse runtimes (DBT, Datapiary) return `SKIPPED` with reason in smoke results (v1).
7. **Spec author boundary** — `spec_author` edits spec prose; `pipeline_verifier` validates/fixes applied pipeline steps only.

## 4. Gherkin

```gherkin
Feature: Pipeline smoke validation

  Scenario: Happy path — all SQL steps probe successfully
    Given a project with a compiled WorkflowSpec and ACTIVE or PAUSED workflow
    When the user calls validatePipelineSmoke
    Then status is PASS
    And every SQL step result is SUCCESS
    And no mart tables are overwritten

  Scenario: Compile blockers prevent smoke
    Given a WorkflowSpec with compile BLOCKER issues
    When validatePipelineSmoke is called
    Then status is BLOCKED
    And no WorkflowRun is created

  Scenario: First failing step stops the run
    Given step 2 SQL references a non-existent column
    When validatePipelineSmoke is called
    Then status is FAIL
    And step 2 is FAILED
    And step 3 is SKIPPED

  Scenario: Verifier subagent routes from supervisor
    Given a project-scoped chat
    When the user says "verify the pipeline" or "smoke test the pipeline"
    Then the supervisor delegates to pipeline_verifier
    And the subagent calls validate_pipeline_smoke_tool

  Scenario: Step fix requires confirmation
    Given pipeline_verifier proposes a SQL fix
    When propose_pipeline_step_fix_tool is called with confirm=false
    Then status is preview and no mutation occurs
    When confirm=true
    Then upsertWorkflowStep persists the new sqlTemplate

  Scenario: Binding fix for mart output
    Given step 6 outputBindings point at a corrupt FQN
    When pipeline_verifier calls list_pipeline_catalog_assets_tool for the mart table
    And propose_pipeline_step_bindings_tool is called with confirm=true
    Then bindWorkflowStep persists the corrected output binding
    And compileWorkflow status is VALIDATED

  Scenario: Catalog columns drive SQL repair
    Given smoke fails on an unknown column
    When list_pipeline_catalog_assets_tool returns fields for the bound asset
    Then pipeline_verifier can propose SQL using real column names without a live warehouse query
```

## 5. API (platform-core)

```graphql
type PipelineSmokeStepResultOutput {
  stepId: ID!
  stepName: String!
  stepOrder: Int!
  status: String!
  errorMessage: String
  rowsProcessed: Int
}

type ValidatePipelineSmokeOutput {
  status: String!  # PASS | FAIL | BLOCKED
  runId: ID
  failedStepName: String
  blockerCount: Int!
  stepResults: [PipelineSmokeStepResultOutput!]!
}

mutation validatePipelineSmoke(input: ValidatePipelineSmokeInput!): ValidatePipelineSmokeOutput!
```

## 6. Brightbot tools

| Tool | Purpose |
|------|---------|
| `validate_pipeline_smoke_tool` | Calls `validatePipelineSmoke` |
| `list_pipeline_catalog_assets_tool` | Catalog assets + columns for binding/SQL repair (no live warehouse query) |
| `propose_pipeline_step_fix_tool` | Preview/apply SQL-only fix via `upsertWorkflowStep` |
| `propose_pipeline_step_config_tool` | Preview/apply full step config (SQL, dependsOn, node type, runtimeConfig, …) |
| `propose_pipeline_step_bindings_tool` | Preview/apply input/output bindings via `bindWorkflowStep` (auto-resolves assetId from FQN) |

All mutating tools are confirm-gated (`confirm=false` preview, `confirm=true` apply) and re-run `compileWorkflow` after apply.

## 7. Out of scope (v1)

- Auto-run smoke on every apply (optional bootstrap flag only).
- Gating Pipeline **Run** button on verified status (webapp may show status; hard gate deferred).
- Full DBT/Datapiary smoke execution.

## 8. PR split

| PR | Repo | ~lines |
|----|------|--------|
| 1 | platform-core | smoke engine + GraphQL |
| 2 | brightbot | pipeline_verifier subagent + tools |
| 3 | brightbot | bootstrap `validate_pipeline` flag |
| 4 | webapp | Verify button (optional) |
