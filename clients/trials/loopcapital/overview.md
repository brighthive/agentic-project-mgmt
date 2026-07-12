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

**Status: Jira-complete, but "fully shipped" OVERSTATES the real capability — CORRECTED
2026-07-12 (pass 7), re-verified directly against code, not re-trusting the prior
2026-07-10 pass**:
- Epic **BH-860** (Skills Extension Framework) + all 14 child tickets (BH-861–875) —
  **Done** in Jira. This part of the original claim holds.
- All 3 skills exist on disk (`brightbot/brightbot/skills/system/{ssis-diagnostics,ssrs-diagnostics,storage-optimization}/SKILL.md`), but **all 3 are prompt-only** — there is
  NO deterministic `.dtsx`/`.rdl` XML parser anywhere in the repo (confirmed by grep: zero
  `.py` files under `skills/system/`, zero `ElementTree`/`lxml` usage for either format).
  Both SSIS and SSRS diagnosis rely entirely on the LLM reading raw XML text and reasoning
  about it — real, but categorically different from "shipped code that parses SSIS
  packages," which is how "fully shipped" reads.
- **SSIS**: 2 real, committed toy fixtures exist
  (`brightbot/tests/fixtures/skills/{create_assetmanagement_mysql,load_assets_with_bottlenecks}.dtsx`,
  ~100-130 lines each, 1-3 components) — deliberately simple, per the fixture README's own
  admission ("contains no row-by-row OLE DB Command, blocking transform, or Data Flow
  bottleneck"). Not representative of a real Loop-Capital-scale SSIS package.
- **SSRS: zero fixtures exist of any kind** (`find . -iname "*.rdl"` returns nothing,
  repo-wide). The SSRS skill has never been exercised against a real or synthetic `.rdl`
  file — its "shipped" status rests entirely on the skill file existing and the epic being
  marked Done, not on any demonstrated diagnosis.
- **No live legacy SQL Server connection exists for SSIS/SSRS specifically.** The only
  SQL-Server-family code in brightbot (`warehouse_connections.py:234-301`) is an Azure
  Synapse warehouse connector — unrelated to `msdb`/`ReportServer` catalog metadata. Every
  SSIS/SSRS diagnosis today is local-file-upload-based (`.dtsx`/`.rdl` read from disk), not
  a connection to a real customer SQL Server instance. This matters directly for any future
  "monitor Loop's actual legacy SQL Server for SSIS/SSRS health" ask — that capability does
  not exist today in any form, prompt-based or otherwise.
- Bedrock requirement satisfied — brightbot already runs on `ChatBedrockConverse`, no
  Anthropic API key. This part of the original claim holds.

**Bottom line**: the 7/9 demo capability is real for SSIS (prompt-based diagnosis + weak
fixture) but essentially undemonstrated for SSRS (no fixture at all), and there is no path
today from "diagnose an uploaded file" to "monitor a live legacy SQL Server's SSIS/SSRS
catalog" — that would be new, unscoped work if Loop Capital asks for it.

Full detail (superseded by the correction above where they conflict):
`project_ssis_poc_vs_proactive_priority.md` (memory).

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
| Legacy pipeline diagnostics (SSIS/SSRS/storage) | PARTIAL — already demoed 7/9, but **corrected 2026-07-12 (pass 7)**: prompt-only, no deterministic parser for either format; SSIS has 2 toy fixtures, SSRS has zero; no live SQL Server (`msdb`/`ReportServer`) connection exists | If Loop Capital asks to monitor a REAL legacy SQL Server's SSIS/SSRS catalog (not just diagnose an uploaded file), that is new, unscoped work — no such connection path exists today |
| Proactive pipeline monitoring (dbt/Databricks/ETL job-status) | IN PROGRESS | Architecture + tickets complete; BH-1043 (dbt) closest to buildable, BH-1044 (Databricks) has an open storage-model decision |
| SQL-Server-with-no-MCP disk/job monitoring | IN PROGRESS, demo-blocking gap identified | Real technical answer exists (query via existing warehouse-connection machinery, no new protocol) — but **no staging SQL Server fixture is provisioned yet** (BH-1057, runbook ready, ~3-5hrs, not yet executed) |
| Ingestion/source-sync proactive health | IN PROGRESS | BH-1048–1052 scoped; Airbyte/Step-Functions pollers are greenfield (no existing tool to wrap) |
| Multi-channel surfacing (Slack + webapp) | REAL, verified against live code | Email/SES channel confirmed dead/unbuilt — Slack+webapp is the actual complete channel set today |
| Fix-recurrence surfacing (Frank's ask #3) | PARTIAL | Self-healing surgical-PR loop (GC-11) is the mechanism; wiring is BH-1047, with a P0 safety fix required (see below) |
| BrightRoutines exposed via MCP/A2A | SCOPED, not built | BH-1038–1041; separate concern from monitoring, unaffected by the above |
| Lineage-aware data quality (Track C — silent-corruption detection) | SCOPED, genuinely new, NOT for 7/17 | BH-1061–1064; the "zero pipeline errors, wrong Gold numbers" gap — BrightHive glues dbt/Databricks' own lineage to before/after monitoring, doesn't rebuild lineage. Honest post-demo framing, see Track C below |

## Track C: Lineage-Aware Data Quality — SCOPED, post-demo

Kuri's example (2026-07-12): "one column has error from source and NULLs come in, there's
ZERO errors on the pipeline; but that value change is producing wrong numbers on
gold/diamond data products." Verified this is a real, unaddressed gap — longitudinal
monitoring (GC-12) can catch the null spike itself if configured, but nothing today traces
which downstream Gold/Diamond tables it poisons. Full spec:
`../../docs/specs/lineage-aware-data-quality.md`.

**Key framing, not a gap to hide from Frank**: BrightHive doesn't rebuild lineage — dbt and
Databricks already compute their own. BrightHive's differentiator is being the glue that
connects source-column health (before ELT) → the lineage those tools already know → Gold/
Diamond impact (after ELT), which neither tool sees on its own. For 7/17: show the
anomaly-detection half (real, shipped) and be upfront that the impact-tracing half is the
next phase.

## Engineering Artifacts

- **Handover spec**: `../../docs/specs/proactive-pipeline-ingestion-monitoring.md` — read its
  "Start Here" section first. Interface contracts, invariants (14), Gherkin AC, eval criteria,
  observability contract, full pass-by-pass verification log.
- **Jira**: epics **BH-1036** (Monitoring Agents) and **BH-1037** (Ingestion Observability),
  plus BH-1038–1041 (BrightRoutines MCP/A2A, under BH-115), BH-1053/1055/1059 (infra tracking),
  BH-1060 (security follow-up).
- **Verification memory**: `~/.claude/projects/-Users-bado-iccha-brighthive/memory/project_loop_capital_pass_index.md` — one-line index into 34+ detailed pass files.
- **Full demo plan**: `poc.yaml` (scope/ownership/demo-relative phases: T-5 → T-0) → renders `TRACKER.md` (live ticket/PR status, regenerate with `make poc-tracker-no-slack CLIENT=loopcapital`). Plan is organized by Suzanne's 3 committed demo points, not calendar days — see `poc.yaml`'s phase titles.
- **Draft PR (Track B)**: [#94](https://github.com/brighthive/agentic-project-mgmt/pull/94) — the proactive-monitoring handover spec + this client folder, on `drchinca/BH-1036/proactive-monitoring-spec`.
- **Draft PR (Track C)**: [#95](https://github.com/brighthive/agentic-project-mgmt/pull/95) — the lineage-aware-data-quality spec, on `drchinca/BH-1061/lineage-aware-data-quality-spec`. Split into its own PR 2026-07-12 to keep both under the 900-line PR-size threshold — Track C is non-blocking for 7/17 and has zero file overlap with Track B.
- **Track C spec**: `../../docs/specs/lineage-aware-data-quality.md` (PR #95) — ASCII
  architecture diagrams of the current-state gap (3 disconnected islands) and the proposed
  glue-layer design, plus interface contracts/invariants/Gherkin AC for BH-1062–1068.

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
| 2 | BH-1044 Databricks storage-model decision (brightbot-only secret vs. platform-core schema change) — recommendation made, not confirmed. **CORRECTED 2026-07-12 (pass 7)**: this decision alone does NOT unblock Databricks work — confirmed zero Databricks connection code exists anywhere in brightbot/platform-core (both repos' warehouse-type enums are closed to redshift/snowflake/azure_synapse/postgres); a new connector + enum members + Unity Catalog system-schema enablement are ALSO required, independent of where credentials live | Kuri | 2026-07-10 | — |
| 3 | BH-1047 code-level auto-merge exclusion not yet built | Kuri | 2026-07-10 | — |

## Decision

_Filled after 2026-07-17._

**Outcome**: TBD

**Rationale**: TBD

**Next Steps**: TBD
