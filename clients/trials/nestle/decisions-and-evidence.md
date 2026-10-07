---
name: "Nestlé decisions and evidence"
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
tags: [nestle, decisions, evidence]
---

# Nestlé decisions and evidence

Use this record to preserve commitments, unresolved decisions and evidence across
sessions. Session statements below were received October 6, 2026 Costa Rica time
(October 7 UTC). Preserve the source and strength of each claim when updating.

## Decisions received

| ID | Decision / statement | Source | Effect |
|---|---|---|---|
| D-01 | Dedicated room belongs in agentic management clients/trials | User: "agentic mgmt clients trials" | Canonical home is `clients/trials/nestle/` |
| D-02 | Nestlé is the biggest client; objective is global expansion across divisions after a six-week trial | User's active goal | Retain enterprise scope; signed expansion commitment not supplied |
| D-03 | Start November 15; January fallback | User: "starts on 15 nov if not Jan" | Plan November 2026 / January 2027 provisionally; confirm year and fallback day |
| D-04 | The technical Slack message offered no business value | User feedback earlier in this session | Actionability and verified business context required; no acceptance credit for receipt |

## Open decisions and blockers

All accountable roles below still need named people. No due date is a commitment
until the trial owner accepts it.

| ID | Required decision / evidence | Proposed accountable role | Needed by | State |
|---|---|---|---|---|
| O-01 | Committed dates, holiday coverage and final decision meeting | Joint sponsors | Before invitations | Open |
| O-02 | Account owner, Nestlé champion/sponsor and approval authority | BrightHive account lead | Before scope signoff | Open |
| O-03 | Full division/region inventory and pilot selection | Nestlé sponsor | Before scope signoff | Open |
| O-04 | Business products, baseline, thresholds and signatories | Product owners | Before Day 1 | Open |
| O-05 | Current workspace/account mapping and data/access permission | Technical/security owners | Before access | Open |
| O-06 | Live Jira epic and GTM reference | Delivery owner | Before Day 1 | Open; no epic assigned |
| O-07 | Cost/volume acceptance scope and billing evidence availability | Commercial/platform owners | Before Day 1 | Historical ask to reconfirm |
| O-08 | Incident recipients, support coverage and real approval path | Operations owner | Before monitoring | Open |

## Source register

| Source | What it establishes | Limit |
|---|---|---|
| [Environment matrix](../../../docs/ENVIRONMENTS.md) | April 9 record associates Nestlé UAT with ProdTestWorkspace and Matt | Historical, not the confirmed November workspace or owner |
| [Release engineering notes](../../../docs/releases/3.0/ENGINEERING_NOTES.md) | Historical UAT and e2e infrastructure context | No current client acceptance or access authorization |
| [Volume matrix spec](../../../docs/specs/volume-matrix-report.md) | Nestlé's earlier demand for evidence-based cost at volume | Example dollar tables are not trial measurements |
| [Consolidated cost theme](../../../docs/specs/THEME-cost-and-volume.md) | Tagging → metering → reporting dependency; parked pending commercial confirmation | Its historical ticket/status statements require live refresh |
| [MCP rollout evidence](https://github.com/brighthive/agentic-project-mgmt/pull/201#issuecomment-6031820227) | Staging demo quality/project checks and Slack delivery smoke | Different workspaces; no Nestlé acceptance |
| [Client operations contract](../../AGENTS.md) | Trial epic, frontmatter, lifecycle and source-of-truth rules | Architecture belongs in the context repo |

## Evidence updates

For each new item record date, author, criterion/decision ID, environment, division,
source link, observed outcome and reviewer. Link controlled artifacts instead of
copying sensitive customer records. Record who changed a decision and why. Do not
replace an unresolved item with a favorable assumption or mark the trial won from
platform test results.
