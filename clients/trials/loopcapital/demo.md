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
| GC-16 | Real root-cause diagnosis → real dbt fix drafted → **real GitHub PR opened** | `remediation_agent.py`; proof PR: `brighthive/loopcapital-dbt-demo#1` (merged 2026-07-16) — open this PR live if asked "did it really do this" |
| GC-17 | Safety gate: the agent **never** auto-merges its own fix — a human always merges | `test_gc_17_auto_merge_exclusion.py` proves `github_merge_pull_request` is never bound to the remediation agent's tool set |

**Demo script**: show the Slack alert → show the agent's diagnosis in chat → open PR #1 in
GitHub to prove it's a real PR, not a screenshot — it shows `MERGED`, by a human, which is
itself the proof of the safety gate: the agent drafted and opened it, a person reviewed and
merged it, the agent never merges its own work.

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
- **GitHub PR authorship** for fixes (see GC-16 above) — real branch, commit, and PR creation, not just a diff preview

**Demo script**: ask the agent the dbt-lineage question live in chat; it should name the real
model and real source. If it instead chooses a grep-based tool for a differently-worded
question, that's a known, harmless variance — the capability is real either way, just don't
over-script the exact phrasing.

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

**Demo script**: reference this as "the same proactive engine also watches for values and
schemas quietly drifting over time, not just hard failures" — don't over-index on a live
click-through unless asked; this is best framed as an architectural point.

---

## 4. BrightRoutines — scheduled "nightshift" workflows, in-app + Slack

Real and shipped (pre-existing BrightHive capability, not built for this trial specifically):

- Scheduling/detection engine: `brightbot/routines/{detector,classifier,detector_task,capture,store,judge}.py`
- Webapp surface: `SuggestedRoutinesSection`, `ScheduledRoutineRow`, `RoutineSuggestionCard`
- Slack surface: `routine-suggestion-action`, Block Kit formatter, classify pipeline

**Demo script**: show a suggested/scheduled routine in the webapp, then the equivalent Slack
card — same routine, two surfaces. Good for the "proactive, not just reactive" narrative.

**What NOT to claim here**: MCP/A2A exposure of BrightRoutines (letting an external agent
trigger a routine) is scoped (BH-1038–1041) but not built. If asked "can another system
trigger this," the honest answer is "that's on the roadmap, not built yet."

---

## What is explicitly NOT ready — do not claim these live

Being upfront here protects the demo. If Frank asks about any of these, the honest answer is
"real engineering work, scoped, not yet built" — not a workaround or a screenshot.

- **SSIS/SSRS live diagnostics.** There is no live SQL Server connection reading `msdb`/
  `ReportServer` catalog metadata, no `.dtsx`/`.rdl` parser code anywhere in the codebase, and
  no PR-generation path from an SSIS/SSRS diagnosis. What exists is a **prompt-only skill**
  that can discuss an uploaded sample file — not a monitored, live capability. Do not demo
  this as "BrightAgent watches your SSIS packages."
- **Whole-database proactive profiling.** The profiler (`scan_warehouse_tables_tool`,
  `governance_quality.py`) is real but **asset-ID-gated** — it profiles the specific
  table/asset you point it at, not "point it at the whole database and it profiles
  everything." Discovery→profiling orchestration (BH-1076) exists with passing unit tests but
  isn't the full auto-rollup story yet.
- **Bronze/silver/gold medallion-aware quality gating.** No code enforces or reports on a
  bronze→silver→gold data-quality lifecycle anywhere in brightbot or platform-core. The one
  hit for "gold" in platform-core is a comment example, not logic. This is honestly scoped as
  future work (BH-1061–1064: lineage-aware data quality), not built.

---

## Pre-demo checklist (run these, in order, ~30 min before)

```bash
# 1. Confirm Loop Capital login + chat surface still render clean
cd brighthive-e2e && .venv/bin/python -m pytest e2e/features/edges/test_loopcapital_webapp.py -v --env=staging -s

# 2. Confirm the golden-case proactive loop still passes
cd brightbot && RUN_LIVE_SQLSERVER=1 BH_RUN_LIVE_EVALS=1 pytest tests/integration/golden_cases/ \
  -k "gc_14 or gc_15 or gc_16 or gc_17 or governance"

# 3. Confirm dbt-mcp lineage is still live (real chat call)
cd brighthive-e2e && BH_LANGGRAPH_URL="https://brightagent-staging-760d8832084555d487edeb54e9969675.us.langgraph.app" \
  .venv/bin/python -m pytest e2e/features/data/test_dbt_mcp_lineage.py -v --env=staging -s

# 4. Have PR #1 open in a tab, ready to show (state: MERGED)
open "https://github.com/brighthive/loopcapital-dbt-demo/pull/1"
```

If anything above fails, stop and fix it before the demo — do not demo against a red check.
