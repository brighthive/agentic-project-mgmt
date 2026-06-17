# Clients — Navigation Contract

> Operational tracking for leads, active trials, and paying customers.
> For client **architecture profiles** (stack, capability maps, integration patterns),
> see `../platform-saas-ai-context/clients/`.

---

## Quick Answer Table

| Question | Location |
|---|---|
| All leads, trials, and active clients | `README.md` |
| Start a new lead | `_templates/LEAD.md` |
| Start a new trial / POC | `_templates/TRIAL.md` |
| Active paying customer profile | `_templates/CLIENT.md` |
| Longaeva POC overview | `trials/longaeva/overview.md` |
| Longaeva milestone scorecard | `trials/longaeva/scorecard.md` |
| Longaeva UAT success guide (whole-company testing) | `trials/longaeva/UAT_GUIDE.md` |
| Longaeva — Sarah's Monday morning (non-tech sales demo) | `trials/longaeva/SARAH_DEMO.md` |
| Longaeva Snowflake standards | `trials/longaeva/SNOWFLAKE_STANDARDS.md` |
| Longaeva full POC response plan | `trials/longaeva/artifacts/poc-response-plan.md` |
| Longaeva client POC scope (verbatim) | `trials/longaeva/artifacts/poc-scope-from-client.md` |
| Longaeva Atlas semantic-view YAML examples (client-provided) | `trials/longaeva/artifacts/atlas-semantic-view-examples.yaml` |
| Longaeva Atlas YAML contract (distilled spec) | `trials/longaeva/artifacts/atlas-semantic-view-spec.md` |
| Longaeva Snowflake sandbox (DX README) | `trials/longaeva/sandbox/README.md` |
| Longaeva sandbox architecture diagrams | `trials/longaeva/sandbox/ARCHITECTURE.md` |
| Longaeva sandbox fidelity tracker | `trials/longaeva/sandbox/FIDELITY.md` |
| Longaeva PoC use-case validator | `trials/longaeva/sandbox/validate_poc.sh` (11/11) |
| Longaeva BrightHive gap analysis | `trials/longaeva/BRIGHTHIVE_GAPS.md` |
| Longaeva tech stack | `../platform-saas-ai-context/clients/longaeva/stack.md` |
| Longaeva capability map | `../platform-saas-ai-context/clients/longaeva/capability-map.md` |

---

## Lifecycle: lead → trial → active

```
leads/{slug}/          ← discovery, qualification, first calls
      ↓ (trial starts)
trials/{slug}/         ← POC execution, scorecard, milestone tracking
      ↓ (won)
active/{slug}/         ← paying customer, expansion, escalations
```

Move the folder when the stage changes — do not duplicate.
Rename the slug only if it was wrong; stability matters for git history.

---

## Dual-repo split

| This repo (agentic-project-mgmt) | platform-saas-ai-context/clients/ |
|---|---|
| POC plans, contacts, success criteria | Client tech stack + data architecture |
| Milestone scorecards, blockers | Capability map (requirements → BH features) |
| Trial artifacts (proposals, redlines) | Feature coverage honesty layer |
| Active customer operational notes | Integration pattern reference |
| Changes weekly | Changes quarterly |

**Rule**: if it would go stale in a sprint, it lives here. If it describes
how their system is built, it lives in platform-saas-ai-context.

---

## Frontmatter required on all content files

```yaml
---
name: ""
slug: ""
stage: "lead | trial | active"
champion: ""
champion_email: ""
trial_start: ""        # YYYY-MM-DD
trial_end: ""          # YYYY-MM-DD
decision_date: ""      # YYYY-MM-DD
jira_epic: ""          # BH-XXX — required before trial Day 1
notion_page: ""        # Notion GTM page ID
workspace_id: ""       # DynamoDB AdminConfig ID (empty until provisioned)
aws_account: ""        # AWS account number (empty until provisioned)
status: "active"       # active | paused | won | lost
tags: []
---
```

---

## Integration rules

**Jira**
- Every trial MUST have a Jira epic (`jira_epic` field) created before Day 1
- Trial engineering work (provisioning, context build, Slack config) goes under that epic
- Find live epics: `mcp__jira__jira_get_epics(boardId=152, done=false)`
- Ticket format: `jira/TICKET_TEMPLATE.md`

**Notion**
- Trials link to the Go-To-Market section: `19302437-dde4-80e5-b46d-de6c7e701ebf`
- Fill `notion_page` frontmatter once the GTM page is created
- Do NOT duplicate Notion content here — link, don't copy

**DynamoDB**
- `active/` clients have `workspace_id` linking to `AdminConfig` table in PROD
- DynamoDB is the source of truth for live account data
- Markdown holds context DynamoDB doesn't: decision history, contacts, expansion notes

**Feature docs**
- Capability map claims link to `../platform-saas-ai-context/docs/features/{slug}.md`
- Missing feature docs are flagged `[demo-ready, no feature doc]` — each is a `/write-feature-doc` task
