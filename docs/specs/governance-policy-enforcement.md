---
title: "Governance & Quality Policy Enforcement — close the create→persist→apply→alert loop"
epic: "BH-172"
author: "drchinca"
status: "Draft"
created: "2026-06-24"
last_reviewed: "2026-06-24"
generates: "tickets"
tags: [governance, quality, policy, enforcement, brightbot, platform-core, great-expectations]
related:
  features: []
  pocs: []
  bedrock: []
---

# Governance & Quality Policy Enforcement

## Problem

**Policies are not applied.** Across BrightHive, governance policies and data-quality rules can be *created* and *stored* in Neo4j, but nothing *enforces* them. The Neo4j relationship is even named `GovernanceNode-[:ENFORCES]->CustomPolicyNode` — yet no code reads a policy and acts. A customer sees policies and "ACTIVE / apply-on-schedule" quality rules in the UI and reasonably believes governance is automatic. It is not: every protection is inert metadata until a human manually triggers a one-off run.

This spec is the umbrella for four confirmed holes (BH-766/767/768/769), all live-proven on staging on 2026-06-24.

## Use Case / Goal

A workspace's declared governance is actually in force:

- A custom policy ("FERPA review required before a dataset joins a project") **blocks or flags** the action it describes.
- A quality rule a user (or the agent) defines is **persisted** as a first-class rule, not lost to chat.
- An `ACTIVE` rule marked `applyOnSchedule` / `applyOnIngestion` **runs on that trigger** without a human clicking.
- A failing `ACTIVE` rule **emits a proactive alert** (BrightSignals/Slack), so silent data-quality regressions surface.

Success = the four scenarios below pass against a real workspace, and the `ENFORCES` relationship stops being aspirational.

## Current Situation

### How It Works Today

- **Custom policies**: created via the UI (`updateGovernance` mutation) → stored as `CustomPolicyNode` in Neo4j. Read by the agent (`getWorkspaceCustomPoliciesTool`) and counted by `analytics-resolver.ts` for a dashboard tile. That is the entire lifecycle.
- **Quality rules**: defined in the UI → `QualityRuleNode` (`createQualityRule` mutation, `CreateQualityRuleInput` at `platform-core schema.graphql:4202/4644`). The governance subagent (`brightbot/agents/governance_agent/`) can *profile* a dataset (`analyze_dataset_structure`) and *generate* Great Expectations recommendations (`generate_quality_expectations`), then runs saved rules on demand (`execute_library_quality_rules`, confirm-gated) — the only path that writes a `QualityRuleExecution` node back.
- The BH-503 spec (`quality-rules-configurable.md`) already designed the rule library + named `createQualityRule` and EventBridge scheduling. **This spec documents the gap between that design and what shipped.**

### Hard Limitations

- **No enforcement engine** in platform-core: `grep enforcePolicy|applyPolicy|checkPolicy|validateAgainstPolicy` → 0 matches.
- **No persist path from the agent**: brightbot never calls `createQualityRule` (only `create_quality_rule_execution_*`). The governance system prompt (`governance_system_prompt.py:116-118`) literally tells the user to save rules by hand in the UI.
- **No trigger reads `applyOnSchedule` / `applyOnIngestion`**: the flags are settable and stored, but nothing scheduled or ingestion-driven consumes them.
- **No alerting** on rule failure.

### Gaps (live evidence — staging workspace `1c7cb12e-6d1a-4922-98a8-cff4de70f24d`, "Brighthive Demo Environment", 2026-06-24)

| # | Ticket | Gap | Evidence |
|---|---|---|---|
| 1 | **BH-766** | Custom policies are inert prose — never enforced | 4 active policies (FERPA Review, PII Anonymization, Access, Retention) with zero enforcement code anywhere |
| 2 | **BH-767** | Agent generates quality expectations but cannot persist them | `createQualityRule` exists in platform-core but is never called from brightbot; prompt punts to UI |
| 3 | **BH-768** | `applyOnIngestion` / `applyOnSchedule` are decorative | Rule "staigng test 2" is ACTIVE + applyOnSchedule=true, yet its 10 executions are at irregular timestamps — a manual fingerprint, not a scheduler cadence |
| 4 | **BH-769** | Failing ACTIVE rules emit no alert | That same rule: all 10 executions `passed=false` (latest: 0/100 rows ok); no BrightSignals/Slack notification |

## Proposals / Solutions

### Recommended Approach

Close the loop in four independently-shippable slices, smallest-risk first:

1. **BH-767 (persist) — M, do first.** Add a feature-flagged, confirm-gated brightbot tool `persist_quality_rules` mapping generated `ChosenExpectationResponse` → `CreateQualityRuleInput` → `createQualityRule`. Update the governance prompt to offer saving *via the tool* instead of the UI. Lowest risk — the mutation already exists; this is wiring.
2. **BH-769 (alert) — M.** On any `ACTIVE` rule execution that fails at/above severity, emit a BrightSignals/Slack notification (respect `warningThreshold`). Reuses the existing execution-write path; couples to BH-409.
3. **BH-768 (auto-run) — L.** Build the trigger that reads `applyOnSchedule` (scheduled job) and `applyOnIngestion` (post-ingestion hook) and invokes the existing execution path. Likely lives in jobs-service / org-cdk (EventBridge), per the BH-503 design intent.
4. **BH-766 (policy enforcement) — L.** Make at least one policy category machine-enforceable (recommend the FERPA USE gate or ACCESS): a platform-core resolver seam that blocks/flags the described action and cites the policy. Free-text→executable NLP is out of scope.

Sequencing rationale: persist + alert are wiring on existing rails and deliver immediate value; auto-run and policy-enforcement are the genuine cross-repo engine work.

### Alternatives Considered

| Approach | Pros | Cons | Why Not |
|----------|------|------|---------|
| Big-bang enforcement engine (all 4 at once) | One coherent design | High risk, crosses 3 repos, long pole | Slice it — persist/alert ship this sprint, engine is its own effort |
| GE-native scheduling / suite persistence | Less custom code | Version-fragile, multi-tenant-hard (rejected in BH-503) | Keep GE stateless; store defs in Neo4j, schedule via EventBridge |
| NLP free-text policy → executable rule | Enforces existing prose policies as-is | Unbounded, unreliable | Out of scope; enforce typed/categorized policies first |

## Areas Involved

| Area | Repo | Impact |
|------|------|--------|
| BrightBot | `brightbot` | New `persist_quality_rules` tool (BH-767); failure→alert emit (BH-769); governance prompt update |
| Platform Core | `brighthive-platform-core` | Policy-enforcement resolver seam (BH-766); no new quality-rule mutation needed (exists) |
| Jobs / Org CDK | `brighthive-jobs` / `brighthive-data-organization-cdk` | EventBridge scheduler + ingestion hook reading the apply* flags (BH-768) |
| BrightSignals | `brightbot` / Slack server | Failure-notification surface (BH-769, via BH-409) |

## Acceptance Criteria

- [ ] **BH-767**: agent-generated expectations persist as `QualityRule` nodes (status DRAFT) via `createQualityRule`; appear in `qualityRules(workspaceId)`; confirm=false previews and writes nothing.
- [ ] **BH-769**: a failing ACTIVE rule of severity ERROR emits a proactive notification citing rule/asset/pass-rate; a passing rule emits nothing.
- [ ] **BH-768**: an ACTIVE `applyOnSchedule` rule executes automatically at a regular cadence with no manual trigger; an `applyOnIngestion` rule runs on new data.
- [ ] **BH-766**: an active USE/ACCESS policy blocks-or-flags its described action with the policy cited.
- [ ] The `ENFORCES` Neo4j relationship has at least one real consumer that acts on it.

## Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| `createQualityRule` mutation (platform-core) | Non-blocking | Ready (exists) |
| `execute_library_quality_rules` execution path | Non-blocking | Ready |
| BH-409 BrightSignals notification surface | Blocking (BH-769) | In progress |
| Scheduler home decision (jobs-service vs org-cdk EventBridge) | Blocking (BH-768) | Not started |
| Policy-category enforceability decision | Blocking (BH-766) | Not started |

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|--------|---------|--------|------|
| BH-767 | Persist agent-generated quality expectations via `createQualityRule` | 5 | BH-172 |
| BH-769 | Alert on failing ACTIVE quality rules (BrightSignals) | 3 | BH-173 |
| BH-768 | Honor `applyOnSchedule` / `applyOnIngestion` — auto-run trigger | 8 | BH-172 |
| BH-766 | Enforce custom governance policies (≥1 category gates its action) | 8 | BH-172 |

## Related

- **Spec**: `docs/specs/quality-rules-configurable.md` (BH-503) — designed the rule library + named `createQualityRule` and EventBridge scheduling this spec finds unshipped.
- **Epic**: BH-409 (BrightSignals) — the notification surface BH-769 plugs into.
