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

**GAP FOUND, completeness audit 2026-07-12**: the client's ORIGINAL verbatim ask
(`artifacts/poc-scope-from-client.md:33`, "Provide a resource costing to show what the cost
will be (cost management)") has **NO ticket, no spec section, and no mention anywhere in
poc.yaml/TRACKER.md** — it was silently dropped somewhere between the original ask and Track
A's Jira scoping. This is distinct from the `storage-optimization` skill's warehouse-storage
cost analysis (which covers `SKILL.md:3,19`'s "reduce warehouse spend" — a real, shipped, but
narrower capability): the client's line 33 ask reads as an overall PROJECT/ENGAGEMENT cost
estimate ("what the cost will be" for this work), not a warehouse-storage line item. **Not
yet resolved — flag to Kuri/Suzanne before 7/17**: either (a) confirm this was already
delivered out-of-band (a sales-side cost proposal, not an engineering deliverable — plausible
given the phrasing, but unconfirmed here), or (b) file it as a real gap if it was expected to
be part of the agent's output.

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
| Legacy pipeline diagnostics (SSIS/SSRS/storage) | PARTIAL, **updated 2026-07-13**: brightbot's own diagnostics skills are still prompt-only (no deterministic parser for either format, confirmed 2026-07-12); but the demo sandbox now has a REAL `.dtsx` (`Extract_Holdings_Nightly.dtsx`) and the first real `.rdl` anywhere in this org (`Holdings_Daily_Report.rdl`), both querying a real running SQL Server — `clients/trials/loopcapital/sandbox/ssis/`, `.../ssrs/` | If Loop Capital asks to monitor a REAL PRODUCTION legacy SQL Server's SSIS/SSRS catalog (not this sandbox), that remains new, unscoped work |
| Proactive pipeline monitoring (dbt/Databricks/ETL job-status) | **Updated 2026-07-15**: dbt (BH-1043) and SQL Server (BH-1045) adapters + the scheduled watchdog (BH-1054) are merged to develop; both `check_pipeline_health_tool` and `scan_warehouse_tables_tool` now also reachable directly from the governance chat agent, not just the scheduler/MCP. Databricks (BH-1044) still has an open storage-model decision | BH-1044 (Databricks) remains the only adapter not started |
| SQL-Server-with-no-MCP disk/job monitoring | **Updated 2026-07-15**: shipped + enriched, merged to `develop` AND `staging` on ALL THREE repos (brightbot, brightbot-slack-server, brighthive-webapp). BH-1045's disk-check + job-status queries; alerts carry the largest offending file (disk-low) and the failed step name + raw error text (job failure). Verified against the REAL local Docker sandbox end-to-end (5 real-behavior tests, zero AWS SSO dependency): correct percent_free, real job pass/fail mix, enrichment fields, and `check_pipeline_health_tool`'s chat surface all reach the live backend. Slack renderer parity merged (brightbot PR #830, brightbot-slack-server PR #135). Cooldown/retry-storm suppression (Invariant 3) also merged (#835) — a real gap found and closed the same pass. **Webapp renderer parity (BH-1067's other half) merged (brighthive-webapp PR #1300)** — `etl_job_failure`/`source_disk_low` added back to `BackendStage` (deliberately pruned in BH-1088's audit for having no live producer; now they do), new `pipeline` StageGroup/NotificationCategory, all three local stage→title switches updated. | Remaining gap is operational, not code: Loop Capital has no provisioned real workspace yet (see Open Blocker #5) — the 7/17 demo runs against the local Docker sandbox, not a live customer SQL Server |
| Ingestion/source-sync proactive health | IN PROGRESS | BH-1048–1052 scoped; Airbyte/Step-Functions pollers are greenfield (no existing tool to wrap) |
| Multi-channel surfacing (Slack + webapp) | **Updated 2026-07-15**: REAL for GC-15's two watchdog stages on BOTH surfaces now (previously only Slack); still true for the pre-existing quality/profiling/schedule stages | Email/SES channel confirmed dead/unbuilt — Slack+webapp is the actual complete channel set today |
| Fix-recurrence surfacing (Frank's ask #3) | **Updated 2026-07-15**: BH-1047's safety gate (`REMEDIATION_TOOLS` excluding `github_merge_pull_request`) is merged. The GC-16 remediation loop (classifier + scoped agent) is **merged** (PR #829), on `develop` + `staging`. GC-17's adversarial sub-case (`github_merge_pull_request` absent from the real ToolNode execution-time lookup, not just the static tool list) also landed (#833). | Post-merge fix-verification (BH-1091) intentionally deferred to human-in-the-loop per explicit product decision — reviewer merges the PR, no automated re-run/verify step |
| BrightRoutines exposed via MCP/A2A | SCOPED, not built | BH-1038–1041; separate concern from monitoring, unaffected by the above |
| Lineage-aware data quality (Track C — silent-corruption detection) | SCOPED, genuinely new, NOT for 7/17 | BH-1061–1064; the "zero pipeline errors, wrong Gold numbers" gap — BrightHive glues dbt/Databricks' own lineage to before/after monitoring, doesn't rebuild lineage. Honest post-demo framing, see Track C below |

## Track C: Lineage-Aware Data Quality — SCOPED, post-demo

Kuri's example (2026-07-12): "one column has error from source and NULLs come in, there's
ZERO errors on the pipeline; but that value change is producing wrong numbers on
gold/diamond data products." Verified this is a real, unaddressed gap — longitudinal
monitoring (GC-12) can catch the null spike itself if configured, but nothing today traces
which downstream Gold/Diamond tables it poisons. Full spec:
`../../../docs/specs/lineage-aware-data-quality.md`.

**Key framing, not a gap to hide from Frank**: BrightHive doesn't rebuild lineage — dbt and
Databricks already compute their own. BrightHive's differentiator is being the glue that
connects source-column health (before ELT) → the lineage those tools already know → Gold/
Diamond impact (after ELT), which neither tool sees on its own. For 7/17: show the
anomaly-detection half (real, shipped) and be upfront that the impact-tracing half is the
next phase.

## Track D: Per-Project Pipeline Health View — PROPOSED, CORRECTED 2026-07-12 (2 passes)

Kuri's follow-up (2026-07-12): this work should surface to a **proactive view on Projects**
— Projects already have transformations/flow, and should have their own dedicated view for
pipeline health (working name "Brightlines," not yet validated with UX/product review).

**CORRECTION (same day, second pass)**: the first pass's premise was wrong — this is NOT
greenfield. Projects' "Flow" tab (`ProjectNavBar.tsx`) actually renders `WorkflowSpecPage.tsx`
today (the legacy static-DAG canvas is dead code, confirmed unreachable), which **already
ships a real run-history panel and live run-timeline** — the exact capability class the
first pass thought was missing. A direct 7-point UI audit against this real, already-shipped
surface also found genuine defects (zero mobile responsiveness across 4 components, a dead
legacy-fallback branch, a tab/route access-gate mismatch letting Collaborators reach an
Admin-hidden page, no accessibility attributes, zero component tests, and more) — all
confirmed against real code, not assumed.

**Re-scoped as two pieces** (full detail in `../../../docs/specs/lineage-aware-data-quality.md`'s
"Track D" section):
- **D1**: fix the 7 confirmed defects in the EXISTING `WorkflowSpecPage` — closer to a
  bug/tech-debt backlog than new-feature work, could be ticketed now.
- **D2**: enrich `WorkflowSpecPage`'s EXISTING run-history/timeline panels with this epic's
  watchdog/anomaly/downstream-impact signals, rather than building a competing new tab — still
  needs a `/write-spec` + design pass before ticketing.

## Track E: Agentic SQL Server Profiling & DB-Level Quality Health Checks — SCOPED (2026-07-13)

Kuri's follow-up (2026-07-13): part of the broader BrightHive SaaS vision — connect MCP
against Microsoft SQL Server so a legacy DB can be agentically identified, scanned, and
quality-health-checked, a PROFILER at the DB/warehouse level, not just per-table.

**Verified against real code (not assumed)**: most of the plumbing already exists.
`SynapseConnection` already connects to a bare SQL Server instance with zero code changes
(the same confirmed fact BH-1045's disk/job queries already rely on). `introspect_warehouse_schema`
already does warehouse-LEVEL table discovery via MCP with no pre-registered `DataAssetNode`
required — the real precedent for "point an agent at a whole warehouse and let it explore."
But the profiler/quality-check layer (`profiler_task.py`, the 3 MCP quality tools) is
ENTIRELY asset-ID-gated today — there is no "point it at the whole DB and profile everything"
mode, and discovery + profiling are never chained end to end.

**Full detail**: `../../../docs/specs/proactive-pipeline-ingestion-monitoring.md`'s "Track E"
section (added pass 81, tickets filed pass 82). The naming/scope decision (is SQL Server a
distinct `WarehouseType`, or a reuse of `azure_synapse`'s connector?) was RESOLVED against the
real webapp UI convention — every warehouse provider gets its own first-class label/icon
today, so a genuine new `sql_server` type is the correct choice, not a Synapse relabel. 3
tickets filed under epic BH-1036: **BH-1075** (new connection type, connector code unchanged),
**BH-1076** (discovery → per-table profiling orchestration), **BH-1077** (DB-level rollup
report). Non-blocking for 7/17.

## Engineering Artifacts

- **Golden Cases (GC-14–17)**: `../../../docs/specs/golden-cases-loopcapital.md` — the first Golden
  Cases ever scoped to Loop Capital (continuing brightbot's Longaeva GC-1–13 numbering). Maps
  Suzanne's 3 demo points 1:1 to GC-14 (proactive alert), GC-15 (SQL-Server-no-MCP), GC-16
  (fix-recurrence PR), plus GC-17 (the auto-merge-exclusion safety gate GC-16 depends on).
  Acceptance criteria are written as Frank's real scenes (a broken nightly Asset Management job,
  a legacy SQL Server with nothing installed on it), not platform-feature Gherkin alone.
- **Handover spec**: `../../../docs/specs/proactive-pipeline-ingestion-monitoring.md` — read its
  "Start Here" section first. Interface contracts, invariants (18, count re-verified pass 81 —
  was stale at 16), Gherkin AC, eval criteria, observability contract, full pass-by-pass
  verification log.
- **Jira**: epics **BH-1036** (Monitoring Agents) and **BH-1037** (Ingestion Observability),
  plus BH-1038–1041 (BrightRoutines MCP/A2A, under BH-115), BH-1053/1055/1059 (infra tracking),
  BH-1060 (security follow-up).
- **Verification memory**: `~/.claude/projects/-Users-bado-iccha-brighthive/memory/project_loop_capital_pass_index.md` — one-line index into 34+ detailed pass files.
- **Full demo plan**: `poc.yaml` (scope/ownership/demo-relative phases: T-5 → T-0) → renders `TRACKER.md` (live ticket/PR status, regenerate with `make poc-tracker-no-slack CLIENT=loopcapital`). Plan is organized by Suzanne's 3 committed demo points, not calendar days — see `poc.yaml`'s phase titles.
- **Handover spec, Track B**: `../../../docs/specs/proactive-pipeline-ingestion-monitoring.md`
  — **merged to master** via PR [#94](https://github.com/brighthive/agentic-project-mgmt/pull/94) (2026-07-12).
- **Track C spec**: `../../../docs/specs/lineage-aware-data-quality.md` — **merged to master**
  via PR [#95](https://github.com/brighthive/agentic-project-mgmt/pull/95) (2026-07-12). ASCII
  architecture diagrams of the current-state gap (3 disconnected islands) and the proposed
  glue-layer design, plus interface contracts/invariants/Gherkin AC for BH-1062–1070.
- **This client folder**: merged to master via PR [#96](https://github.com/brighthive/agentic-project-mgmt/pull/96) (2026-07-12).
- **PR #97 — merged** to master (dual-write shape correction, BH-1054/BH-1046), verified
  pass 47 via `gh pr view 97` rather than trusting a prior pass's "open" note as still true.
- **Open follow-up PR**: [#98](https://github.com/brighthive/agentic-project-mgmt/pull/98) —
  on `drchinca/BH-1061/triple-click-zoom-pass-38`. Opened fresh after #97 merged (crossed the
  900-line split threshold); ongoing verification passes land here until it's next merged.

## Things that must happen before 7/17, not yet done

**RE-VERIFIED pass 62 (2026-07-12) — all still genuinely open, checked fresh against live
Jira status + real code, not carried forward from an earlier pass's note. Updated from "two
things" to the real current count.**

**RE-VERIFIED pass 51 (2026-07-12) — both still genuinely open, checked fresh against live
Jira status + real code, not carried forward from an earlier pass's note:**

1. **BH-1057** — **RESOLVED 2026-07-13, no longer an open blocker.** Replaced the RDS plan with a
   local Docker sandbox (`clients/trials/loopcapital/sandbox/`) — no billable AWS resource needed,
   no go-ahead required. Built and verified end-to-end: real disk-check + job-status queries
   return real data (18% free, one real Succeeded + one real Failed job run). Run `./setup.sh`
   before the demo, `./validate.sh` to confirm.
2. **BH-1058** — the dbt Cloud deliberate-failure fixture BH-1043's e2e case depends on.
   Re-checked pass 62: still `To Do`; the fix itself (a genuine runtime SQL error, not a
   compile-time `raise_compiler_error`) is already correctly specified in the ticket, just not
   yet executed — a one-time human dbt Cloud UI setup, ~XS effort, not code.
3. **BH-1047's safety fix — RESOLVED**: `REMEDIATION_TOOLS` (`dbt_agent_react.py`) now
   built via direct import, explicitly omitting `github_merge_pull_request` by name — a
   code-level gate, not just the system-prompt instruction. Merged via brightbot PR #813.
   The GC-16 remediation loop itself (classifier + scoped agent) is **merged** via PR #829
   (2026-07-15) — both to `develop` and promoted to `staging`. GC-17's own adversarial
   sub-case (proving `github_merge_pull_request` is absent from the tool-binding layer's
   real execution-time lookup, not just the static tool list) also landed the same pass, PR
   #833. GC-14/15/16/17 are all real code on staging now, verified against the local Docker
   sandbox with zero AWS SSO dependency (see "New gap found" below for what that
   verification pass surfaced).
4. **Confirm Loop Capital's real dbt Cloud connection count — STILL BLOCKED, verified
   2026-07-15**: searched `dynamo-vault/cli/secrets search "loop"/"loopcapital"` against
   STAGE (108 workspaces) and PROD (506 workspaces) — **zero match in either account.**
   This isn't a missing single-vs-multi-connection confirmation anymore; it means Loop
   Capital has **no provisioned workspace at all** yet in either environment. This
   frontmatter's blank `workspace_id`/`aws_account` fields (lines 11-12) are accurate, not
   an oversight. The demo on 7/17 must be running against a synthetic/sandbox workspace,
   not a real Loop Capital tenant — confirm this is the intended demo setup before 7/17,
   since BH-1043's dbt watchdog and BH-1045's SQL Server watchdog both require a real
   `workspace_id` to poll against.
5. **Cooldown/retry-storm suppression — RESOLVED same day (see Open Blocker #6)**.
6. **CodeRabbit code-review pass, 2026-07-15 — 8 real bugs found and fixed** (brightbot PR
   #840, merged to develop + staging): a cooldown-store outage previously suppressed EVERY
   alert that cycle instead of failing open; one broken pipeline adapter aborted the whole
   chat health-check instead of isolating per adapter; disk-low enrichment picked the largest
   file across the whole database instead of the specific low volume; job-failure detail
   correlation was keyed by job_id alone with no run correlation — and the FIRST fix attempt
   for that (keying on `instance_id`) was itself wrong, caught by a strengthened test:
   verified directly against the real sandbox that `instance_id` increments per history row,
   not per run — re-keyed on `(job_id, run_date, run_time)`, the value msdb actually shares.
   Also tightened 3 overly-broad root-cause-classifier regexes that could misclassify a
   generic dbt compile error into a wrong-cause remediation PR, and added error handling to
   the remediation subagent that previously had none. 4 golden-case tests were also
   strengthened to prove real behavior instead of passing on import/registry checks alone.
7. **RE-VERIFIED 2026-07-15, final pass — after the CodeRabbit fixes**: fresh sandbox
   teardown-then-rebuild, then `RUN_LIVE_SQLSERVER=1 pytest tests/integration/golden_cases/
   -k "gc_14 or gc_15 or gc_16 or gc_17"` against current `develop` HEAD — **13 passed, 0
   failed, 4 honestly-skipped** (BH-1087 webapp parity, BH-1058 dbt Cloud fixture, multi-
   connection disambiguation — all real, tracked, non-blocking). Full `governance_agent`/
   `dbt_agent` unit suites: 278/278. GC-14/15/16/17's engineering-buildable scope is
   **complete AND code-reviewed on `develop` AND `staging`**. Everything left open (below) is operational or
   business, not code.

## Open Blockers

| # | Blocker | Owner | Raised | Resolved |
|---|---|---|---|---|
| 1 | BH-1057 SQL Server fixture not provisioned | Kuri | 2026-07-10 | **2026-07-13** — Docker sandbox built + verified, replaces AWS RDS plan |
| 2 | BH-1044 Databricks storage-model decision (brightbot-only secret vs. platform-core schema change) — recommendation made, not confirmed. **CORRECTED 2026-07-12 (pass 7)**: this decision alone does NOT unblock Databricks work — confirmed zero Databricks connection code exists anywhere in brightbot/platform-core (both repos' warehouse-type enums are closed to redshift/snowflake/azure_synapse/postgres); a new connector + enum members + Unity Catalog system-schema enablement are ALSO required, independent of where credentials live | Kuri | 2026-07-10 | — |
| 3 | BH-1047 code-level auto-merge exclusion not yet built | Kuri | 2026-07-10 | **2026-07-15** — `REMEDIATION_TOOLS` merged (brightbot PR #813); GC-16 remediation loop itself merged (PR #829), on `develop` + `staging` |
| 4 | Client's original "resource costing / cost management" ask (`poc-scope-from-client.md:33`) has no ticket, spec section, or tracked deliverable — confirm whether already delivered out-of-band (sales-side cost proposal) or a real engineering gap | Kuri/Suzanne | 2026-07-12 | — |
| 5 | **Escalated 2026-07-15**: not just "confirm connection count" anymore — `dynamo-vault search "loop"/"loopcapital"` returns **zero workspaces in STAGE or PROD**. Loop Capital has no provisioned real workspace at all. 7/17's demo must run against a synthetic/sandbox workspace — confirm that's the plan, since BH-1043/BH-1045's watchdogs both need a real `workspace_id` to poll. | Kuri | 2026-07-12 | — |
| 6 | Cooldown/retry-storm suppression (Invariant 3) had zero code — confirmed by grep, not assumed. Real risk of duplicate Slack alerts on a flapping job or persistent low-disk condition. | Kuri | 2026-07-15 | **2026-07-15** — `pipeline_alert_cooldown.py` built (4-tuple key, DynamoDB + in-memory adapters), wired into `_publish_signals`, merged (brightbot PR #835), on `develop` + `staging` |

## Decision

_Filled after 2026-07-17._

**Outcome**: TBD

**Rationale**: TBD

**Next Steps**: TBD
