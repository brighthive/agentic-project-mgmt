---
name: "Nestlé Global"
slug: "nestle"
stage: "trial"
champion: ""
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: ""
jira_epic: ""
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [nestle, global-expansion, six-week-trial, mcp]
---

# Nestlé Global trial room

Prepare a six-week trial that earns a decision to expand across Nestlé divisions.
The user identifies Nestlé as BrightHive's biggest client and requests a dedicated
room for this engagement. Global expansion is the stated objective; division scope,
acceptance criteria and rollout authorization still need joint agreement.

**Current phase:** trial preparation. **Target start:** November 15; January fallback.
The working years are November 2026 and January 2027, inferred from this session's
date. Confirm the year and fallback day before scheduling. Frontmatter dates stay
empty until a committed window exists. `status: active` tracks preparation work,
not a started trial or an approved global rollout.

## Start here

| Need | Record |
|---|---|
| Dates, weekly outcomes and readiness | [Six-week trial plan](trial-plan.md) |
| Business value and acceptance evidence | [Trial scorecard](scorecard.md) |
| Expansion across all agreed divisions | [Global rollout plan](global-rollout.md) |
| Decisions, blockers and authoritative sources | [Decisions and evidence](decisions-and-evidence.md) |

## First decisions

| Decision | Required answer | Accountable role to assign |
|---|---|---|
| Trial calendar | November 15 or January; dates and decision meeting | Joint sponsors |
| People | BrightHive account owner; Nestlé sponsor, champion and approver | Account owner |
| Pilot scope | Named division, region, business decision and data product | Nestlé champion |
| Success | Baselines, thresholds, measurement windows and signatories | Business owner |
| Access | Authorized workspace, systems, data classification and write scope | Technical/security owners |
| Delivery | Real alert destination, operator and escalation coverage | Operations owner |
| Coordination | Live Jira epic before Day 1 and GTM page reference | BrightHive delivery owner |

## Business outcomes to agree

Prioritize work that changes a decision: a trusted data product delivered by its
deadline, an actionable warning before a dependent process is affected, or a reviewed
repair with verified recovery. Measure elapsed time and human effort against the
agreed baseline. A message delivered, a passing unit test or a completed scheduler
invocation cannot alone establish these outcomes.

The five platform journeys are candidates for the Nestlé trial, not imported client
commitments. Choose the specific products and thresholds in the [scorecard](scorecard.md).
Longaeva's ingestion patterns and Loop Capital's SQL Server/Slack requirements do not
become Nestlé requirements without confirmation.

## Environment and commercial context

The April environment record associates Nestlé UAT with `ProdTestWorkspace` and Matt.
That is a historical pointer, not confirmation of this trial's environment or owner.
Validate the current workspace/account through the account registry before access or
provisioning. Keep `workspace_id` and `aws_account` empty until reconciled.

Nestlé previously requested a volume/cost matrix. The consolidated cost theme is
parked pending reconfirmation; its status must not be presented as a delivered feature.
The source register links the original ask and dependency chain. Confirm whether it
is a trial acceptance gate; if so, start collecting the required usage baseline early.

## Operating rhythm

Proposed: twice-weekly blocker review, weekly sponsor scorecard and a final joint
decision after six weeks. Assign owners and agree the cadence at kickoff. Every
status change needs a dated source; every failed criterion needs a next action.

For the next session, read this overview, the decision log and the scorecard first.
Refresh live state before claiming deployment or client acceptance. Store operational
evidence here; durable customer architecture belongs in `platform-saas-ai-context`.
