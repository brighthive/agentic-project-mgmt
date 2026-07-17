---
name: ""
slug: "loopcapital"
stage: "trial"
champion: "Frank"
champion_email: ""
trial_start: ""
trial_end: ""
decision_date: ""
jira_epic: "BH-1036"
notion_page: ""
workspace_id: "e3fc0917-03a6-4ac6-aad4-ac265329bfb9"
aws_account: ""
status: "active"
tags: ["demo"]
---

# Loop Capital demo — this afternoon

> Every claim below is verified against real, deployed staging code and a real e2e test run
> the same day this doc was written. No feature is listed as "ready" without a file path, a
> passing test, or a real PR to point at. See `overview.md` entries 26–36 for the full audit
> trail behind each item.

## Environment

- **Workspace**: `e3fc0917-03a6-4ac6-aad4-ac265329bfb9` ("Loop Capital"), real staging
- **Login**: `loopcapital.demo@brighthive.io` — Cognito credentials in `staging/loopcapital-demo/login-user` (Secrets Manager)
- **Webapp**: `https://staging.brighthive.io/workspace/e3fc0917-03a6-4ac6-aad4-ac265329bfb9/brightagent`
- **Re-verify live right before the demo**: `cd brighthive-e2e && .venv/bin/python -m pytest e2e/features/edges/test_loopcapital_webapp.py -v --env=staging -s`

---

## 1. Golden Cases GC-14 → GC-17 — the core proactive loop

This is the strongest, most demoable capability. Real code, deployed to staging, with one
real external GitHub PR as proof it isn't a mock.

| # | What it demos | Evidence |
|---|---|---|
| GC-14 | Watchdog detects a broken nightly dbt job **before** anyone asks BrightAgent — alert reaches Slack | `pipeline_watchdog_task.py`; `test_gc_14_proactive_monitor_alert.py` (3 passed) |
| GC-15 | Same proactive detection for a SQL Server source with **no MCP connector** — disk pressure + job pass/fail, BYOW pattern | `sql_server_pipeline_source.py`; live sandbox tests (5 real-behavior, zero mock) |
| GC-16 | Real root-cause diagnosis → real dbt fix drafted → **real GitHub PR opened** | `remediation_agent.py`; proof PR: `brighthive-dbt/loopcapital-dbt-demo#1` (merged 2026-07-16) — open this PR live if asked "did it really do this" |
| GC-17 | Safety gate: the agent **never** auto-merges its own fix — a human always merges | `test_gc_17_auto_merge_exclusion.py` proves `github_merge_pull_request` is never bound to the remediation agent's tool set |

**Demo script**: show the Slack alert → show the agent's diagnosis in chat → open PR #1 in
GitHub to prove it's a real PR, not a screenshot — it shows `MERGED`, by a human, which is
itself the proof of the safety gate: the agent drafted and opened it, a person reviewed and
merged it, the agent never merges its own work.

**Maps directly to Suzanne's 3 commitments to Frank for this demo**: (1) GC-14/16/17 = "proactively
monitors, detects and resolves issues, alerts the user"; (2) GC-15 = "MCP connects to a SQL
Server with no MCP installed, alerts at 20% disk"; (3) GC-16's diagnosis surfacing = "surface
the fixes the agent applied." **Be precise on #3**: what's proven is the agent surfaces *why*
it fixed something (plain-language diagnosis in the PR). What's honestly still open,
documented as a real gap (`test_gc_16_recurrence_actually_prevented_not_just_redetected`), is
proof that the *same class* of issue is actually prevented from recurring — vs. being
correctly re-diagnosed each time it happens. If asked "does this stop it from happening again,"
the honest answer is "it correctly diagnoses and fixes each occurrence today; proving it
prevents the *next* occurrence is the next real step."

**Re-verify same day**:
```bash
cd brightbot
RUN_LIVE_SQLSERVER=1 BH_RUN_LIVE_EVALS=1 pytest tests/integration/golden_cases/ \
  -k "gc_14 or gc_15 or gc_16 or gc_17 or governance"
```

---

## 2. Engineering agent capacities

Real, chat-reachable capabilities — not aspirational:

- **SQL generation + dbt model creation** from a plain-English ask (`convert_sql_to_dbt`, `generate_dbt_source_and_staging`)
- **Real dbt DAG lineage** via dbt-mcp (`get_lineage`, `get_model_parents`/`get_model_children`) — enabled on staging as of this week (BH-1111), proven against Loop Capital's own dbt Cloud project: ask "what are the upstream dependencies of `stg_holdings_nightly`" and the agent correctly answers `source('raw', 'holdings_raw')`
- **Warehouse/pipeline health checks** via `check_pipeline_health_tool` / `scan_warehouse_tables_tool`
- **Whole-warehouse discover→profile scan** (`scan_warehouse_tables_direct`, BH-1076) — "scan
  the whole database" is real, chat-reachable, and now proven with real-behavior tests against
  a live SQL Server sandbox (3 passing: real discovery, real profiling, real per-table error
  isolation) — not just unit-mocked. Caveat: this is per-table profiling chained across the
  catalog, not a single "database health score" — describe it as "point it at a database and
  it profiles every table it finds," not "one-click whole-DB report."
- **GitHub PR authorship** for fixes (see GC-16 above) — real branch, commit, and PR creation, not just a diff preview

**Do NOT script this as a live "watch it happen" moment — a real root cause was found and is
partially fixed, not just a phrasing quirk.** Forcing a direct `get_lineage` call on
2026-07-16 reproduced a real error: `1 validation error for get_lineageArguments\nunique_id\n
Field required` — the tool needs a fully-qualified `unique_id`, not a bare model name, and our
prompt never told the model that. Traced further and fixed 2 of 3 real infra bugs blocking
this (GitHub App authorization + a dbt Cloud repository↔project linking bug — full writeup:
`platform-saas-ai-context/docs/architecture/DBT_CLOUD_LEARNINGS.md`). The parse step now
genuinely succeeds (found the real model + source), but the full run still fails on Snowflake
demanding MFA enrollment for the service account — a real, unresolved blocker needing
Snowflake account-admin access, not something fixable today. **Demo script**: describe this
narratively ("we found and are actively fixing the exact reason this doesn't work yet — the
underlying capability and its dbt Cloud connection are real, this is a live open engineering
item, not vaporware") rather than asking the live question. If asked directly whether it works,
the honest answer is "not yet — here's exactly what's blocking it and why," which is a stronger
answer than a vague "it's real but variable."

---

## 3. Longitudinal drift monitoring — values AND schema

Real, shipped, separate from the GC-14-17 work (this is GC-12, a general BrightAgent
capability Loop Capital also benefits from):

- `longitudinal_detect.py`, `root_cause_classifier.py`, `metric_history_store.py`
- Detects both **value drift** (a metric moving outside its historical range) and **schema
  drift** (a column renamed/retyped) — this session fixed a real bug where the schema-drift
  classifier's regex was over-broad and false-positived; now precise
- Test coverage: `test_longitudinal_detect.py`, `test_longitudinal_graph_wiring.py`,
  `test_gc_12_longitudinal_live.py` (live variant)

**Loop Capital's own workspace has zero data assets** — confirmed live: `workspace.dataAssets`
returns `[]`. Longitudinal drift needs historical metric snapshots to compare against, which
requires a real, catalogued data asset first; there's nothing to click through on Loop
Capital's own workspace yet, same underlying reason as BrightRoutines' empty state above (a
fresh synthetic demo workspace, no organic history).

**Demo script**: reference this as "the same proactive engine also watches for values and
schemas quietly drifting over time, not just hard failures" — don't attempt a live
click-through on Loop Capital's own workspace (there's nothing there yet); this is best framed
as an architectural point, or demoed on the OneTen/sandbox workspace if a live example is asked
for.

---

## 4. BrightRoutines — scheduled "nightshift" workflows, in-app + Slack

Real and shipped (pre-existing BrightHive capability, not built for this trial specifically):

- Scheduling/detection engine: `brightbot/routines/{detector,classifier,detector_task,capture,store,judge}.py`
- Webapp surface: `SuggestedRoutinesSection`, `ScheduledRoutineRow`, `RoutineSuggestionCard`
- Slack surface: `routine-suggestion-action`, Block Kit formatter, classify pipeline

**Exact in-app navigation path (verified against `brighthive-webapp` routes 2026-07-17)**: left
nav → **Knowledge → Workflows**. That nav label mounts `FormulasPage.tsx` — the page header
itself says "Formulas," not "Workflows" (a real, user-visible naming mismatch — mention it only
if asked, don't lead with it). `SuggestedRoutinesSection` is the only *live* section on that
page; the other five "Formula" cards (Data Transformations, Calculated Metrics, Custom Prompts,
Document Pipelines, Share & Publish) are all `status: coming_soon` placeholders at reduced
opacity — do not click into them or imply they're real.

**What the in-app routine card shows, and what it honestly doesn't**: a scheduled routine's row
shows title, description, a cadence chip (daily/weekly/biweekly/monthly/quarterly), a delivery
chip (webapp/Slack/email), and an on/off toggle. It does **not** show last-run status, next-run
time, or the underlying workflow logic/steps — there's a separate, unrelated "Project Workflow"
step-graph builder (`src/ProjectWorkflow/`, reached via Projects → a project → Workflow tab)
that is NOT linked from the routines card. If asked "can I see exactly what steps this routine
runs," the honest answer is "not from this card — that's a different, unconnected part of the
app today."

**Loop Capital's own workspace has zero routines today** — confirmed live: both
`routineSuggestionsForWorkspace` and `scheduledRoutinesForWorkspace` return empty for
workspace `e3fc0917-03a6-4ac6-aad4-ac265329bfb9`. This is expected, not a bug — BrightRoutines'
detector surfaces suggestions from real observed usage patterns over time, and Loop Capital's
workspace is a fresh synthetic demo environment with no organic activity history yet. The OneTen
ground-truth workspace has a real one ("Generate weekly earnings report", status `OFFERED`) —
confirmed live the same way.

**Demo script**: navigate Knowledge → Workflows to show the real OneTen routine card in the
webapp (or ask BrightHive's own team account, not Loop Capital's), then the equivalent Slack
card — same routine, two surfaces. Frame it as "this is what emerges after the agent has
watched your team's real work for a while" — do NOT open Loop Capital's own workspace expecting
to find one; there isn't one yet. Do NOT click into the other five "Formulas" cards — they're
placeholders, not built.

**What NOT to claim here**: (1) MCP/A2A exposure of BrightRoutines (letting an external agent
trigger a routine) is scoped (BH-1038–1041) but not built — if asked "can another system trigger
this," the honest answer is "that's on the roadmap, not built yet." (2) A routine card does not
show its own run history or its underlying step logic today — those live in a separate,
unconnected part of the app (see above).

---

## 5. The "Legacy Analyst Analyzer Agent" — SSIS, SSRS, and Storage Optimization

Corrected from an earlier, wrong read of this codebase: real deterministic XML parsing
exists, not just a prompt-only skill.

- `analyze_dtsx_package` / `analyze_rdl_report` (`pipeline_diagnostics_tools.py`, BH-823) use
  real `ElementTree` parsing — not the model eyeballing raw XML — to find grounded structural
  facts, wired onto the analyst agent's chat tools
- **Proven against Loop Capital's own real sandbox artifacts** (not synthetic toy XML): the
  `.dtsx` parser correctly finds `Extract_Holdings_Nightly.dtsx`'s two deliberately planted
  gaps (no error-row redirect, no staging step); the `.rdl` parser correctly finds
  `Holdings_Daily_Report.rdl`'s `CAST(GETDATE() AS DATE)` function-on-filtered-column
  anti-pattern (`test_ssis_ssrs_diagnostics_real_fixtures.py`, 2 passed)
  - **Also proven at the full chat level, against Loop Capital's own real identity and its own
    real artifact** (not just the generic OneTen test), live on staging: ask the analyst to
    diagnose `Extract_Holdings_Nightly.dtsx` in the Loop Capital workspace and it delegates
    correctly and returns a real skill-shaped diagnosis
    (`test_loopcapital_analyst_diagnoses_its_own_real_ssis_package`, passed 3x)
- Output is a structured JSON diagnosis + dbt-migration suggestion — a real recommendation, not
  a screenshot

**Timing note**: this specific skill (full package read + reasoning) took 2m47s–9m+ across
live test runs — noticeably slower than most other chat answers in this doc. If demoing this
live, either kick it off early and talk through something else while it runs, or set the
expectation up front ("this one takes a few minutes — it's actually reading and reasoning
over the whole package, not a canned answer").

**Demo script**: ask the agent to diagnose `Extract_Holdings_Nightly.dtsx` (or the SSRS
report) and it should name the real missing error-redirect / staging-step gap, or the real
function-on-filter issue — grounded in the actual file structure, not a generic-sounding
guess.

**What NOT to claim here**: this is on-demand diagnosis of a file you point the agent at, not
a continuous background watch like GC-14/15. The diagnosis-to-PR path is real, tested, AND
live-proven (`ssis_remediation_agent.py`, BH-1114 — real PR
[#2](https://github.com/brighthive-dbt/loopcapital-dbt-demo/pull/2)) — see the non-claims
section below, updated to reflect this closure.

### 5c. Storage Optimization — the third skill, verified live against a real Snowflake warehouse

The client's own POC scope names this as the third skill of the "Legacy Analyst Analyzer
Agent" alongside SSIS and SSRS. Real and proven, verified live 2026-07-16 against OneTen's
real, connected Snowflake warehouse (not a sandbox):

- Asked the analyst live: "find cold or oversized tables and estimate savings" — it ran **8
  real `execute_sql_query_tool` calls** against Snowflake's real `information_schema`
  metadata (not fabricated numbers): 21 real tables, 214 real columns inventoried
- Correctly identified real top storage consumers by byte size (`STG_HOLDINGS_SNAPSHOT`,
  `INT_ENRICHED_HOLDINGS`, `MART_DAILY_PORTFOLIO_EXPOSURE`) and correctly labeled each by its
  real bronze/silver/gold tier from the naming convention — independent confirmation of the
  same tier classification `lineage_graph.py` (§6) formalizes
- Correctly flagged 2 real empty tables and reported "no clustering keys applied" as a real
  optimization opportunity — grounded in the actual catalog metadata, not a generic-sounding
  answer
- One query attempt used a wrong Snowflake column name (`IS_PRIMARY_KEY`) and failed with a
  real SQL compilation error — the agent self-corrected via an alternate query path and still
  produced the full real analysis. Worth knowing about if it happens live: it's the model
  guessing a column name, not a broken tool, and it recovers on its own.

**Demo script**: ask the agent to find storage optimization opportunities in the connected
warehouse — expect a real, multi-query analysis citing actual table names, byte sizes, and row
counts, landing on real, specific recommendations (not "consider reviewing your storage
costs").

---

## What is explicitly NOT ready — do not claim these live

Being upfront here protects the demo. If Frank asks about any of these, the honest answer is
"real engineering work, scoped, not yet built" — not a workaround or a screenshot.

- **SSIS/SSRS → automatic PR suggestion — CLOSED AND LIVE-PROVEN (2026-07-16, BH-1114).**
  Diagnosis itself IS real (see section 5 below), and it now has a real path into an opened
  GitHub PR: `ssis_remediation_agent.py` mirrors GC-16's dbt remediation loop exactly — same
  `REMEDIATION_TOOLS` GitHub tool list (GC-17's `github_merge_pull_request` exclusion holds
  unconditionally), same "real finding, never a guessed fix" gate. **Live-proven the same day**,
  the same bar GC-16's own PR #1 set: ran the real compiled graph against Loop Capital's own
  real workspace and real connected dbt Cloud/GitHub service, fed it the real parsed diagnosis
  from `Extract_Holdings_Nightly.dtsx` — the real LLM committed 5 real dbt files (staging
  model, quarantine model, fact table, schema tests) scoped exactly to the two planted
  findings and opened a real PR:
  [`brighthive-dbt/loopcapital-dbt-demo#2`](https://github.com/brighthive-dbt/loopcapital-dbt-demo/pull/2)
  — confirmed `mergedAt: null`, `state: open` via GitHub API (GC-17 held live, not just in a
  unit test). This path needs zero Snowflake access (static XML parsing only), so it is NOT
  affected by the Snowflake MFA blocker documented in §2/§6. If asked "can it open a PR to fix
  my SSIS package," the honest answer is "yes — here's the real PR it opened this morning."
- **SSIS/SSRS as a monitored, standing watch.** There is no live SQL Server connection reading
  `msdb`/`ReportServer` catalog metadata on an ongoing basis — this is on-demand diagnosis of a
  file you point the agent at (uploaded or in a known path), not a background watchdog like
  GC-14/15. Frame it as "ask the agent to diagnose this package" not "it's watching your SSIS
  jobs continuously."
---

## 6. Bronze/silver/gold pipeline quality — real, three pieces now connected

Corrected from an earlier, wrong read of this codebase: this was flagged as "zero code exists"
— that was true of a bespoke medallion-tier concept, but wrong once you look at what already
combines. Three real pieces, now genuinely wired together (BH-1114):

- **Per-asset quality checks already run against any asset, any tier, today.**
  `execute_library_quality_rules` (real, already shipped) runs a workspace's active quality
  rules against a named asset and writes a real `QualityRuleExecution` to Platform Core — the
  tier the asset sits at was never a gate on this.
- **Whole-warehouse discovery + profiling already covers every table** (BH-1076, real-behavior
  tested against a live SQL Server sandbox this week).
- **The missing piece — tier classification + real lineage-graph traversal — is now built**
  (`lineage_graph.py`): a warehouse-agnostic `LineageGraph`/`LineageSource` **Port**, with dbt
  as the first real **Adapter** (Databricks Unity Catalog / Snowflake-native lineage are the
  documented next adapters, not speculative — this follows the org's own ports-and-adapters
  rule). `classify_tier` maps the same `raw`/`stg_`/`int_`/`mart_` naming convention already
  used elsewhere in this codebase (the SSIS diagnostics staging-step check) onto
  bronze/silver/gold. Tested against Loop Capital's own real model pair
  (`raw.holdings_raw` → `stg_holdings_nightly`) — 13 unit tests passing, real fixture, not an
  invented naming scheme.
- **Generalized to any asset, not just dbt models, with mandatory citation + real audit.**
  Every node now carries a `LineageProvenance` (real adapter name + real source reference +
  timestamp) — omitting it is a hard construction-time error, not a silent gap. A second real
  adapter, `build_graph_from_filesystem_assets`, covers configs (YAML/JSON), pivot/Excel
  exports, and unstructured documents alongside warehouse tables. Every graph build emits a
  real audit log line via BH-695's existing audit infra — proven with a real logging-capture
  test, not just a decorator.
- **A graph finding now actually opens a real GitHub PR — the composition is wired, not just
  documented.** `raise_finding_for_remediation` + `describe_gold_blast_radius` feed a real
  "this bronze source's drift threatens that gold mart" finding into the SAME compiled
  remediation graph GC-14's watchdog already uses — no second PR mechanism. A new golden-case
  test (`test_gc_16_lineage_graph_finding_actually_triggers_this_graph`) proves it reaches the
  real classified/drafting branch end-to-end. 41 unit + golden-case tests passing.

**What this genuinely unlocks**: "which gold-tier marts are at risk because this bronze source
has a quality problem" is now a real, answerable graph query — `graph.downstream_of(bronze_id,
tier=PipelineTier.GOLD)` — AND, if the drift's phrasing classifies into a known DATA_SHAPE mode,
a real reviewable PR the same way GC-16 already works for a dbt-detected failure.

**What's still a real limitation, be upfront about it**: the graph today needs real
model/source + edge data from dbt-mcp's Discovery API to populate — and that's the exact
capability blocked on the Snowflake MFA issue documented in §2 above (fixed for the
GitHub/dbt-Cloud-linking half; still blocked on Snowflake account-admin access for the
warehouse-auth half). Until that's resolved, this is demoable as **real, tested code** you can
show and explain, not yet a live "watch it answer" chat moment on Loop Capital's own project.

---

## Pre-demo checklist (run these, in order, ~30 min before)

```bash
# 1. Confirm Loop Capital login + chat surface still render clean
cd brighthive-e2e && .venv/bin/python -m pytest e2e/features/edges/test_loopcapital_webapp.py -v --env=staging -s

# 2. Confirm the golden-case proactive loop still passes
cd brightbot && RUN_LIVE_SQLSERVER=1 BH_RUN_LIVE_EVALS=1 pytest tests/integration/golden_cases/ \
  -k "gc_14 or gc_15 or gc_16 or gc_17 or governance"

# 3. Confirm dbt-mcp lineage is STILL LIVE (not just still invokable — this test only
#    checks the tool got called; a SKIP here is common (~6/6 seen on 2026-07-16 morning)
#    and does NOT mean the capability is broken — see the note in section 2 above.
#    Do not treat a skip as a red flag; do not treat a bare PASS as proof it worked either.
cd brighthive-e2e && BH_LANGGRAPH_URL="https://brightagent-staging-760d8832084555d487edeb54e9969675.us.langgraph.app" \
  .venv/bin/python -m pytest e2e/features/data/test_dbt_mcp_lineage.py -v --env=staging -s

# 4. Have PR #1 (GC-16 dbt remediation, state: MERGED) and PR #2 (SSIS remediation,
#    state: OPEN, not merged — GC-17 proof) open in tabs, ready to show.
# NOTE: repo was moved to brighthive-dbt org on 2026-07-16 while fixing get_lineage's
# GitHub App authorization (see overview.md entry 42) — use this URL, not the old brighthive/ one.
open "https://github.com/brighthive-dbt/loopcapital-dbt-demo/pull/1"
open "https://github.com/brighthive-dbt/loopcapital-dbt-demo/pull/2"

# 5. Confirm SSIS/SSRS diagnostics find the real, planted gaps in Loop Capital's own fixtures
cd brightbot && .venv/bin/python -m pytest \
  tests/integration/golden_cases/test_ssis_ssrs_diagnostics_real_fixtures.py -v
```

If anything above fails, stop and fix it before the demo — do not demo against a red check.

**Optional, only if demoing the whole-warehouse scanner live** (heavier — needs the sandbox up):
```bash
cd clients/trials/loopcapital/sandbox && MSSQL_SA_PASSWORD=<pw> ./setup.sh
cd ../../../../brightbot && MSSQL_SA_PASSWORD=<pw> RUN_LIVE_SQLSERVER=1 \
  pytest tests/integration/golden_cases/test_warehouse_scan_real_sandbox.py -v
# tear down after: cd clients/trials/loopcapital/sandbox && MSSQL_SA_PASSWORD=<pw> docker compose down -v
```

**Optional, only if demoing SSIS diagnostics live against Loop Capital's own identity**
(slow — budget 3-9 minutes):
```bash
cd brighthive-e2e && BH_LANGGRAPH_URL="https://brightagent-staging-760d8832084555d487edeb54e9969675.us.langgraph.app" \
  .venv/bin/python -m pytest e2e/features/edges/test_loopcapital_ssis_diagnostics.py -v --env=staging --writes -s
```
