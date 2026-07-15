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
workspace_id: "e3fc0917-03a6-4ac6-aad4-ac265329bfb9" # synthetic demo workspace, staging, created 2026-07-15 — NOT a real Loop Capital workspace
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
8. **RE-VERIFIED 2026-07-15, webapp-parity pass**: BH-1067's webapp half
   (`etl_job_failure`/`source_disk_low` renderer parity, previously Slack-only) merged and
   promoted — brighthive-webapp PRs #1300/#1302. Multi-channel surfacing for GC-15 is now
   REAL on both Slack and webapp. Re-ran the full 3-repo test sweep after the merge: 13/13
   real-behavior tests (brightbot), 278/278 unit (brightbot), 12/12 (brightbot-slack-server),
   60/60 (brighthive-webapp) — all green.
9. **Jira hygiene pass, 2026-07-15**: found BH-1043/1045/1047/1054/1057's Jira status stale
   against merged reality (showing "To Do"/"Needs Refinement" despite code merged+verified
   weeks of real-sandbox testing ago). Added evidence comments to each and transitioned:
   BH-1057 → Done (the sandbox itself needs no staging QC — it's a local dev artifact);
   BH-1043/1045/1047/1054 → Staging QC (code is genuinely merged+promoted, but real
   customer-workspace validation is blocked on Open Blocker #5 — no provisioned workspace —
   so "Staging QC" is the honest state, not "Done"). BH-1067 commented with a split
   recommendation (etl_job_failure/source_disk_low done; dbt_run_stale + both Databricks
   stages genuinely have no producer yet).
10. **Follow-up Jira pass, 2026-07-15**: found + fixed 2 more stale tickets the same way —
    BH-1046 (proactive alert path) verified field-name-for-field-name against
    dbt_pipeline_source.py's real metadata keys, transitioned to Staging QC. BH-1076
    (warehouse discovery→profiling) verified against warehouse_scan.py + 7/7 passing unit
    tests, transitioned to Staging QC. **Left correctly open, confirmed genuinely unbuilt by
    direct code check**: BH-1042 (spec — §8 eval-design decisions not made), BH-1044
    (Databricks, zero connector code), BH-1075 (no new `sql_server` WarehouseType — demo
    uses the existing `azure_synapse` type as an interim path, which BH-1075's own ticket
    text explicitly allows), BH-1077 (DB-level rollup report, zero code), BH-1091/1092
    (post-merge verification loop — explicitly deferred to human-in-the-loop per an earlier
    product decision this session, not a gap), BH-1087/1060/1071 (dbt webapp parity /
    PII redaction / stale docs — untouched by this session's scope). Full epic status is now
    honest: 9 tickets in Staging QC/Done reflecting real merged+verified work, 10 correctly
    still open reflecting real remaining gaps.
11. **Second correlation bug found + fixed, 2026-07-15 (brightbot PR #842, merged develop +
    staging)**: extended real-sandbox e2e testing caught a real bug in the PRIOR pass's own
    fix — `(job_id, run_date, run_time)` correlation for job-failure detail was ALSO wrong,
    verified directly against the sandbox that a step-level row and its own job's outcome
    row can log `run_time` a full second apart. Corrected by moving the "most recent failed
    step" dedup into the SQL query itself (`ROW_NUMBER()`, partitioned by `job_id`) — no
    cross-row timestamp matching needed. Also added 2 new tests driving the REAL compiled
    `remediation_agent_graph` end-to-end (both unclassifiable and DATA_SHAPE-classified
    paths), closing the "node unit-tested" vs "graph wiring proven" gap for GC-16 without
    needing a live dbt Cloud + GitHub sandbox. Re-verified 3x in a row for stability, not a
    lucky pass — 15/15 real-behavior tests, 278/278 unit tests, both green on develop AND
    staging.
12. **Live-eval coverage added, 2026-07-15 (brightbot PR #844/#845, merged develop +
    staging)**: `check_pipeline_health_tool`/`scan_warehouse_tables_tool` (BH-1054/1076,
    surfaced to the governance chat agent this session) had only unit-mocked coverage —
    never proven against a real model call. The same class of gap already caught one real
    regression this session (a tool competing with, rather than serving, the `ssis-
    diagnostics` skill). Added 2 new live-eval tests mirroring `test_analyst_reads_ssis_
    skill`'s exact pattern — real Bedrock call, asserts the model calls the specific tool for
    its own documented trigger phrase. Both pass on real Bedrock (`BH_RUN_LIVE_EVALS=1`):
    "is anything broken in my pipelines right now?" → `check_pipeline_health_tool`; "scan my
    warehouse and tell me if any tables look unhealthy" → `scan_warehouse_tables_tool`.
13. **T-1 combined dry run, 2026-07-15**: `make poc-tracker-no-slack CLIENT=loopcapital`
    regenerated TRACKER.md from live Jira — checkbox status ("🟡 in progress") for BH-1045/
    1047/1054/1067 is honest, not stale (Jira's own `statusCategory` maps "Staging QC" to
    "In Progress" — the tracker's rendering is correct, matches the real state: code merged,
    live-workspace validation still blocked on Open Blocker #5). Ran the closest thing to
    TRACKER.md's own "T-1 — Full dress rehearsal" bar without a live workspace: fresh
    sandbox rebuild, then ALL THREE demo points' proof in one combined pytest invocation —
    `RUN_LIVE_SQLSERVER=1 BH_RUN_LIVE_EVALS=1 pytest tests/integration/golden_cases/
    tests/integration/test_skills_execution.py -k "gc_14 or gc_15 or gc_16 or gc_17 or
    governance"` — **17 passed, 0 failed, 5 honestly-skipped**. Point 1 (dbt watchdog logic),
    Point 2 (SQL Server disk-low against the real Docker sandbox), Point 3 (surgical PR via
    the real remediation graph), GC-17's safety gate, and live-Bedrock proactive-monitoring
    intent routing — all together, one command, all green.
14. **THIRD surface's parity gap found + fixed, 2026-07-15 (brighthive-platform-core PR
    #1050/#1051, merged develop + staging)**: checking `resolveSignal()`'s source registry
    (the per-user NotificationInbox delivery path — `notificationRecipients ->
    resolveSignal -> stored displayJson/detailJson`) found `source_disk_low`/
    `etl_job_failure` had NO entry — falling through to `formatGenericDisplay`. A real
    notification lands (never a stub/throw, per the registry's own design), but with no
    diagnostic detail. Slack (`brightbot-slack-server`) and the webapp's SSE toast
    (`Navbar.tsx`) both got this exact fix earlier this session; this THIRD surface — the
    per-user inbox itself, `brighthive-platform-core`, a repo not otherwise touched this
    session — had never been checked. Added real formatters reading the exact metadata keys
    `sql_server_pipeline_source.py` writes, mirroring the existing
    `notifications-workflow-suggestion-display.test.ts` test pattern. 37/37 unit tests pass.
    Merged to develop and staging.
15. **Real dual-write architecture traced end-to-end, 2026-07-15**: mapped the actual
    production path across all 4 repos by direct code read, not assumption —
    `publishNotification` (called by brightbot) writes `NOTIFICATIONS_TABLE` ONLY.
    `brightbot-slack-server`'s `NotificationPoller` is the real mechanism that scans that
    table, delivers to Slack, AND calls `platform-core`'s `notificationRecipients` (which
    writes `NotificationInbox` + pushes the SSE toast `Navbar.tsx` reads). `platform-core`'s
    `notificationRecipients` was NEVER called directly from brightbot's Python — confirmed
    by grep across the whole codebase. The poller's own code comment ("no stage filter — all
    stages push via SSE") was accurate but unproven for the two new watchdog stages
    specifically — added 2 new tests (brightbot-slack-server PR #141/#142, merged develop +
    staging) asserting the exact GraphQL request body sent to `notificationRecipients`
    carries the real enrichment metadata. This closes the loop the prior 3 surface-parity
    fixes (Slack formatter, webapp SSE toast, webapp inbox display) depended on but had
    never traced end-to-end.
16. **Real over-broadcast subscription bug found + fixed, 2026-07-15
    (brightbot-slack-server PR #143/#144, merged develop + staging)**: while writing a test
    to PROVE `SubscriptionStore.findMatching` correctly delivers GC-15's no-asset watchdog
    signals (`source_disk_low`/`etl_job_failure` never carry `asset_id` — SQL Server is a
    BYOW connection, never a catalogued `DataAssetNode`), the test asserting an
    asset-SCOPED subscription should NOT match a no-asset signal **failed against the real
    code** (`expected [...] to have a length of +0 but got 1`). Root cause:
    `if (sub.asset_filter !== "*" && assetId && sub.asset_filter !== assetId) return false`
    — the `assetId &&` guard silently skipped the whole check whenever a signal had no
    asset, so an asset-specific subscription ("alert me about asset X only") incorrectly
    matched EVERY no-asset signal in the workspace. This is a real, previously-undetected
    over-broadcast bug affecting the whole notification system, not just Loop Capital's two
    new stages — found via real-behavior test-writing per `test-behavior-real.md`, not
    static review. Fixed by dropping the `assetId &&` short-circuit; verified against the
    full 629-test suite (no regressions). Merged to develop (#143) and promoted to staging
    (#144).
17. **Third-party fix from teammate promoted to staging, 2026-07-15
    (brighthive-platform-core PR #1054)**: Harbour (Nano-233) merged #1052 to develop — an
    AI-only quality run (no configured rules, all counts 0, status "passed") was silently
    filtered out of the notification inbox because `qualityStageFilter`'s count-gated
    conditions (`failedCount/droppedCount/passedCount > 0`) never fired for a metric-free
    run. Same notification pipeline GC-14/GC-15 depend on — promoted develop→staging
    immediately per the standing "--admin all to staging" directive rather than letting it
    drift. All 4 repos (`brightbot`, `brighthive-webapp`, `brighthive-platform-core`,
    `brightbot-slack-server`) confirmed fully synced (develop == staging, zero commits
    ahead) as of this pass.
18. **GC-17 safety gate re-verified + full-suite regression re-run, 2026-07-15**: read
    `test_gc_17_auto_merge_exclusion.py` in full — the code-level backstop is solid
    (`REMEDIATION_TOOLS` built by direct import, excludes `github_merge_pull_request` by
    construction; a third test introspects the REAL compiled agent's bound tool dict, not
    just the expected list, so drift between the two can't silently pass). 3/3 pass, no
    changes needed. Rebuilt the sandbox fresh, re-triggered disk pressure (18.02% free,
    confirmed live) and the job-status mix, and re-ran the full combined suite —
    `RUN_LIVE_SQLSERVER=1 BH_RUN_LIVE_EVALS=1 pytest tests/integration/golden_cases/
    tests/integration/test_skills_execution.py -k "gc_14 or gc_15 or gc_16 or gc_17 or
    governance"` — **17 passed, 0 failed, 5 honestly-skipped**, identical to the prior
    dress-rehearsal result. Confirms this session's fixes (dual-write trace, subscription
    over-broadcast fix, teammate's inbox fix) introduced zero regressions across all 4
    demo points. Sandbox torn down after (`docker compose down -v`).
19. **Real credential-scrubbing gap found + fixed, 2026-07-15 (brightbot PR #846/#847,
    merged develop + staging)**: re-read the spec's own Gherkin scenario "diagnosis text is
    scrubbed before reaching any of 4 sinks" (Slack, NotificationInbox, GitHub PR body,
    audit log) and grepped for `scrub_text` across the whole pipeline-watchdog path — zero
    hits. Confirmed the audit-log sink already redacts via `@audit_action`'s
    `emit_action_audit -> _truncate(_redact=True)`, but `_publish_signals` posts to
    `publishNotification` via raw `httpx`, never wrapped in that decorator — the one sink
    the spec's own requirement never reached. SQL Server's raw `failure_message` and dbt's
    error text flow straight into `diagnosis`/`metadata` and out to all 3 non-audit sinks
    unscrubbed. Fixed by calling `scrub_text()` at signal-collection time in
    `_poll_all_adapters` (`pipeline_watchdog_task.py`) — the single choke point every source
    (dbt, SQL Server) and every downstream sink shares. Added a regression test proving an
    embedded AWS key, JWT, and inline password get redacted while ordinary text (e.g. job
    names) survives untouched. 279/279 governance+dbt_agent unit tests pass, no
    regressions. Merged develop (#846) and promoted staging (#847). All 4 repos reconfirmed
    fully synced.
20. **Cross-repo e2e coverage added for the first time, 2026-07-15
    (brighthive-e2e PR #45, merged to master)**: confirmed `brighthive-e2e` had ZERO Loop
    Capital coverage — grep across the whole repo for "loopcapital"/"GC-1[4-7]" returned
    nothing. The `SSO` blocker the standing directive references turned out to be
    incorrect — `aws sts get-caller-identity --profile brighthive-staging` succeeded via
    access keys, so a real local core WAS bootable against staging's live Neo4j/DynamoDB
    data plane per `RUN_LOCAL_AGAINST_STAGING.md`. Booted `brighthive-platform-core`
    locally (Redis + staging Neo4j creds + a locally-generated `NOTIFICATIONS_API_KEY` +
    the real staging `brighthive-notification-inbox-stg` DynamoDB table), then wrote a real
    GraphQL round-trip test for BH-1067's two watchdog formatters: deliver
    `source_disk_low`/`etl_job_failure` via `notificationRecipients` (the exact call
    `brightbot-slack-server`'s poller makes), read back via the `notifications` query,
    assert the dedicated title/subtitle/detail render — not `formatGenericDisplay`'s
    fallback. This is the first test in the whole repo proving the formatters work through
    the REAL mutation+query wire, not just the isolated unit tests — closes a real gap a
    unit test structurally cannot: GraphQL schema validation, `resolveSignal()`'s registry
    dispatch, and DynamoDB storage all had zero round-trip coverage before this. Both tests
    pass (`2 passed in 7.29s`), self-purging. New spec `SPEC-E2E-NOTIFICATIONS-WATCHDOG-
    PAYLOAD.md` added; `TRACKER.md` regenerated (42 specs / 315 ACs, 100% bound). Local core
    + Redis torn down after; both `brighthive-e2e` and `brighthive-platform-core` restored
    to the branches they were on before this pass (pre-existing in-flight work, untouched).
21. **GC-14's own inbox-detail gap found + fixed, 2026-07-15 (brighthive-platform-core PR
    #1055/#1056, brighthive-e2e PR #46, all merged/promoted)**: while extending e2e coverage
    to GC-14 (the FIRST of Suzanne's 3 demo points), found `dbt_run_failure`'s
    `resolveSignal()` registry entry was category-only (`{category: "dbt"}`) — no
    `display`/`detail` — so it fell through to `formatGenericDisplay` with none of the rich
    `model_name`/`job_id`/`error`/`log_id` detail `brightbot-slack-server`'s Slack formatter
    already reads from the same signal metadata. Exactly the same class of gap already
    fixed for GC-15's two SQL Server stages last cycle — missed there because GC-14
    predates that fix pass and was never separately re-checked. Added
    `formatDbtRunFailureDisplay` + `buildDbtRunFailureDetail`, mirroring the GC-15 pattern
    exactly. New unit test (`notifications-dbt-run-failure-display.test.ts`, 37/37
    notifications suite passes) + a real GraphQL round-trip e2e test
    (`test_notifications_dbt_run_failure_payload.py`, `1 passed in 6.55s` against a local
    core on staging's real data plane, self-purging). Merged develop (#1055), promoted
    staging (#1056), e2e merged to master (#46). All 4 repos reconfirmed fully synced.
    **All 3 of Loop Capital's demo-point signals now render real detail on the inbox** —
    GC-14 (dbt), GC-15's disk-low, GC-15's job-failure — none fall through to the generic
    formatter anymore.
22. **CRITICAL — GC-14's dbt watchdog was completely non-functional in production, found +
    fixed, 2026-07-15 (brightbot PR #848, brighthive-platform-core PR #1057, both merged +
    promoted staging)**: proved by direct run, not speculation — a scheduled watchdog
    principal has `token=None` by design (`_principal_for_workspace`'s own comment:
    "scheduled runs have no user JWT"), but `fetch_dbt_credentials` hard-required a real
    bearer token to call Platform Core's authenticated `workspace` GraphQL query. With
    `token=None`, the watchdog silently returned zero signals and logged "no connected dbt
    Cloud service" — even for a workspace that genuinely has one connected. Fixed
    composably, not with bespoke auth: extended platform-core's EXISTING `x-service-key`
    gate (the same pattern `executeWorkflowAsOwner`/`notificationRecipients` already use)
    with one new read-only query, `getTransformationServicesForScheduledWatchdog`; brightbot
    falls back to it when `token` is absent. **Verified end-to-end against staging's real
    data, zero mocks**: resolves OneTen's real connected dbt Cloud TransformationService
    (`f0d1f30c-…`, "Longaeva POC dbt") with zero user token, real Secrets Manager
    credentials, real GitHub repo. Also caught + fixed a build-breaking mistake mid-pass: the
    first schema edit landed in `schema.graphql`, which is a GENERATED artifact
    (`emit-schema-sdl.ts` writes it FROM `typedefs.ts`) — a real local-server boot caught
    this ("defined in resolvers, but not in schema") before it could ship. Corrected by
    extracting a new `watchdog-typedefs.ts` module (typedefs.ts is already at the 1300-line
    limit) and wiring it into all 3 real assembly points (`server.ts`, `servers/utils.ts`,
    `emit-schema-sdl.ts`).
23. **GC-16 wiring gap found + fixed, 2026-07-15 (brightbot PR #850, merged + promoted
    staging)**: `remediation_agent_graph` (GC-16's surgical-PR loop) had ZERO callers outside
    its own tests — confirmed by grep across the whole codebase. GC-14 (watchdog detection)
    and GC-16 (remediation) were two completely disconnected LangGraph assistants; a real
    dbt failure could be detected and alerted on forever without ever triggering a fix
    attempt. This directly contradicted the spec's own invariant ("DATA_SHAPE root cause
    routes to the existing surgical-PR loop"). Fixed by adding an `attempt_remediation` node
    to the watchdog graph that invokes the SAME compiled `remediation_agent_graph` in-process
    (mirrors `analyst_ask.py`'s pattern for `deep_agent_graph` — both graphs run in the same
    brightbot process, no LangGraph SDK round-trip needed). GC-17's auto-merge exclusion is
    re-checked at this exact runtime call site — the one place remediation can be triggered
    autonomously — not just trusted from an earlier test run. 4 new tests + 6 existing
    assertions updated; 312/312 golden-case + governance + dbt_agent tests pass, 0 failed.
    **The demo's full "detect → fix" narrative for GC-14→GC-16 is now real, not manual-only.**
24. **End-to-end proof of the watchdog→remediation wiring added, 2026-07-15 (brightbot PR
    #852/#853, merged + promoted staging)**: last cycle's `attempt_remediation` node was unit
    tested in isolation, but nothing proved the FULL pipeline — a watchdog-detected failure
    reaching remediation and producing a real PR — through both real compiled graphs
    together. Found this gap by re-running the existing GC-14 full-graph test and noticing
    it now silently exercises `attempt_remediation` with zero assertions about it. Added that
    assertion, plus a new GC-16 test (`test_gc_16_watchdog_detection_actually_triggers_this_
    graph`) driving the REAL `pipeline_watchdog_task_graph` (poll → publish →
    attempt_remediation) end-to-end into the REAL `remediation_agent_graph` — proves a
    watchdog-detected schema-drift failure gets classified correctly and drafts a real PR,
    with only the LLM/GitHub network boundary mocked. 313/313 golden-case + governance +
    dbt_agent tests pass (up from 312). All 4 repos reconfirmed fully synced.
25. **Remediation-boundary safety test added, 2026-07-15 (brightbot PR #854/#855, merged +
    promoted staging)**: verified GC-15's two SQL Server stages (`etl_job_failure`,
    `source_disk_low`) are correctly `RootCauseClass.JOB_RUNTIME` at the source (confirmed by
    code read of both `dbt_pipeline_source.py` and `sql_server_pipeline_source.py`), matching
    the spec's own invariant ("Surgical PRs remain exclusive to DATA_SHAPE signals"). This
    boundary was structurally correct in code but had NO test pinning it at the watchdog
    level — a future regression could silently start feeding unclassifiable job-runtime
    errors into the remediation loop's LLM call on every SQL Server failure with nothing to
    catch it. Added a regression test proving SQL Server signals never populate
    `published_dbt_failures`, the exact gate `attempt_remediation` checks. 314/314 tests
    pass. All 4 repos reconfirmed fully synced.
26. **Tracker scope fixed + Jira brought current, 2026-07-15**: `poc.yaml`'s `repos:` list was
    missing `brightbot-slack-server`, `brighthive-webapp`, and `brighthive-e2e` — all 3 had
    substantial work land this session but were invisible to `make poc-tracker-no-slack`.
    Fixed; linked PR references went 48→57 once all 6 repos were scanned. Posted accurate,
    PR-linked status comments to BH-1043, BH-1047, and BH-1067 in Jira — flagged that
    BH-1067 conflates a shipped 60% (Loop Capital's 3 real stages: dbt_run_failure,
    etl_job_failure, source_disk_low — all fully done across Slack + webapp + inbox +
    e2e) with a genuinely-blocked 40% (3 Databricks/staleness stages with no connector or
    detection-side signal source yet), recommended re-scoping.
27. **Final full dress rehearsal, 2026-07-15 — 18/18 passed, 0 failed**: fresh sandbox
    rebuild, disk pressure + job-status mix re-verified real, then
    `RUN_LIVE_SQLSERVER=1 BH_RUN_LIVE_EVALS=1 pytest tests/integration/golden_cases/
    tests/integration/test_skills_execution.py -k "gc_14 or gc_15 or gc_16 or gc_17 or
    governance"` — 18 passed (up from 17 two cycles ago — the new watchdog→remediation
    e2e test now included), 0 failed, 5 honestly-skipped (live dbt Cloud/GitHub sandbox
    cases). Every demo point, the safety gate, and the new auto-trigger wiring all pass
    together in one real run. Sandbox torn down after. **Loop Capital's POC engineering
    surface is demo-ready for 2026-07-17** — code, tests, staging promotion, cross-repo
    e2e coverage, and Jira status all consistent with reality. Remaining open items
    (multi-connection disambiguation, live workspace validation, Databricks stages) are
    all correctly documented, non-code, or explicitly out of scope — not gaps in what
    shipped.
28. **Correction + real progress on Open Blocker #5, 2026-07-15**: entry 27's "demo-ready"
    framing was called out, correctly — a sandbox I built passing tests is NOT the same claim
    as "Loop Capital's demo is ready," and there was no live Loop Capital workspace behind any
    of that verification. Re-checked Blocker #5 directly: still zero workspaces matching
    "loop"/"loopcapital" in STAGE or PROD. Tried the real GraphQL `createWorkspace` mutation —
    found it exists as a full resolver (~700 lines, complete org/admin-group/policy tree) but
    was NEVER wired into `type Mutation` (confirmed: `Cannot query field "createWorkspace"`).
    Fixing the wiring (brighthive-platform-core PR #1060, merged develop + staging) surfaced 2
    MORE real bugs in the same dead code, both confirmed by direct run against real staging
    data: (1) `OrganizationNode.domain` is required+unique with no input surface on
    `CreateWorkspaceInput` — derived from the owner's email domain; (2) the owning member's
    workspace-role edge is created `PENDING` by design (the normal invite flow) but nothing in
    this path ever flips it `ACTIVE`, so `@authorized`'s `findWorkspaceRoleByUserId` (filters
    `edge:{active:ACTIVE}`) never found the owner — they were 403'd on their OWN workspace.
    Added `activateUserAsAdmin` (SystemAdmin-only, mirrors `confirmUser`'s own update exactly)
    for the demo identity's Cognito password already having been force-set with no confirm-flow
    challenge session left. **Verified against the REAL deployed staging API** (not local):
    workspace `e3fc0917-03a6-4ac6-aad4-ac265329bfb9` ("Loop Capital") exists, real member login
    succeeds, real authorized `workspace` query succeeds — the actual production authorization
    path, not a bypass. New unit tests (`workspace-lifecycle.test.ts`, 4/4 pass); 33/33 across
    all previously-verified suites, zero regressions (48 pre-existing unrelated failures
    confirmed identical to clean develop). **What this actually closes**: Loop Capital now has
    a real, usable, staging-provisioned workspace and a real login. **What it does NOT close**:
    no real Loop Capital SQL Server (BYOW) connection is wired into it yet — that's the next
    concrete step, not "done."
29. **Real SQL Server EC2 CDK stack written, NOT deployed, 2026-07-15 (agentic-project-mgmt
    PR #108, draft)**: user's explicit ask — a real EC2 running Microsoft SQL Server, not a
    local Docker sandbox. First checked `brighthive-admin`'s actual provisioning model: EVERY
    workspace gets its own dedicated new AWS account (7 CDK stacks, Cognito, Neo4j entity,
    welcome email — the real paying-client onboarding factory). Stopped short of running that
    unilaterally — flagged it as a materially bigger, harder-to-reverse organizational action
    than the ask, even with prior go-ahead, because neither of us knew its true size when that
    go-ahead was given. Scoped down to what was actually confirmed: one isolated, easy-to-
    tear-down EC2 instance in the EXISTING shared STAGE account, running the SAME
    `mcr.microsoft.com/mssql/server:2022` image the local sandbox already uses.
    `clients/trials/loopcapital/infra/` — new standalone CDK app (Python, matching the org's
    IaC pattern), `cdk synth`/`cdk diff` both run clean against REAL staging
    (`vpc-0aeee7c16439b5d79`, account `873769991712`) — 4 new resources, no drift. **Not
    deployed** — two things deliberately left as blocking TODOs, not silently assumed done:
    (1) the security group's ingress CIDR is a dead-end placeholder (`127.0.0.1/32`, never
    `0.0.0.0/0`) pending platform-core's real known source; (2) SQL seeding via
    `sandbox/sql/*.sql` is stubbed (`SEED_PENDING` marker), not yet wired as a CDK asset.
    Opened as a **draft** PR deliberately — `cdk deploy` creates real, billable AWS
    infrastructure and needs its own explicit sign-off before it runs, separate from this
    review. **This is the honest current state**: infra is written and reviewable, nothing
    billable has been created yet.
30. **Both remaining TODOs from entry 29 closed, 2026-07-15 (same PR #108, still draft)**:
    (1) the security-group placeholder was resolved by explicit user confirmation to open
    1433 to `0.0.0.0/0` — brightbot deploys on LangGraph Cloud (managed SaaS, no published
    static egress CIDR), so there was genuinely no real source to scope to. Compensating
    control: the SA password is no longer a hardcoded literal (which would have undermined
    the whole justification) — it's a real 32-character secret generated by Secrets Manager
    at deploy time, fetched at boot via an IAM policy scoped to only that one secret's ARN
    (confirmed via `cdk synth`, no wildcards). (2) SQL seeding is no longer stubbed — the
    entire `sandbox/` directory (the proven, real `setup.sh` + `reset.py` + `fill_disk.sh`)
    is uploaded as a CDK asset and run for real on boot, not reimplemented in user-data
    (which would have drifted from the proven local version). `cdk synth`/`cdk diff` both
    still run clean against real staging. **The stack is now complete end-to-end — network,
    credentials, seeding — nothing left but the explicit `cdk deploy` sign-off itself**,
    which remains a separate decision for whoever owns AWS spend, not mine to make
    unilaterally.

## Open Blockers

| # | Blocker | Owner | Raised | Resolved |
|---|---|---|---|---|
| 1 | BH-1057 SQL Server fixture not provisioned | Kuri | 2026-07-10 | **2026-07-13** — Docker sandbox built + verified, replaces AWS RDS plan |
| 2 | BH-1044 Databricks storage-model decision (brightbot-only secret vs. platform-core schema change) — recommendation made, not confirmed. **CORRECTED 2026-07-12 (pass 7)**: this decision alone does NOT unblock Databricks work — confirmed zero Databricks connection code exists anywhere in brightbot/platform-core (both repos' warehouse-type enums are closed to redshift/snowflake/azure_synapse/postgres); a new connector + enum members + Unity Catalog system-schema enablement are ALSO required, independent of where credentials live | Kuri | 2026-07-10 | — |
| 3 | BH-1047 code-level auto-merge exclusion not yet built | Kuri | 2026-07-10 | **2026-07-15** — `REMEDIATION_TOOLS` merged (brightbot PR #813); GC-16 remediation loop itself merged (PR #829), on `develop` + `staging` |
| 4 | Client's original "resource costing / cost management" ask (`poc-scope-from-client.md:33`) has no ticket, spec section, or tracked deliverable — confirm whether already delivered out-of-band (sales-side cost proposal) or a real engineering gap | Kuri/Suzanne | 2026-07-12 | — |
| 5 | **Escalated 2026-07-15**: not just "confirm connection count" anymore — `dynamo-vault search "loop"/"loopcapital"` returns **zero workspaces in STAGE or PROD**. Loop Capital has no provisioned real workspace at all. 7/17's demo must run against a synthetic/sandbox workspace — confirm that's the plan, since BH-1043/BH-1045's watchdogs both need a real `workspace_id` to poll. | Kuri | 2026-07-12 | **2026-07-15** — a synthetic "Loop Capital" workspace (`e3fc0917-03a6-4ac6-aad4-ac265329bfb9`) now exists in REAL staging, created via `createWorkspace` (found + fixed: the mutation existed but was never wired into the schema — see overview entry below). Real member login + real authorized workspace query both confirmed against the live deployed staging API, not a local server. Still not a real Loop Capital SQL Server connection — that's the next real step (wire a BYOW MySQL/SQL Server connection into this workspace) — but the workspace itself is no longer the blocker. |
| 6 | Cooldown/retry-storm suppression (Invariant 3) had zero code — confirmed by grep, not assumed. Real risk of duplicate Slack alerts on a flapping job or persistent low-disk condition. | Kuri | 2026-07-15 | **2026-07-15** — `pipeline_alert_cooldown.py` built (4-tuple key, DynamoDB + in-memory adapters), wired into `_publish_signals`, merged (brightbot PR #835), on `develop` + `staging` |

## Decision

_Filled after 2026-07-17._

**Outcome**: TBD

**Rationale**: TBD

**Next Steps**: TBD
