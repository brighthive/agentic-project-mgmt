---
title: "Configurable Quality Agent — workspace rule library, curation, and history"
epic: "BH-503"
author: "drchinca"
status: "Draft"
created: "2026-05-16"
generates: "tickets"
tags: [quality, governance, great-expectations, brightbot, platform-core, webapp]
related:
  features: []
  pocs: []
  bedrock: []
---

# Configurable Quality Agent

## Problem

The webapp Quality Rules page (`src/Governance/pages/QualityRulesPage.tsx`) is mock data behind a `PreviewBanner`. There is no way for a workspace to declare which data-quality rules it cares about, edit thresholds, or see whether a rule passed over time.

The brightbot quality agent works, but it regenerates a fresh Great Expectations suite from an LLM on every run. Nothing a workspace "decides" survives between runs. For enterprise data-governance buyers, workspace-level rule control is table stakes — without it the page reads as a static demo.

## Use Case / Goal

A workspace admin opens the Quality Rules page, sees the rules that apply to their data, edits a threshold (e.g. completeness from 95 to 98 percent), activates or deactivates rules, clones from a template library, runs a check on demand, and watches the pass rate trend over time. Viewers and collaborators see the same rules read-only.

Success: the page renders live data, every rule shows a real pass rate and last-run from execution history, and the quality agent executes exactly the active rules a workspace chose — not LLM-regenerated ones.

## Current Situation

### How It Works Today

Quality lives in `brightbot/agents/governance_agent/tools/quality_tools.py` as three LangGraph tools:

1. `analyze_dataset_structure_tool` — samples 5000 rows from the warehouse, profiles columns.
2. `generate_quality_expectations_tool` — Claude proposes 10 to 25 GE expectations from the profile.
3. `run_quality_validation_tool` — builds a GE suite, runs it on the sample, formats a report.

Great Expectations 1.9 in **ephemeral** mode (`gx.get_context(mode="ephemeral")`, quality_tools.py:469). The suite is built programmatically:

- `generate_chosen_expectations_gx()` maps each `ChosenExpectation` pydantic model to a live GE object via `getattr(gxe, name)(**kwargs, meta=meta)` (expectation_mapped.py:555-557).
- `gx.ExpectationSuite(name=..., expectations=[...])` then `context.suites.add()` (quality_tools.py:476-479).
- `validation_definition.run(batch_parameters={"dataframe": df})` executes (line 500).
- `convert_gx_validation_result()` produces a dict with `statistics` plus a per-expectation `results` array (quality_utils.py:16-88).

Results persist as an `AgentCapabilityExecutionNode` in Neo4j (capabilityType `quality_check`, result is a JSON blob) plus artifact files in S3. Execution is on demand via `POST manage agents run` (graph_id `quality_check_agent`, 5-minute cooldown) and scheduled via EventBridge plus DynamoDB.

Nav visibility is governed by `src/routes/navAccess.ts` (added in BH-517): a `NAV_ACCESS` map of route `key` to allowed `WorkspaceRoleEnum[]`, consumed by `genNav.tsx` via `isNavAllowed(key, role)`. The `VITE_ROUTE_VISIBILITY_CONFIG` whitelist overrides it. Today `quality-rules` is visible to Admin, Collaborator, Viewer.

### Hard Limitations

- **Rules are ephemeral.** Every run produces a different LLM-generated suite. A workspace cannot pin "these are our rules".
- **No per-rule history.** Results are one JSON blob per run, so pass rate by rule over time is not queryable.
- **No CRUD surface.** Nothing lets the webapp create, edit, activate, or delete a rule.

### Gaps

- No persistent rule entity scoped to a workspace.
- No aggregation of pass rate or last-run per rule.
- No GraphQL types on platform-core for the webapp to consume.
- No template library to lower time-to-first-rule.
- No server-side enforcement distinguishing who can VIEW rules from who can MUTATE them. `navAccess.ts` hides tabs but is not security.

## Proposals / Solutions

### Recommended Approach

Persist rule definitions ourselves in Neo4j; use Great Expectations purely as a stateless execution engine.

**Key finding (validated against brightbot code):** GE 1.9 supports the full round-trip the design needs.

| Capability | Status | Evidence |
|---|---|---|
| Stable expectation name string | Supported | `expectation_name: Literal[*EXPECTATION_NAMES]` (expectation_mapped.py:75) |
| Params serialize to JSON | Supported | `suggested_parameters: dict[str, Any]` (line 81) |
| Suite built programmatically | Supported | `gx.ExpectationSuite(name, expectations=[...])` (quality_tools.py:476) |
| Reconstruct expectation from stored name plus params | Supported | `getattr(gxe, name)(**kwargs, meta=meta)` (expectation_mapped.py:555) |
| Per-expectation results for fanout | Supported | `for result in validation_result.results` (quality_utils.py:34) |
| Custom params: mostly, min_value, max_value, regex, type_list | Supported | passed through as `**kwargs` (line 69-70) |

**Architectural decision: GE is a stateless engine.** We do NOT use GE native suite persistence (GE Cloud or filestore), which is version-fragile. We store rule definitions (name plus params) as `QualityRuleNode` in Neo4j and rebuild an ephemeral GE suite on every run through the existing `_convert_expectation_to_gx` bridge. This makes BH-507 a low-risk change: feed the bridge our stored rules instead of LLM output.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| GE native suite persistence (filestore or Cloud) | GE-managed lifecycle | Version-fragile across GE releases, extra infra, harder multi-tenant isolation | Store definitions in Neo4j instead; GE stays stateless |
| Keep LLM regeneration, just cache last suite | Minimal change | Rules still not workspace-controlled, drift between runs | Defeats the goal of workspace configurability |
| Full-table validation against warehouse now | Trustworthy pass rate | Large scope, per-warehouse adapters, slow | Ship on sample first, label honestly, upgrade later |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| BrightBot | `brightbot` | New Neo4j nodes, REST CRUD, agent reads rules from library, per-rule execution fanout, template seed |
| Platform Core | `brighthive-platform-core` | GraphQL types and resolvers proxying brightbot REST |
| Web App | `brighthive-webapp` | Quality Rules page wired to live data, editor sheet, history drawer; depends on BH-517 navAccess |

## Interface Contract

### Neo4j nodes (brightbot)

`QualityRuleNode` — id, name, description, expectation_type (string matching GE name), expectation_params (JSON), target_asset_id, target_column (nullable), severity (critical | warning | info), status (draft | active | deprecated), workspace_id, created_at, updated_at, created_by.

`QualityRuleExecutionNode` — id, rule_id, run_id, evaluated_count, success_count, partial_unexpected_count, passed (bool), evaluated_at, sample_size.

`QualityRuleTemplateNode` (global, not workspace-scoped) — id, name, description, category, expectation_type, default_params (JSON), suggested_severity, tags.

Relationships: `(DataAsset)-[:HAS_QUALITY_RULE]->(QualityRuleNode)`; `(QualityRuleNode)-[:HAS_EXECUTION]->(QualityRuleExecutionNode)`; `(Workspace)-[:OWNS]->(QualityRuleNode)`.

### REST (brightbot)

```
GET    /workspace/{ws}/quality-rules          list, paginated, filter asset/severity/status
GET    /workspace/{ws}/quality-rules/{id}      single rule + embedded latest execution
POST   /workspace/{ws}/quality-rules           create from explicit params
POST   /workspace/{ws}/quality-rules/from-template/{templateId}   clone a template
PATCH  /workspace/{ws}/quality-rules/{id}      update params, severity, status
DELETE /workspace/{ws}/quality-rules/{id}      soft delete (status -> deprecated)
GET    /workspace/{ws}/quality-rules/{id}/history   paginated executions, date window
GET    /quality-rule-templates                 global catalog grouped by category
```

### GraphQL (platform-core)

Types: QualityRule, QualityRuleExecution, QualityRuleTemplate, enums QualityRuleSeverity and QualityRuleStatus. Queries: `workspace.qualityRules`, `qualityRule(id)`, `dataAsset.qualityRules`, `qualityRuleTemplates`. Mutations: createQualityRule, updateQualityRule, deleteQualityRule, cloneQualityRuleFromTemplate, runQualityCheck. `QualityRule.passRate` is a Float 0 to 100 for direct UI binding.

## Invariants

1. WHEN a rule is read, queried, or mutated, THE System SHALL scope it to the caller workspace_id; cross-workspace access SHALL return not-found.
2. Rule status transitions SHALL follow draft to active to deprecated. Reverse transitions SHALL require an explicit flag.
3. WHEN the agent runs against an asset, THE System SHALL execute only that asset active rules, never LLM-regenerated ones.
4. IF an asset has zero active rules, THE System SHALL return an explicit empty state and SHALL NOT regenerate rules silently.
5. A run evaluating N rules SHALL create exactly N QualityRuleExecutionNodes (no double counting, no blob).
6. Rule definitions are the source of truth; GE suites SHALL be reconstructed per run and SHALL NOT be persisted in GE.
7. Tab visibility (navAccess.ts) is presentation only. THE System SHALL enforce mutate permissions server-side independently of nav hiding.
8. WHERE role is Viewer or Collaborator, THE System SHALL allow read of rules but SHALL reject create, update, delete, and run with forbidden.
9. WHERE role is Admin, THE System SHALL allow all rule operations.
10. passRate SHALL be computed from QualityRuleExecutionNode history over a configurable window (default 30 days), never stored as a static field.
11. expectation_type SHALL be one of the GE expectation names enumerated in EXPECTATION_NAMES; unknown types SHALL be rejected at create time.
12. Cloning a template SHALL create a QualityRuleNode in draft status, never active.

## Acceptance Criteria

- [ ] Workspace admin can view, create, edit, activate, deactivate, and delete rules
- [ ] Viewer and Collaborator see rules read-only; mutate attempts return forbidden server-side
- [ ] Quality agent executes only active rules for the target asset
- [ ] Zero-active-rules path returns an empty state and suggests propose-from-profile
- [ ] Each rule shows real passRate and lastRun from execution history
- [ ] A run with N rules creates exactly N execution nodes
- [ ] At least 20 templates seeded across categories; clone creates a draft rule
- [ ] Webapp page renders live data, PreviewBanner removed
- [ ] Detail drawer shows a 30-day trend chart
- [ ] Multi-agent review (UX, sales-strategist, react-frontend-expert, brighthive-ux-voice) signed off

## Auth Model (explicit, since nav hiding is not security)

| Operation | Admin | Collaborator | Viewer | Enforced where |
|-----------|-------|--------------|--------|----------------|
| See Quality Rules tab | yes | yes | yes | navAccess.ts `quality-rules` (client hide) |
| Read / list rules | yes | yes | yes | brightbot REST + platform-core resolver |
| Create / edit / delete | yes | no | no | brightbot REST (server) |
| Activate / deactivate | yes | no | no | brightbot REST (server) |
| Run check now | yes | no | no | brightbot REST (server) |

navAccess.ts `quality-rules: [Admin, Collaborator, Viewer]` matches the read row. Mutations are NOT expressible in navAccess (it only hides tabs) and MUST be enforced in the REST handlers and GraphQL resolvers.

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| BH-517 navAccess.ts merged | Blocking for webapp ticket | In progress (harbour) |
| BH-376 nav restructure merged | Blocking for webapp ticket | In review (PR 1100) |
| brightbot OGM (BH-505) | Blocking for all backend | Not started |
| Great Expectations 1.9 round-trip | Validated | Confirmed in this spec |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| BH-504 | Spec (this doc) | 2 | BH-503 |
| BH-505 | QualityRuleNode + QualityRuleExecutionNode OGM | 3 | BH-503 |
| BH-506 | REST CRUD endpoints | 3 | BH-503 |
| BH-507 | Agent reads rules from library | 3 | BH-503 |
| BH-508 | Per-rule execution fanout + aggregation | 2 | BH-503 |
| BH-509 | platform-core GraphQL types + resolvers | 2 | BH-503 |
| BH-510 | webapp page wire-up + editor + history drawer | 3 | BH-503 |
| BH-511 | Seed library of 20+ templates | 2 | BH-503 |

## Related

- **Epic**: BH-503
- **Webapp parent**: BH-114 (Governance page lives here)
- **Alerts on failure**: BH-409 BrightSignals
- **Quality trends in analytics**: BH-359
