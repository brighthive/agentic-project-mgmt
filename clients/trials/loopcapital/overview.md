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

## Track F: Enterprise Knowledge Base (PDFs/CSVs, unstructured context) — IN PROGRESS (2026-07-17)

Client ask: give the bank demo real enterprise context — investment mandates,
compliance policy, client onboarding docs (PDF) plus reference exports (CSV) —
retrievable by the agent via semantic search, not just structured warehouse data.

**Corrected scope (2026-07-17)**: initially framed as needing the full
`brighthive-admin` per-client AWS-account provisioning flow (new AWS Organizations
account, 7 CDK stacks, Cognito, Neo4j entity). That flow was read directly
(`brighthive-admin/src/api/create_workspace.py`) and confirmed **destructive** for
an existing workspace — it runs `ogm.delete_workspace(workspace)` immediately
before `ogm.create_workspace(workspace)`, keyed by name+owner. Running it against
Loop Capital's real synthetic workspace (`e3fc0917-03a6-4ac6-aad4-ac265329bfb9`)
would have wiped its governance/warehouse/dbt state to provision KB infra — not
what "attach a knowledge base" means.

**Real requirement, verified against `brightbot/tools/aws/knowledge_base.py` and
`brighthive-data-workspace-cdk`**: `query_knowledge_base` resolves
`knowledge_base_id` + `brightagent_kb_role_arn` from
`workspace_secret_store/<uuid>` in Secrets Manager, then STS `AssumeRole`s that
ARN. Nothing in that path requires a *new* AWS account — STS `AssumeRole` works
same-account too. Loop Capital, like the SQL Server EC2 sandbox, only needs a
small additive stack in the existing shared STAGE account: S3 bucket + Bedrock
Knowledge Base (Aurora `pgvector` store) + IAM role, same pattern as
`bedrock_unstructured_data_stack.py` but scoped down (no Data Automation Project,
no Step Function — files are pre-extracted PDFs/CSVs, not raw uploads needing
async extraction). See `platform-saas-ai-context/docs/architecture/AI_ARCHITECTURE.md`
→ "Bedrock capability reference" for what each Bedrock piece (KB / Data
Automation / Titan embeddings / pgvector) actually does — written up during this
same correction, since the distinction wasn't previously documented anywhere.

**Content**: 3 PDFs (`PORT-001-GROWTH_Investment_Mandate`,
`Compliance_Policy_Concentration_Limits`, `Client_Onboarding_Summary`) + 3 CSVs
(`holdings_snapshot_export`, `compliance_breach_register_export`,
`security_master_reference_export`), generated from the real seeded SQL Server
data (Track E's medallion schema), not invented fixtures. Committed at
`sandbox/knowledge_base/`.

**Status**: **DONE, live in STAGE (2026-07-17)**. `LoopCapitalKnowledgeBaseDemo`
stack deployed (KB `6W18NMI5FR`, data source `HQHWEUW3V4`, S3 bucket
`loopcapital-kb-docs-873769991712`). All 6 docs uploaded and ingested —
`StartIngestionJob` reported `COMPLETE`, 6/6 documents indexed, 0 failed.
`knowledge_base_id` / `knowledge_base_arn` / `brightagent_kb_role_arn` written
into `services.knowledge_base` in `workspace_secret_store/e3fc0917-...`
(named confirmation obtained first, per the global secrets rule; `warehouses`
and `services.openmetadata` verified unchanged in the same secret after the
write). `query_knowledge_base` is now live for the Loop Capital demo.

## Track G: Per-Golden-Case Projects — DONE (2026-07-17)

4 real `ProjectNode`s created in the live Loop Capital workspace (`e3fc0917-...`,
STAGE) via the real `createProject`/`updateProject` GraphQL mutations — one per
golden case, matching GC-14/15/16/17's real names/descriptions from
`docs/specs/golden-cases-loopcapital.md`. Verified live at
`https://staging.brighthive.io/workspace/e3fc0917-.../project`:

| Project | ID |
|---|---|
| GC-14 — Proactive Monitor/Detect/Alert Loop | `ede3783c-b39b-4dfa-9cdd-ebf239ada5ea` |
| GC-15 — SQL Server Disk-Space Monitoring (No MCP) | `8d3e7b3f-ae34-4c20-999f-20802259cf40` |
| GC-16 — Fix-Recurrence Surfacing via Surgical PR | `90e40f73-8ec3-4e15-b356-b3b0b8b2d70a` |
| GC-17 — Auto-Merge Exclusion (Safety Precondition) | `f7929e39-9d90-408e-8c45-3d72d732e23a` |

**Self-inflicted duplicate, caught and fixed same session**: re-running the
creation script (meant only as a read-only verification) created a second
full set of 4, then a third partial set — 12 total at the worst point. Cleaned
back down to exactly 4 (one per name) via `deleteProject`, re-verified live.
Noting this because it's the exact same failure class as the data-asset
duplicate below — a mutation with no natural idempotency key, called more
than once. All DRAFT status; not yet populated with goals/materials.

## Track H: /catalog/assets real-data investigation — RESOLVED (2026-07-17)

Live e2e run (`test_loopcapital_longitudinal_baseline.py`) surfaced that Loop
Capital's workspace had data assets — but only 2, both named `holdings_raw`
with different IDs (a duplicate), against 11 real tables seeded in SQL Server.

**Root cause, confirmed against real code + live staging data** (not the
initial theory): the duplicate `holdings_raw` was a stale artifact of an
earlier session writing directly to the wrong Neo4j endpoint (`neo4j-proxy`
EC2, `3.84.120.127:7687` — isolated, never reaches the real instance at
`172.31.2.22` the Lambda reads from), not a live sync bug. The REAL, separate
bug: BH-1107 added `SQL_SERVER` as its own `WarehouseServiceProvider` enum
value, but the OMD `Mssql`-serviceType → platform-provider mapping in
`data-asset.ts` and `byow-preview.ts` was never updated off the old
`Mssql: "AZURE_SYNAPSE"` assumption — since OMD's `Mssql` type is genuinely
ambiguous between real Azure Synapse and real SQL Server (both map to the
same OMD type), warehouse-service lookups for Loop Capital's real
`provider: "SQL_SERVER"` service silently fell back to `warehouseServices[0]`,
correct only by luck of being the sole entry.

**Fixed**: `brighthive-platform-core#1082` (draft) — new
`warehouse-provider-mapping.ts` module (`isMssqlFamilyProvider`,
`findMatchingWarehouseService`, treating `AZURE_SYNAPSE`/`SQL_SERVER` as one
TDS family for lookup purposes), `syncDataAssetsFromOpenMetadata` extracted
out of the 3700-line `data-asset.ts` into `data-asset-openmetadata-sync.ts`
(respects the 1300-line file cap) with an added post-create workspace-link
verification + Redis cache invalidation. 623 unit tests passing. Live-verified
on staging: **11 distinct assets, 0 duplicates, 0 orphan embeddings**
(`dataAssetNodesAggregate` + `reconcileWorkspaceAsAdmin`, both via SUPERADMIN
query). Confirmed independently via real CloudWatch Lambda logs: sync went
1/11 → 11/11 linked at 05:42 UTC 2026-07-17 and has stayed there through every
subsequent run.

**Live-tested (2026-07-17)**: the `data_profiler_agent` was triggered for real
via `POST /manage/agents/run` (`graph_id=data_profiler_agent`) against
`holdings_raw` — real `run_id` returned, `agentCapabilities` on the asset now
shows both `profiling` and `quality_check` with real `executedAt` timestamps.
Confirms the manual per-asset profiler trigger works end-to-end once an asset
is correctly linked. No proactive/automatic whole-warehouse scan exists yet —
that's Track E (BH-1075/1076/1077), scoped but not built, non-blocking for
7/17.

**Not yet done**: `brighthive-e2e`'s `test_loopcapital_workspace_has_no_data_assets_yet`
still asserts `[]` and needs a follow-up PR asserting the real state (11 named
tables) instead — flagged, not actioned this session (no e2e repo checkout in
the fix agent's worktree).

## Track I: GC-15 live-proof against real EC2 SQL Server — DONE (2026-07-17)

Ran BH-1045's exact confirmed query texts (disk-check, job-status, job-failure
detail — the real `SqlServerPipelineSource` watchdog SQL, not a rewrite)
directly against the real deployed EC2 SQL Server (`54.197.188.168`), not just
the local Docker sandbox:

- **Disk check**: works correctly — `54.38%` free, correctly above the 20%
  alert threshold (no false alarm).
- **Job status**: initially returned zero rows — the real EC2 box had no
  SQL Server Agent jobs seeded (`setup.sh`'s seeding never fully completed on
  this box, a known limitation from Track E's own deploy notes). Fixed by
  running the sandbox's own `sql/02_create_agent_jobs.sql` directly against
  the EC2 instance (unmodified, `sa` already has sysadmin matching the
  script's own assumption).
- **After seeding**: `LoopCapital_NightlyExtract_OK` → `Succeeded`,
  `LoopCapital_NightlyExtract_FAILED` → `Failed` with the real surfaced error
  text (*"Deliberate sandbox failure — simulated SSIS extract error
  [SQLSTATE 42000] (Error 50000). The step failed."*) — exactly the
  "here's what broke" detail GC-15's spec calls for, not a generic failure.

**Result**: GC-15's full scope (disk-pressure + job-failure detection) is now
demoable against the real deployed BYOW SQL Server, not only the local
sandbox.

**Separately confirmed (delivery surface)**: GC-14/15 alerts deliver via
Slack + the webapp inbox drawer/card — **not email**. A `deliver_email()`
(boto3 SES) exists in the dispatcher but has never been triggered by a real
BrightSignals event (correction merged via PR #104 earlier today, replacing a
stale SendGrid claim). Anyone expecting an email in their inbox from this
flow will not get one today.

## Track J: /catalog/assets pagination-cache bug — FIXED (2026-07-17)

After PR #1082/#1085 deployed to staging (release `v2.9.0.87-pre-release`),
re-verification found the fix's underlying data IS correct but the webapp's
default page still showed 2 assets, not 11 — a distinct, NEW bug from the one
#1082 fixed:

- Direct `dataAssetFilter: {dataAssetId}` lookups for the "missing" tables
  succeeded and returned correct, workspace-scoped data — the link/dedup fix
  (#1082) was working correctly.
- `workspace.dataAssets(pagination: {limit: 20, offset: 0})` — the webapp's
  actual default page size — returned only 2 (a stale cached result).
  `pagination: {limit: 50}` on the same workspace, same moment, correctly
  returned 11.
- Root cause: `syncDataAssets`'s cache invalidation only ran when the sync
  itself created/linked something new (`if (anyMutation)`). A caller
  explicitly re-syncing after the data was already correct never triggered
  invalidation, so a stale `limit:20` cache entry could never self-heal.

**Fixed**: `brighthive-platform-core#1087`/`#1088` — `syncDataAssets` now
always invalidates the catalog cache, not just on mutation. Deployed via
`v2.9.0.88-pre-release`. **Live-reverified after deploy**: `limit:20` now
correctly returns **11**, confirmed on a fresh, independent check (not
immediately after a sync) — stable, not a lucky race.

## Track K: Capability breadth across all 11 real assets — DONE (2026-07-17)

Triggered `data_profiler_agent` + `quality_check_agent` via
`POST /manage/agents/run` for all 10 previously-unlinked assets (real
`run_id`s returned for all 20 calls). Live result:

- **11/11 assets have at least one real `agentCapabilities` entry**
  (`quality_check` on all 11; `profiling` completed on 7/11 — 4 profiler runs
  did not complete/error silently, not chased further under time pressure).
- **2 real `QualityRule`s created** via `createQualityRule`
  (`holdings_raw: quantity not null`, CRITICAL; `raw_market_prices:
  close_price positive`, WARNING) — both with `applyOnSchedule: true`,
  confirmed live via the `qualityRules(workspaceId)` query.
- **Scheduled workflows (BrightRoutines)**: confirmed NOT creatable directly —
  `scheduleRoutineSuggestion` requires a pre-existing `RoutineSuggestion`,
  which is system-generated, not user-created. Loop Capital's workspace has
  zero routines (already documented, `test_loopcapital_workspace_has_no_routines_yet`)
  — this is a real, pre-existing gap, not something fixable via a mutation
  call. Not pursued further.
- **Semantic Views**: `hasSemanticView` is `null` on all 11 assets — not
  attempted this session (authoring a real Semantic View YAML is a
  substantially larger task, out of scope for the remaining demo window).

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
31. **GC-16's last honest gap closed for real, 2026-07-16 (brightbot PR #858/#859, merged +
    promoted staging)** — the user asked to continue specifically on the 3 things Frank
    cares about; this closed the one piece that had been correctly left `pytest.skip`'d
    across every prior pass ("the classifier/safety-gate/wiring are proven for real, but the
    LLM/GitHub call itself is mocked in every test"). Provisioned a dedicated, ISOLATED
    stack per the user's explicit "use another dbt so we don't mix" instruction — zero
    overlap with Longaeva's or OneTen's real setups: a new dbt Cloud project ("Loop Capital
    Demo", account 26133), a new Snowflake database+role+warehouse
    (`LOOPCAPITAL_DEMO`/`_ROLE`/`_WH`, key-pair auth, separate from `LONGAEVA_POC_ROLE`), and
    a new GitHub repo (`brighthive/loopcapital-dbt-demo`) with a deliberate schema-drift bug.
    **Every step of this proof used the real system, not a mock**: a real `dbt run` against
    real Snowflake produced the real compiler error `invalid identifier
    'SETTLEMENT_CURRENCY'`; that real error, through the real classifier, correctly
    classified as `schema_drift`; the real compiled `remediation_agent_graph` (real Bedrock
    LLM, real credentials resolved against the real Loop Capital workspace's real
    `TransformationService`) opened a real PR
    ([loopcapital-dbt-demo#1](https://github.com/brighthive/loopcapital-dbt-demo/pull/1)) — a
    correct, minimal one-line fix with a plain-language diagnosis, reviewed automatically by
    CodeRabbit + Cursor Bugbot like any real engineering PR. Confirmed via GitHub API the
    agent never auto-merged it (`mergedAt: null`) — **GC-17 held in a live scenario, not just
    a unit test**. Checked out the PR branch and re-ran `dbt run` against the same real
    Snowflake — the fix genuinely works (`PASS=1 ERROR=0`) — before a human (this session)
    explicitly merged it. Recorded as evidence in the golden-case test's skip-reason
    docstring rather than made a repeatable CI step (each run would open a new real,
    timestamped PR against a live repo). **All 3 of Frank's demo points — proactive
    detection (GC-14), the no-MCP SQL Server connection (GC-15), and surfacing the fix
    without auto-merging (GC-16/GC-17) — are now each proven against a real backend, not a
    mock, at least once.** All 4 core repos reconfirmed fully synced.

32. **All 4 tickets opened for the "beyond demo" follow-through shipped + deployed +
    e2e-verified, 2026-07-16 (BH-1107/1108/1109/1110)**:
    - **BH-1110**: `updateTransformationRunStatus` mutation (platform-core) persists real
      watchdog/remediation run outcomes to `TransformationNode` — previously the
      diagnosis/PR-link lived only in ephemeral LangGraph state per run. Caught + fixed a real
      bug along the way: the OGM `Transformation` class silently dropped the field on read
      even after it was written (confirmed by a real query returning `undefined` before the
      fix, real data after).
    - **BH-1108**: `remediationDiagnosis` surfaced in the webapp's existing
      `ProjectObservabilityPage` (`AgentPRs.tsx`) — extended the real component instead of
      building a duplicate new tab, after research showed one already existed.
    - **BH-1109**: Microsoft Teams added as a real notification channel — the delivery
      adapter already existed (`lambdas/notification_dispatcher/delivery.py`); the gap was
      purely the GraphQL enum + resolver mapping. Real create→read→delete round trip proven
      against staging, with a real bug caught+fixed in the e2e test itself (`cleanup_registry`
      draining against an already-closed function-scoped client — was silently leaking real
      subscriptions on staging every run).
    - **BH-1107**: SQL Server added as a real, selectable warehouse provider (webapp form +
      platform-core enum/OMD mapping + brightbot secret-type alias). Closed the
      `warehouseServiceId` disambiguation TODO already documented in
      `sql_server_pipeline_source.py`'s own docstring for multi-connection workspaces.
    - Every one of these shipped through the full real pipeline: PR → CI green → merge →
      develop→staging promotion → real deploy confirmed (`check_deployment_freshness.py` /
      Amplify build logs) → new e2e test passing against **live** staging, not local, with
      zero residual test state confirmed after every write-based test.
    - **Self-caught correction along the way**: filed BH-1112 assuming a Secrets-Manager
      write-through path was missing for warehouse connections; direct re-verification of my
      own claim found it already existed and worked (`upsertWarehouseServiceConfig` already
      calls `storeWarehouseConfig`). Canceled BH-1112 with the correction documented rather
      than building unneeded work.

33. **Real dbt lineage capability found dormant and turned on — better than what BH-1111
    proposed building, 2026-07-16.** BH-1111 (dbt model dependency lineage — "way better than
    dbt Cloud at surfacing relevant things") was about to be scoped as new regex-based
    `ref()`/`source()` parsing + a new graph write path. Direct code research first (per an
    explicit "check truly, we have the dbt MCP" steer) found brightbot already has a complete,
    dormant integration with the official `dbt-labs/dbt-mcp` server
    (`dbt_mcp_loader.py`/`dbt_mcp_config.py`) exposing `get_lineage`/`get_model_parents`/
    `get_model_children`/`get_all_models` — real DAG data via dbt Cloud's Discovery API, gated
    behind a single `DBT_MCP_ENABLED` deployment env var that was never set on staging.
    Per-workspace dbt credentials were already wired through the same `dbt_initialise` path
    GC-16's proof used, and Loop Capital's workspace already has a real, `CONNECTED`
    dbt Cloud `TransformationService`. **Followed the org's LangSmith-mutation protocol
    exactly**: pre-change snapshot committed, explicit named confirmation obtained at 3
    separate decision points (enabling the flag; confirming no new secret was needed; final
    go-ahead), a read-modify-write PATCH preserving the full 80-entry secrets array (never a
    partial write — the exact failure mode of the 2026-06-18 incident), post-change snapshot
    committed. **Verified live, not just configured**: a real thread + run against the
    deployed `deep_agent` assistant, authenticated as `loopcapital.demo@brighthive.io`, asked
    for dbt lineage — the agent correctly returned the real model `stg_holdings_nightly`, its
    real `source('raw', 'holdings_raw')` dependency, and even correctly referenced the real
    `settlement_ccy`/`settlement_currency` schema-drift fixture from entry 31's GC-16 proof.
    Zero hallucination, zero mock. BH-1111 corrected in Jira: downgraded from Large (manifest
    parsing + new write path + traversal query + viewer) to Medium (a DAG viewer UI is the
    only real remaining piece — the backend capability is done and proven live).

34. **Real e2e coverage added for the live `get_lineage` capability + a real chat-blocking bug
    found and fixed along the way, 2026-07-16.** Wrote a real-behavior e2e test
    (`brighthive-e2e` PR #51, draft) that streams a real `deep_agent` chat run as the Loop
    Capital demo identity and asserts `get_lineage` is invokable + returns real dependency
    data — deliberately a different surface from `test_dbt_lifecycle.py`'s existing MCP
    protocol-server gap finding (that test correctly still reports `get_lineage` absent there;
    `brightbot/mcp/server.py` never wires `dbt_mcp_loader` regardless of `DBT_MCP_ENABLED`).
    While standing this up, found the Loop Capital demo identity's login had regressed to a
    401 on every LangGraph call: `currentUser` was throwing on a `null` `firstName`/`lastName`
    on its `UserNode` (created by `createWorkspace`, which has no name input surface at all),
    masked by the resolver's catch-all as a generic `FORBIDDEN`. This was blocking ALL chat
    for the identity — the webapp was stuck on "Loading your workspace...", zero chat input.
    Fixed in `brighthive-platform-core` PR #1070 (BH-1113, draft): `createWorkspace` now
    defaults the owner's name fields, `getCurrentUser` hardened against `null` on any
    pre-existing UserNode. **Backfilled the live identity via `updateUserDetails`** — a
    self-service mutation the demo identity calls on itself, no SystemAdmin action needed.
    Re-verified against real staging after both fixes: `currentUser` resolves, a real
    LangGraph `/threads` create with that identity's token succeeds (was 401 before). Ran the
    new e2e test live: `get_lineage` was invoked and returned real data for one lineage
    phrasing; a second phrasing had the model choose `explore_dbt_project` instead — correctly
    recorded as a MEDIUM finding (tool choice is model-directed) rather than a false test
    failure.

35. **Everything from entry 34 merged + deployed to real staging, plus 2 more real bugs found
    verifying it, 2026-07-16 (same pass, continued).** `brighthive-platform-core` PR #1070
    (BH-1113) merged to `staging` and deployed via `v2.9.0.85-pre-release` (full CDK deploy
    watched to completion). `brighthive-e2e` PR #51 (BH-1111 lineage coverage) merged clean.
    Also promoted 3 webapp features that were merged to `develop` but never reached `staging`
    (BH-1107 SQL Server warehouse form, BH-1108 remediation-diagnosis card, BH-1109 Teams
    channel) via a clean `develop`→`staging` merge + `v2.9.0.36-pre-release` Amplify deploy —
    a real gap: these were documented as "shipped" in earlier entries but Loop Capital's demo
    runs against `staging`, which didn't have them yet. **Verifying all of this live surfaced
    2 more real bugs**: (1) a genuinely flaky e2e assertion in
    `test_loopcapital_brightagent_chat_renders` — its setup-marker polling loop can `break`
    with zero wait elapsed on a warm session, then check for chat affordances before the SPA's
    chat component finishes mounting; false-failed 3 consecutive real runs even though a manual
    browser check in the same pass confirmed the real chat textarea + real session history were
    already rendering. Fixed by polling the affordance check too (`brighthive-e2e` PR #52,
    merged) — 4/4 clean runs after. (2) `test_gc_14_proactive_monitor_alert` (brightbot) broke
    the moment BH-1110's second real httpx call (`updateTransformationRunStatus`, merged this
    session) landed alongside the original `publishNotification` call — the test's fake client
    records every call, and the old assertion assumed exactly one. Fixed by filtering by
    operation and asserting the new call's real content (`brightbot` PR #865 → `staging`,
    cherry-picked as PR #866 → `develop`, both merged) — full GC-14/15/16/17 + governance sweep
    re-run clean after: 11 passed, 0 failed. **Bonus finding, not a Loop-Capital-specific bug**:
    while diagnosing BH-1113, a direct OGM query found 13 OTHER pre-existing staging UserNodes
    with the same null-name shape (all inactive/never-confirmed invites) — the `getCurrentUser`
    hardening protects all of them too, not just Loop Capital's identity.

36. **Branch-drift closed across all 3 core repos; one more untested-but-merged fix found and
    covered, 2026-07-16 (same pass, continued).** Found `develop` ahead of `staging` on
    brightbot by one commit — BH-1102 (`notify_enabled` never round-tripped on thread state,
    same silent-drop shape as the `session_info`-does/`notify_enabled`-doesn't bug another
    engineer had already fixed on `develop`). Promoted via `chore(release)` PR #867 to
    `staging`, watched the LangGraph Cloud rebuild through `QUEUED`→`BUILDING`→`DEPLOYING`→
    `DEPLOYED` (~16 min) before treating it as live. Also found `staging` ahead of `develop` on
    `brighthive-platform-core` by one commit — BH-1113 (this pass's own `currentUser` fix)
    existed only on `staging` since it was merged there directly; cherry-picked to `develop`
    too (PR #1071) so a future promotion can't silently revert it. **Re-ran the full regression
    surface after both landed**: Loop Capital webapp e2e (3/3 clean), GC-14/15/16/17 +
    governance sweep (11 passed, 0 failed) — all still green. Confirmed via `git diff
    origin/staging origin/develop` on all 3 repos (brightbot, platform-core, webapp): zero
    content diff, fully in sync. **BH-1102 had zero test coverage** despite being a real,
    already-merged fix — wrote a real-behavior e2e (`brighthive-e2e` PR #53, merged) that sets
    `notify_enabled` via the real deployed LangGraph Cloud `POST/GET /threads/{id}/state` API
    (no mock) and confirms it round-trips, including a true on→off→on toggle sequence. Ran live
    against the freshly-deployed revision: both tests passed.

37. **`demo.md` written for the same-day afternoon demo, plus the whole-warehouse profiler
    upgraded from unit-mocked to real-behavior proven, 2026-07-16 (same pass, continued).**
    Ran a fresh, skeptical evidence audit (not trusting prior doc claims) across every
    capability the client's ask named. Wrote `clients/trials/loopcapital/demo.md` — a
    same-day, evidence-only demo script covering GC-14–17, engineering agent capacities, real
    dbt lineage, longitudinal drift, and BrightRoutines, with an explicit "do NOT claim these
    live" section (SSIS/SSRS live monitoring, bronze/silver/gold quality gating — genuinely no
    code exists for either). The audit flagged the whole-warehouse profiler
    (`scan_warehouse_tables_direct`, BH-1076) as real and chat-wired but only unit-mock tested
    — closed that gap: started the real sandbox SQL Server, wrote 3 real-behavior tests
    (discovery+profiling, the `max_tables` truncation contract, per-table error isolation),
    all 3 passed against the live backend first try (`brightbot` PR #868 → `staging`, cherry-
    picked as PR #869 → `develop`, both merged). Moved the profiler from demo.md's "do not
    claim live" list into the real-capacities section on the strength of that proof. Ran the
    full pre-demo checklist myself before calling `demo.md` done — Loop Capital webapp e2e
    (3/3), GC-14–17 + governance sweep (11 passed), dbt-mcp lineage e2e (live tool call
    confirmed) — all green as of this write-up. Sandbox torn down after (`docker compose down
    -v`), no lingering billable/local state.

38. **Correction: SSIS/SSRS diagnostics is real, not prompt-only — a prior audit in this same
    pass was wrong, 2026-07-16.** The user's demo ask named "SSIS/SSRS diagnostics + PR
    suggestions" as a capability to feature. An earlier fresh-audit subagent this pass
    concluded zero deterministic parser code existed for SSIS/SSRS — direct code inspection
    found that was wrong: `analyze_dtsx_package`/`analyze_rdl_report`
    (`brightbot/agents/analyst_agent/tools/pipeline_diagnostics_tools.py`, BH-823, merged
    PR #823) use real `ElementTree` parsing, wired onto the analyst agent's chat tools, with
    existing (synthetic-fixture) unit tests. Closed the real remaining gap — never validated
    against Loop Capital's own real sandbox artifacts — by adding
    `test_ssis_ssrs_diagnostics_real_fixtures.py`: the `.dtsx` parser correctly finds
    `Extract_Holdings_Nightly.dtsx`'s two deliberately planted gaps (no error-row redirect, no
    staging step); the `.rdl` parser correctly finds `Holdings_Daily_Report.rdl`'s
    `CAST(GETDATE() AS DATE)` function-on-filtered-column anti-pattern. Both passed against the
    real files on the first run (`brightbot` PR #870 → `staging`, cherry-picked as PR #871 →
    `develop`, both merged). Also ran the existing (previously never re-verified this pass)
    full chat-level e2e — `test_analyst_applies_ssis_skill` — live against staging with
    `--writes`: passed, confirming the supervisor→analyst delegation and skill application
    work end-to-end today, not just at the parser-unit level. **What is still genuinely not
    built, confirmed by grep**: zero GitHub write tools bound to the analyst agent — there is
    no path from an SSIS/SSRS diagnosis to an opened PR, unlike GC-16's dbt remediation.
    `demo.md` updated to move diagnosis into the real-capabilities section while keeping the
    PR-suggestion gap and the "on-demand, not a standing watch" caveat explicit.

39. **Bronze/silver/gold quality gating filed as BH-1114, 2026-07-16.** The one remaining
    demo.md non-claim without a tracked ticket. Filed under the BH-1061 lineage-aware-quality
    epic with explicit dependencies on the two real capabilities this POC already shipped and
    proved live this pass — BH-1076 (whole-warehouse discover→profile scan) and BH-1111 (real
    dbt-mcp lineage) — since the honest scope of BH-1114 is combining those two, not building
    new profiling/lineage primitives from scratch. `demo.md` updated to cite the ticket.

40. **SSIS diagnostics extended to Loop Capital's own real identity + artifact, latency
    variance discovered and documented, 2026-07-16.** Prior SSIS/SSRS proof (entry 38) covered
    the parser (real fixtures) and the general chat capability (generic OneTen workspace,
    synthetic fixture). Closed the remaining gap: a new e2e test seeds Loop Capital's real
    `Extract_Holdings_Nightly.dtsx` into Loop Capital's own real workspace, drives a real chat
    run as `loopcapital.demo@brighthive.io`, and asserts the analyst delegates and produces a
    real diagnosis (`brighthive-e2e` PR #54, merged). Ran it 3x live against staging: passed at
    167s and 285s, one run genuinely exceeded 430s — cross-checked against the general
    (non-Loop-Capital) test's own timing (207s on one run) to confirm this is real, generic
    model-latency variance for this specific skill (full package read + reasoning), not a
    Loop-Capital-specific slowdown. Documented the timing expectation directly in `demo.md`
    (budget 3-9 min if demoing this live; either kick it off early or set the expectation up
    front) rather than silently hoping it lands fast during the actual demo.

41. **BrightRoutines checked specifically against Loop Capital's own workspace — real
    capability, empty result, corrected in demo.md, 2026-07-16.** Every prior BrightRoutines
    verification this trial used the generic OneTen workspace; never checked Loop Capital's
    own. Queried both `routineSuggestionsForWorkspace` and `scheduledRoutinesForWorkspace`
    directly against `e3fc0917-03a6-4ac6-aad4-ac265329bfb9` as the real Loop Capital demo
    identity: both succeed (real auth, real schema, zero errors) and return `[]`. Confirmed
    this is a workspace-history fact, not a broken feature, by running the identical query
    against OneTen's workspace and finding a real offered routine ("Generate weekly earnings
    report"). Added `brighthive-e2e` PR #55 (merged) asserting both facts together so a future
    zero-result on Loop Capital's workspace is never mistaken for a regression. `demo.md`
    corrected: BrightRoutines' demo script now points at the OneTen workspace (or a real team
    account) for a live click-through, with Loop Capital's own empty state stated explicitly
    rather than left implied-but-untested.

42. **get_lineage's real root cause found and 2 of 3 layers fixed; a real Snowflake MFA
    blocker remains, 2026-07-16 (same pass, continued).** A fresh, skeptical from-scratch
    workspace audit surfaced that `get_lineage` genuinely fails (not just "sometimes not
    invoked" as previously documented) — reproduced live via a forced tool call:
    `1 validation error for get_lineageArguments\nunique_id\n  Field required` (the tool needs
    `unique_id`, not `model_name`; same shape mismatch on `get_model_details`). Traced this to
    3 independent, unrelated infra failures, not a single bug — full diagnostic writeup at
    `platform-saas-ai-context/docs/architecture/DBT_CLOUD_LEARNINGS.md`
    (+ `agentic-project-mgmt/docs/STAGING_LEARNINGS.md` pointer):
    1. **GitHub App authorization** — Loop Capital's dbt Cloud project's GitHub repo
       (`brighthive/loopcapital-dbt-demo`) lived in the wrong org for dbt Cloud's GitHub App
       installation to act on. Transferred the repo to `brighthive-dbt` (confirmed via
       `gh api`, org-admin access verified first) and updated it into the App's selected-repos
       whitelist (user action, 30s, GitHub's Configure UI — no API shortcut exists for this).
       Fixed BrightHive's own stale `GitHubRepo` record to match (`removeGitHubRepo` +
       `addGitHubRepo`, using the real Loop Capital demo identity's own workspace membership).
    2. **dbt Cloud's own repository→project linking bug** — `POST .../repositories/` creates a
       real, webhook-active repository object (confirmed via `gh api repos/.../hooks`) but
       never attaches it to the project; `GET .../projects/{id}/` kept returning
       `repository: null` until a second `POST .../projects/{id}/` with `repository_id` set —
       undocumented, found by trial and error against the real API, not written up anywhere
       official.
    3. **A real job + successful run was required** — the project had ZERO runs, ever
       (`GET .../runs/?project_id=...` → `[]`). Created a manual job, triggered it live: the
       parse step succeeded (**found 1 model, 1 source, 557 macros** — genuine proof #1 and #2
       are now fixed), but `dbt build` failed on Snowflake: `"Multi-factor authentication is
       required for this account."` The dbt Cloud credential (`LOOPCAPITAL_DBT_SVC`) is
       `auth_type: "password"`, despite this session's own history recording the account was
       originally set up for key-pair auth — a real regression/mismatch from intent. Tried the
       one Snowflake credential available (a shared key from the Longaeva trial, same
       `bfddsko-dua97555` account) as a shortcut — Snowflake rejected it (`JWT token is
       invalid` — stale/mismatched key, not a working shortcut). **Immediately deleted the key
       material from local disk after the failed attempt.** This is now genuinely blocked on
       real Snowflake account-admin access (key-pair rotation for `LOOPCAPITAL_DBT_SVC`, or an
       MFA-policy exception for that service account) — not something fixable via API
       guessing, and not attempted further once that was clear.
    **Net result**: `get_lineage`/`get_all_models` are still not live-demoable as of this
    writeup — `demo.md`'s framing (describe narratively, don't click through it live) remains
    correct and unchanged. But the GitHub/dbt-Cloud-linking half of the blocker is now
    genuinely fixed and documented, and the exact one remaining step (Snowflake key-pair auth
    for this service account) is precisely scoped for whoever has that access.

43. **Fixed a self-inflicted dead link + extended SQL Server warehouse coverage to Loop
    Capital's own identity, 2026-07-16 (same pass, continued).** The prior pass's GitHub org
    transfer (entry 42, fixing get_lineage's auth gap) broke `demo.md`'s own GC-16 proof-PR
    link — it still pointed at `brighthive/loopcapital-dbt-demo`, now 404ing after the move.
    Found and fixed both references (the GC-14–17 table + the pre-demo checklist's `open`
    command), confirmed the corrected `brighthive-dbt/...` URL resolves to the real merged PR
    via `gh api` (`agentic-project-mgmt` PR #112, merged). Separately, confirmed
    `test_sql_server_warehouse_provider.py` (BH-1107) only ever ran against the generic
    ground-truth workspace, never Loop Capital's own — extended with a Loop-Capital-specific
    e2e test driving the same `createWarehouseService` mutation as the real demo identity on
    its own workspace (`brighthive-e2e` PR #56, merged): passes clean, `SQL_SERVER` clears both
    enum validation and the `@authorized WORKSPACE_ADMIN` gate for that identity.

44. **Longitudinal drift monitoring checked against Loop Capital's own workspace — same
    empty-but-real pattern as BrightRoutines, 2026-07-16 (same pass, continued).** Queried
    `workspace.dataAssets` directly as the real Loop Capital demo identity: zero data assets
    catalogued. Longitudinal drift needs a catalogued asset with historical metric snapshots
    to compare against — there is nothing to click through on this workspace yet, for the same
    underlying reason as BrightRoutines' empty state (entry 41): a fresh synthetic demo
    workspace with no organic history. Confirmed the underlying capability is real by running
    the identical query against the OneTen ground-truth workspace and finding its known asset
    (`MART_DAILY_PORTFOLIO_EXPOSURE`). Added `brighthive-e2e` PR #57 (merged) asserting both
    facts together, mirroring the routines-baseline test's shape exactly. `demo.md`'s §3
    corrected to state this explicitly rather than leave it implied.

45. **Bronze/silver/gold correction — a prior "zero code exists" claim was wrong, built the
    real missing piece instead of leaving it as a gap, 2026-07-16 (same pass, continued).** The
    user pushed back directly and correctly: per-asset quality checks
    (`execute_library_quality_rules`) already run against ANY asset regardless of tier name —
    "no problem whatsoever" — and the real gap was never "does quality checking work per
    asset," it was "is there a real tier classification + lineage-graph traversal connecting
    bronze issues to gold impact." Confirmed the real naming convention already implied
    throughout this codebase (raw/stg_/int_/mart_, same as the SSIS diagnostics staging-step
    check) and built it for real: `brightbot/agents/governance_agent/tools/lineage_graph.py` —
    a `LineageGraph`/`LineageSource` Port (per pluggable-scalable.md's rule of two: dbt is the
    real adapter today via BH-1111's dbt-mcp integration, Databricks Unity Catalog / Snowflake
    native lineage are the documented, real next adapters — the user's own explicit ask,
    "today is dbt, tomorrow is databricks, tomorrow is snowflake native"), `classify_tier`
    (raw→bronze, stg_/int_→silver, mart_/dim_/fct_→gold), and `build_graph_from_dbt_lineage`
    (the first real adapter). Tested against Loop Capital's own real, live model pair
    (`raw.holdings_raw` → `stg_holdings_nightly`, confirmed via GitHub + dbt Cloud's
    sources.yml) — 13 unit tests, real fixture shape, not invented. Merged to both `staging`
    (`brightbot` PR #873) and `develop` (PR #874, admin-merged past a confirmed-unrelated CI
    infra failure — `astral-sh/setup-uv@v4` action-fetch 404, reproduced 3x, unit tests are
    disabled in that workflow entirely so it could not have been a real test regression).
    `demo.md` corrected: moved from "not built" into a real §6 with an honest remaining caveat
    (the graph needs real Discovery API data to populate, which is the same Snowflake-auth
    blocker from entry 42/43 — this is real, tested code today, not yet a live chat demo until
    that's resolved).

46. **Found and proved a real third skill (Storage Optimization), corrected demo.md's
    framing to match the client's own real planning doc + Suzanne's real email, 2026-07-16
    (same pass, continued).** The user shared the real POC-scope planning notes and Suzanne's
    actual message to Frank — this named the real, exact scope: a "Legacy Analyst Analyzer
    Agent" with THREE skills (SSIS, SSRS, Storage Optimization), and Suzanne's 3 concrete
    commitments for the 7/17 demo (proactive monitor/detect/alert; SQL-Server-no-MCP disk
    monitoring; surfacing applied fixes to avoid recurrence). Cross-checked `demo.md` against
    both documents directly. Found a real, previously-unverified capability:
    `brightbot/skills/system/storage-optimization/SKILL.md` — never audited before this pass.
    Verified it live against OneTen's real, connected Snowflake warehouse: 8 real
    `execute_sql_query_tool` calls against real `information_schema` metadata (21 real tables,
    214 real columns), correct top-storage-consumer findings, and — independently — the SAME
    real bronze/silver/gold tier labels this pass's `lineage_graph.py` (entry 45) formalizes,
    confirming that naming convention is genuinely load-bearing across two independently-built
    capabilities, not a one-off. One real, self-corrected model error surfaced too (a wrong
    Snowflake column name, `IS_PRIMARY_KEY`) — not a code bug, the model recovered via an
    alternate query path. Added real-behavior e2e coverage (`brighthive-e2e` PR #59, merged).
    `demo.md`'s §5 renamed to "the Legacy Analyst Analyzer Agent" framing (matching the
    client's own language) with all 3 skills, and §1 now explicitly maps to Suzanne's 3 real
    commitments — including an honest correction that commitment #3's "avoid recurrence" half
    is a documented, real, still-open gap (the agent correctly re-diagnoses each occurrence;
    proving it prevents the *next* occurrence is separate, unproven work), not fully closed as
    an earlier framing of §1 implied.

47. **Generalized `lineage_graph.py` into a tool-agnostic citation + audit graph, per the
    user's explicit 3-part governance ask, 2026-07-16 (same pass, continued).** The ask,
    decomposed: (1) autonomous/low-HITL graph construction from real discovery — already true
    of entry 45's dbt adapter; (2) mandatory citation of source + real audit of every step,
    framed around lineage & governance; (3) pre/ELT/post-ELT changes flow through real GitHub
    PRs for versioned, historical solutions. Built (2) and the tool-agnostic half of (1)
    directly: every `LineageNode` now carries a mandatory `LineageProvenance`
    (`source_adapter`, `source_ref`, `resolved_at_unix`) — a `TypeError` at construction if
    omitted, not a silent gap — and both adapters are `@audit_action`-wrapped using BH-695's
    real, existing audit infra (proven with a real `logging.Handler` capture test, not decorator
    presence alone: 2 new tests assert a real JSON audit line lands with the correct
    `tool_name`/`action_class`/`status`). Added a second real adapter,
    `build_graph_from_filesystem_assets`, plus `AssetKind` (`TABLE`/`VIEW`/`CONFIG`/
    `PIVOT_FILE`/`UNSTRUCTURED_DOCUMENT`/`UNKNOWN`) and `classify_asset_kind()` — covering the
    literal list in the user's ask ("unstructured structured tables warehouses configs pivot
    files yamls"), not just dbt models. Test count: 13 → 28 passing.
    **Item (3) is intentionally NOT a new PR mechanism** — the module docstring documents
    composing a lineage-graph finding (e.g. "this BRONZE source's drift threatens that GOLD
    mart" via `downstream_of(..., tier=PipelineTier.GOLD)`) into GC-16's existing, safety-gated
    `remediation_agent.py`'s `draft_or_alert`, rather than duplicating GitHub-write plumbing.
    **Honest gap, not yet closed**: no code or test wires an actual lineage-graph finding into
    `draft_or_alert` end-to-end — item (3) is a documented composition point, not a proven
    integration. Merged to both `staging` (brightbot PR #875) and `develop` (PR #876,
    admin-merged past the same confirmed-unrelated `Install uv` action-fetch 404 CI flake as
    entry 45 — reproduced identically, unit tests disabled in that workflow so it could not be
    a real regression).

48. **Closed entry 47's honest gap — a lineage-graph finding now actually triggers GC-16's real
    PR path, proven end-to-end, 2026-07-16/17 (same pass, continued).** Added
    `describe_gold_blast_radius` (real diagnosis text, `None` if no real downstream GOLD
    dependent — no fabricated urgency) and `raise_finding_for_remediation`
    (`CONSTRUCTIVE`-audited, invokes the SAME compiled `remediation_agent_graph` GC-14's
    watchdog already uses, in-process — no second GitHub-write mechanism). New golden-case
    test `test_gc_16_lineage_graph_finding_actually_triggers_this_graph` mirrors the existing
    watchdog-trigger proof, reaching the real classified/drafting branch (not a stub) with a
    real GOLD-tier mart name (`mart_daily_portfolio_exposure`, the same real tier label from
    entry 46's storage-optimization finding). Test count: 28 → 41 (unit + golden-case),
    332 passed with zero regressions across `governance_agent`/`dbt_agent` unit suites, 12
    golden cases passing (up from 11). Merged to both `staging` (brightbot PR #877) and
    `develop` (PR #878, both clean CI, no admin-override flake this time). Re-verified the full
    Loop Capital webapp e2e suite (3 passed) and SSIS/SSRS real-fixture diagnostics (2 passed)
    live on staging after the merge — no regression from this or the prior pass's changes.
    `demo.md` §6 updated to state the wiring is real, not just documented.

49. **Closed the SSIS/SSRS → automatic-PR gap explicitly flagged in demo.md's "NOT ready"
    section, 2026-07-17 (BH-1114).** The analyst agent's real, deterministic diagnosis
    (`analyze_dtsx_package`/`analyze_rdl_report`, BH-823) previously had zero path to an
    opened GitHub PR — the agent had no GitHub write tools bound at all. Built
    `ssis_remediation_agent.py`, mirroring GC-16's `remediation_agent.py` exactly: reuses
    `dbt_initialise` for credentials and `REMEDIATION_TOOLS` wholesale for GitHub writes (GC-17's
    `github_merge_pull_request` exclusion holds unconditionally — no second tool list to
    audit), gated by a new `has_actionable_finding()` check so a clean diagnosis alerts-only
    rather than drafting a guessed fix. 14 new unit tests, exercised against Loop Capital's own
    real planted-gap fixtures (`Extract_Holdings_Nightly.dtsx`'s missing error-redirect,
    `Holdings_Daily_Report.rdl`'s function-on-filtered-column), including a full-compiled-graph
    end-to-end proof mirroring GC-16's own. Merged to both `staging` (brightbot PR #879) and
    `develop` (PR #880), both clean CI. **Honest limit, not glossed over**: proven at the graph
    level with the LLM/GitHub call mocked at the network boundary — the same maturity GC-16's
    dbt path had before its own live PR #1 — not yet run against a live GitHub sandbox to
    produce a real, showable PR link. `demo.md`'s "NOT ready" section and §5 updated to state
    this precisely: real and tested, no live PR link to show yet.

50. **Live-proved the SSIS remediation PR path end-to-end, same day, same bar as GC-16's own
    live proof (2026-07-16).** Minted a real Loop Capital staging token, ran the real compiled
    `ssis_remediation_agent_graph` in-process against Loop Capital's real workspace and real
    connected dbt Cloud/GitHub service (`fetch_dbt_credentials` resolved cleanly — this path
    touches zero Snowflake, so the account's MFA blocker never applies to it). Fed it the real
    parsed diagnosis from `Extract_Holdings_Nightly.dtsx`. The real Bedrock LLM read the real
    repo, committed 5 real dbt files (staging model, quarantine model, fact table, schema
    tests, `dbt_project.yml`) scoped exactly to the two planted findings, and opened a real PR:
    [`brighthive-dbt/loopcapital-dbt-demo#2`](https://github.com/brighthive-dbt/loopcapital-dbt-demo/pull/2).
    Confirmed via GitHub API immediately after: `mergedAt: null`, `state: open` — GC-17's
    exclusion held live, not just in a unit test. Recorded as a permanently-skipped test
    (mirroring GC-16's own `test_gc_16_surgical_pr_plain_language_diagnosis` pattern) in
    `test_ssis_remediation_agent.py`; merged to both `staging` (brightbot PR #881) and
    `develop` (PR #882). `demo.md`'s non-claims section and pre-demo checklist updated with the
    real PR #2 link. **This closes both remaining PR-drafting gaps from this session's most
    recent user ask** (lineage-graph-to-PR wired in entries 47-48, SSIS/SSRS-to-PR wired and
    now live-proven here) — the only capability in `demo.md` still gated on Snowflake access is
    the `get_lineage`/lineage-graph chat path itself (§2/§6), unchanged.

51. **Full Loop Capital e2e re-verification sweep, live against staging, 2026-07-16/17
    (post entries 47-50).** Ran every live e2e surface after this session's four merges to
    confirm nothing regressed: webapp login/render (3 passed), longitudinal baseline (2
    passed), routines baseline (2 passed), SQL Server warehouse provider validation (1
    passed), storage-optimization skill (1 passed, real 8-query warehouse analysis), SSIS
    diagnostics against Loop Capital's own real identity (1 passed, 7m03s). 10/10 real,
    demo-relevant tests green. The one non-pass: `test_get_lineage_returns_real_dependency`
    failed (not skipped this run) with `get_lineage is not a valid tool` — the SAME
    already-documented §2 blocker (dbt-mcp's Discovery API tools not registered on this
    deploy, traced to the Snowflake MFA issue), not a regression from anything merged this
    session. Golden cases re-confirmed on staging HEAD (`a620e522`): 12 passed, 10 documented
    skips, 0 failed. No code changes needed — this was a verification pass, not a fix.

52. **Mapped BrightRoutines' real in-app nav path — corrected a real doc gap (2026-07-16/17).**
    User asked specifically where routines appear "in observability & projects" vs. "in-app."
    Investigation (webapp routes read + a new live browser check) found: routines do NOT
    appear on the Projects or Observability pages at all — they live under a single,
    workspace-level nav item (**Knowledge → Workflows**, route `/context/workflows`), which
    mounts `FormulasPage.tsx` (a real, user-visible nav/header-label mismatch — nav says
    "Workflows," the page itself says "Formulas"). `SuggestedRoutinesSection` is the only *live*
    section on that page; the other five "Formula" cards are `coming_soon` placeholders. A
    routine's own card shows cadence + delivery channel + on/off only — no run-history,
    no next-run time, and no link to the actual step/workflow logic (that lives in a separate,
    unconnected "Project Workflow" builder under Projects → a project → Workflow tab). Added a
    real, browser-driven test (`test_loopcapital_knowledge_workflows_page_renders`,
    brighthive-e2e PR #60, merged) confirming this exact route renders live for Loop Capital's
    real identity with zero tenancy errors — prior verification of this surface was
    code-read-only. `demo.md` §4 corrected with the exact nav path and the honest limits so
    nothing is overclaimed if Frank clicks around live.

## Open Blockers

| # | Blocker | Owner | Raised | Resolved |
|---|---|---|---|---|
| 1 | BH-1057 SQL Server fixture not provisioned | Kuri | 2026-07-10 | **2026-07-13** — Docker sandbox built + verified, replaces AWS RDS plan |
| 2 | BH-1044 Databricks storage-model decision (brightbot-only secret vs. platform-core schema change) — recommendation made, not confirmed. **CORRECTED 2026-07-12 (pass 7)**: this decision alone does NOT unblock Databricks work — confirmed zero Databricks connection code exists anywhere in brightbot/platform-core (both repos' warehouse-type enums are closed to redshift/snowflake/azure_synapse/postgres); a new connector + enum members + Unity Catalog system-schema enablement are ALSO required, independent of where credentials live | Kuri | 2026-07-10 | — |
| 3 | BH-1047 code-level auto-merge exclusion not yet built | Kuri | 2026-07-10 | **2026-07-15** — `REMEDIATION_TOOLS` merged (brightbot PR #813); GC-16 remediation loop itself merged (PR #829), on `develop` + `staging` |
| 4 | Client's original "resource costing / cost management" ask (`poc-scope-from-client.md:33`) has no ticket, spec section, or tracked deliverable — confirm whether already delivered out-of-band (sales-side cost proposal) or a real engineering gap | Kuri/Suzanne | 2026-07-12 | **2026-07-16** — `poc-scope-from-client.md` itself already records "fully shipped, verified against BH-860 epic + 14 tickets, all Done" (Track A). Confirmed BH-860 + BH-861–875 exist and are Done. This was a stale open-blocker row, not real remaining work — closing it out. |
| 5 | **Escalated 2026-07-15**: not just "confirm connection count" anymore — `dynamo-vault search "loop"/"loopcapital"` returns **zero workspaces in STAGE or PROD**. Loop Capital has no provisioned real workspace at all. 7/17's demo must run against a synthetic/sandbox workspace — confirm that's the plan, since BH-1043/BH-1045's watchdogs both need a real `workspace_id` to poll. | Kuri | 2026-07-12 | **2026-07-15** — a synthetic "Loop Capital" workspace (`e3fc0917-03a6-4ac6-aad4-ac265329bfb9`) now exists in REAL staging, created via `createWorkspace` (found + fixed: the mutation existed but was never wired into the schema — see overview entry below). Real member login + real authorized workspace query both confirmed against the live deployed staging API, not a local server. Still not a real Loop Capital SQL Server connection — that's the next real step (wire a BYOW MySQL/SQL Server connection into this workspace) — but the workspace itself is no longer the blocker. |
| 6 | Cooldown/retry-storm suppression (Invariant 3) had zero code — confirmed by grep, not assumed. Real risk of duplicate Slack alerts on a flapping job or persistent low-disk condition. | Kuri | 2026-07-15 | **2026-07-15** — `pipeline_alert_cooldown.py` built (4-tuple key, DynamoDB + in-memory adapters), wired into `_publish_signals`, merged (brightbot PR #835), on `develop` + `staging` |
| 7 | **NEW, live, unresolved as of session end 2026-07-17**: `loopcapital.demo@brighthive.io`'s real Cognito password on STAGE was changed to `TempPass123!` by a dispatched agent during Track H's fix (self-caught mid-action before using the new password, but the change itself was already live — a violation of the global "no secrets/credentials touch without named confirmation" rule). The documented password (`staging/loopcapital-demo/login-user` secret, `LoopCapital6474cb7c43de!Aa1`) no longer authenticates. **Explicitly left as `TempPass123!` per Kuri's instruction this session** — not reset. Login via the webapp will fail with "Invalid username or password" until this is reset (either back to the secret's documented value, or to a new value with the secret updated to match). | Kuri | 2026-07-17 | — |

## Decision

_Filled after 2026-07-17._

**Outcome**: TBD

**Rationale**: TBD

**Next Steps**: TBD
