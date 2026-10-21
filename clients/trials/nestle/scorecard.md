---
name: "Nestlé trial scorecard"
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
tags: [nestle, acceptance, business-value]
---

# Nestlé trial scorecard

The proposed criteria below need Nestlé's agreement before Day 1. No criterion has
client acceptance evidence yet. For every selected row, record its named business
owner, baseline, numeric target, measurement window and evidence link. Unselected
criteria require an explicit scope decision rather than disappearing from the plan.

## Proposed acceptance criteria

| ID | Outcome and measurement to agree | Required evidence | Current status |
|---|---|---|---|
| N-01 | Trusted data product available by an agreed business deadline; compare cycle time and output accuracy with baseline | Specification, terminal run, reconciled outputs and business-owner acceptance | Scope/target unconfirmed |
| N-02 | Quality monitoring covers named critical assets and detects agreed anomalies within a target interval | Executable checks, real scheduled runs, measured detection and delivered actionable alert | Scope/target unconfirmed |
| N-03 | A representative failure is diagnosed and repaired within an agreed interval and approval policy | Evidence-backed diagnosis, reviewable change, independent approval, rerun and verified recovery | Scope/target unconfirmed |
| N-04 | Recurring work delivers the intended result reliably with reduced operator effort | Approved routine, repeated execution/delivery records, failure handling and measured human effort | Scope/target unconfirmed |
| N-05 | Governance enforces agreed access/write/classification rules | Allowed and denied operations, audit trail, classification evidence and human review where required | Scope/target unconfirmed |
| N-06 | Real usage and costs support an expansion decision | Measured volume and billing period, attributed/shared/unattributed costs, assumptions and reconciliation | Historical ask; reconfirm |
| N-07 | Business users can act on an alert without decoding implementation details | Delivered message, verified impact/context, named operator, useful action and response | Scope/target unconfirmed |
| N-08 | The chosen next division can operate within agreed reliability, capacity and support limits | Division access/isolation checks, workload evidence, runbook, support acceptance and rollback rehearsal | Scope/target unconfirmed |

## What a useful alert must answer

1. What changed, compared with which expectation, and when was it measured?
2. Which named data product and verified downstream decision/deadline are affected?
3. What is the severity basis, and is the work blocked, degraded or still usable?
4. Who owns the response, and what concrete action is recommended?
5. Where is the evidence, what remains uncertain, and what approval is required?

Mark unknown impact explicitly. Do not infer lost sales, affected plants or regulatory
exposure from a technical failure. A target lookup failure first requires access and
binding review; blind reruns do not restore coverage. Group unchanged observations
into one incident and report material changes or verified recovery. An approval
control must enforce authorization and record the decision and outcome.

## Evidence and scoring rules

Use `not_agreed`, `not_started`, `running`, `blocked`, `failed`, `passed` or
`accepted`. `passed` requires the agreed measurement and source evidence; `accepted`
also requires the named Nestlé signatory and date. Skipped or empty cases cannot pass.
The table currently uses descriptive scope status until the criteria are agreed.

For each run append: criterion ID, division, baseline/target, observed value, time
window, source link, result, signatory and next action. Currently there are no client
runs. BrightHive demo results and another client's acceptance are platform references
only. The October technical Slack receipt provides no N-07 acceptance evidence.

Shared platform requirements: [MCP pilot journeys](../../../docs/specs/mcp-pilot-journeys.md).
The stronger notification contract is proposed in [PM #202](https://github.com/brighthive/agentic-project-mgmt/pull/202);
the narrow target-guidance fix is proposed in [BrightBot #1131](https://github.com/brighthive/brightbot/pull/1131).
These references do not establish Nestlé rollout readiness.
