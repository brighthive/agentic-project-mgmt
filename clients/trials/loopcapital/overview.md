---
name: "Loop Capital"
slug: "loopcapital"
stage: "trial"
champion: "Frank"
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: "2026-07-17"
jira_epic: "BH-1036"
notion_page: ""
workspace_id: ""
aws_account: ""
status: "active"
tags: [legacy-analyst, ssis, ssrs, proactive-monitoring, mcp-a2a]
---

# Loop Capital — Trial Overview

> This file was created 2026-07-12 to fill a real gap: two weeks of active POC work (two
> demos, 24 Jira tickets, a full handover spec) existed only in Jira + a specs doc, with no
> client-lifecycle folder tracking it the way Longaeva has one. This is that folder, backfilled
> from what's actually documented elsewhere — contacts/dates below are intentionally left
> blank where not confirmed, not guessed.

## North Star

Loop Capital's champion (Frank) wants to see BrightHive's platform demonstrate genuine
proactivity — an engineering agent that checks, finds issues, alerts, and (for safe cases)
fixes them unprompted, the way a human data engineer would — not just respond to prompts. His
own words after the 7/9 demo: *"I don't think that you're there because I did not see how your
digital engineers are going to do the level of proactivity that I'm imagining."*

## Contacts

| Name | Role | Email | Notes |
|---|---|---|---|
| Frank | Champion / Decision-maker | — | Drives the "future world" vision (digital workers alongside human engineers); skeptical after 7/9, needs to see it live |
| Suzanne | BrightHive GTM lead | — | Owns the sales-gate relationship, sets demo commitments |
| Matt | BrightHive eng/GTM | — | Coordinates kickoff logistics (BrightHive Studio, asset links) |
| Kuri | BrightHive tech lead | — | Owns engineering delivery for both demo tracks |

## Timeline

| Date | Event |
|---|---|
| 2026-06-2x (pre) | POC kickoff planning — SSIS/SSRS "Legacy Analyst Analyzer Agent" scope defined for BrightHive Studio |
| 2026-07-02 (target) | Original kickoff target: SSIS data assets + acceptance criteria/blueprint in BrightHive Studio |
| 2026-07-09 | Demo #1 — "POC Scope Technical Deep Dive." Delivered: Legacy Analyst Analyzer Agent (SSIS/SSRS/storage-optimization skills) — see [Track A](#track-a-legacy-analyst-analyzer-agent-ssisssrsstorage--shipped). Frank's reaction: platform is real but "your screen says this is not live" and proactivity wasn't demonstrated. |
| 2026-07-17 | Demo #2 — committed follow-up, scoped by Suzanne's reply (see [Track B](#track-b-proactive-monitoring--in-progress)). Decision gate for moving toward a sale. |

## Track A: Legacy Analyst Analyzer Agent (SSIS/SSRS/Storage) — SHIPPED

Original POC ask (7/9 demo): one agent, three skills (SSIS diagnostics, SSRS diagnostics,
storage optimization), synthetic SSIS data modeled on Loop's Asset Management domain,
bottleneck analysis + dbt-migration suggestions.

**Status: fully shipped**, verified 2026-07-10 against Jira + code:
- Epic **BH-860** (Skills Extension Framework) + all 14 child tickets (BH-861–875) — **Done**.
- All 3 skills exist on disk: `brightbot/brightbot/skills/system/{ssis-diagnostics,ssrs-diagnostics,storage-optimization}/SKILL.md`.
- Synthetic `.dtsx` fixture built (BH-869), staging validation + demo prep done (BH-866).
- Bedrock requirement satisfied — brightbot already runs on `ChatBedrockConverse`, no Anthropic API key.

Full detail: `project_ssis_poc_vs_proactive_priority.md` (memory).

## Track B: Proactive Monitoring — IN PROGRESS (the 7/17 demo)

Suzanne's committed scope for 7/17, directly from her reply to Frank:

1. The engineering agent proactively monitors, detects, and resolves issues, alerting the user on what it finds.
2. How MCP connects to a SQL server that has **no MCP of its own** (Frank's literal example: disk-space monitoring at 20% remaining).
3. Skills that surface fixes the agent applied, to avoid recurrence of the same issue.

**Engineering response**: a full handover spec + 24 Jira tickets, built over ~33 verification
passes (2026-07-10 to 2026-07-12), each citing real code or live AWS data rather than
assumption. Full detail below in [Capability Coverage](#capability-coverage-summary) and
[Engineering Artifacts](#engineering-artifacts).

## Capability Coverage Summary

| Workstream | Coverage | Key Caveat |
|---|---|---|
| Legacy pipeline diagnostics (SSIS/SSRS/storage) | FULL MATCH — shipped | None; already demoed 7/9 |
| Proactive pipeline monitoring (dbt/Databricks/ETL job-status) | IN PROGRESS | Architecture + tickets complete; BH-1043 (dbt) closest to buildable, BH-1044 (Databricks) has an open storage-model decision |
| SQL-Server-with-no-MCP disk/job monitoring | IN PROGRESS, demo-blocking gap identified | Real technical answer exists (query via existing warehouse-connection machinery, no new protocol) — but **no staging SQL Server fixture is provisioned yet** (BH-1057, runbook ready, ~3-5hrs, not yet executed) |
| Ingestion/source-sync proactive health | IN PROGRESS | BH-1048–1052 scoped; Airbyte/Step-Functions pollers are greenfield (no existing tool to wrap) |
| Multi-channel surfacing (Slack + webapp) | REAL, verified against live code | Email/SES channel confirmed dead/unbuilt — Slack+webapp is the actual complete channel set today |
| Fix-recurrence surfacing (Frank's ask #3) | PARTIAL | Self-healing surgical-PR loop (GC-11) is the mechanism; wiring is BH-1047, with a P0 safety fix required (see below) |
| BrightRoutines exposed via MCP/A2A | SCOPED, not built | BH-1038–1041; separate concern from monitoring, unaffected by the above |

## Engineering Artifacts

- **Handover spec**: `../../docs/specs/proactive-pipeline-ingestion-monitoring.md` — read its
  "Start Here" section first. Interface contracts, invariants (14), Gherkin AC, eval criteria,
  observability contract, full pass-by-pass verification log.
- **Jira**: epics **BH-1036** (Monitoring Agents) and **BH-1037** (Ingestion Observability),
  plus BH-1038–1041 (BrightRoutines MCP/A2A, under BH-115), BH-1053/1055/1059 (infra tracking),
  BH-1060 (security follow-up).
- **Verification memory**: `~/.claude/projects/-Users-bado-iccha-brighthive/memory/project_loop_capital_pass_index.md` — one-line index into 33 detailed pass files.

## Two things that must happen before 7/17, not yet done

1. **BH-1057** — provision a real staging SQL Server (RDS Web edition) so the disk-monitoring
   demo runs against real infrastructure, not a mock. Runbook is complete (~3-5 hrs). **Not yet
   executed** — needs a deliberate go-ahead from Kuri (this is a real, billable AWS resource).
2. **BH-1047's safety fix** — the remediation loop's tool-binding must exclude
   `github_merge_pull_request` at the code level (found: "never auto-merge" was previously a
   prompt-only instruction with no code enforcement). Must ship before any remediation-PR flow
   is demoed, regardless of timeline.

## Open Blockers

| # | Blocker | Owner | Raised | Resolved |
|---|---|---|---|---|
| 1 | BH-1057 SQL Server fixture not provisioned | Kuri | 2026-07-10 | — |
| 2 | BH-1044 Databricks storage-model decision (brightbot-only secret vs. platform-core schema change) — recommendation made, not confirmed | Kuri | 2026-07-10 | — |
| 3 | BH-1047 code-level auto-merge exclusion not yet built | Kuri | 2026-07-10 | — |

## Decision

_Filled after 2026-07-17._

**Outcome**: TBD

**Rationale**: TBD

**Next Steps**: TBD
