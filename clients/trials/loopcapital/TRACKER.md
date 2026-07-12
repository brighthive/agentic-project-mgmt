# Loopcapital — Live Tracker

_Last refreshed **2026-07-12 22:17 UTC** by `make loopcapital-tracker`. Auto sections are overwritten — manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, ❓ Open Questions) are preserved._

> **Trial dates**: Demo 1: 2026-07-09 (done) — Demo 2 / decision gate: 2026-07-17 · **Epic**: [BH-1036](https://brighthiveio.atlassian.net/browse/BH-1036)

---

## 🚨 Blockers

<!-- TRACKER:MANUAL:BEGIN blockers -->

_No active blockers. Add lines in the form: `**🚨 BH-XXX** — short description (raised YYYY-MM-DD by @owner)`._

<!-- TRACKER:MANUAL:END blockers -->

## 🎯 This Week

<!-- TRACKER:MANUAL:BEGIN this-week -->

_Weekly standup output. Update Monday morning with the week's ticket commitments by owner._

<!-- TRACKER:MANUAL:END this-week -->

---

## 🗓️ Day-by-day — task / day / progress

_Legend: 🟢 done (ticket closed / PR merged) · 🟡 in progress (PR open or ticket in review) · ⬜ not started · 🔲 awaiting external/manual. Auto-fills as tickets move and PRs merge._

### Track A — Legacy Analyst Analyzer Agent (SSIS/SSRS/Storage) — COMPLETE (0/4 🟢)

_Delivered for the 2026-07-09 demo. Fully shipped per BH-860 epic (14 tickets, all Done). No further engineering work needed on this track. Frank's reaction: platform is real, but proactivity wasn't demonstrated and "your screen says this is not live" on a separate page — this drove the Track B commitment below._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Done | SSIS diagnostics skill (bottleneck detection + dbt migration suggestions) | [BH-863](https://brighthiveio.atlassian.net/browse/BH-863) |
| ⬜ | Done | SSRS diagnostics skill | [BH-863](https://brighthiveio.atlassian.net/browse/BH-863) |
| ⬜ | Done | Storage optimization skill | [BH-863](https://brighthiveio.atlassian.net/browse/BH-863) |
| ⬜ | Done | Synthetic SSIS fixture + staging validation | [BH-869](https://brighthiveio.atlassian.net/browse/BH-869), [BH-866](https://brighthiveio.atlassian.net/browse/BH-866) |

### Track B, Point 1 — Proactive monitor/detect/alert loop (0/6 🟢)

_Suzanne's demo commitment #1: "the engineering agent and how it proactively monitors, detects and resolves issues with the ability to alert the user on what it finds." This is the watchdog capability node — the actual missing-proactivity primitive this whole spec was built to close._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | T-5 (by 2026-07-12) | BH-1042 contract finalized — types/registry/MCP tool, no ambiguity for implementers | [BH-1042](https://brighthiveio.atlassian.net/browse/BH-1042) |
| ⬜ | T-4 | BH-1054 watchdog node registered + wired to existing scheduled dispatcher | [BH-1054](https://brighthiveio.atlassian.net/browse/BH-1054) |
| ⬜ | T-4 | BH-1043 dbt job/run health poller — detects a real failed run | [BH-1043](https://brighthiveio.atlassian.net/browse/BH-1043) |
| ⬜ | T-3 | BH-1046 alert path — Slack + webapp both show the detected failure (dual-write verified) | [BH-1046](https://brighthiveio.atlassian.net/browse/BH-1046) |
| ⬜ | T-3 | CRITICAL, filed pass 35: BH-1067 renderers for 5 of 6 new stage values — dual-write alone is not enough; dbt_run_stale/databricks_job_failure/databricks_cluster_unhealthy/etl_job_failure/source_disk_low have zero visible text on either surface without this, identical to GC-12's confirmed dead-end (BH-1065/1066) | [BH-1067](https://brighthiveio.atlassian.net/browse/BH-1067) |
| ⬜ | T-2 | End-to-end dry run: real dbt Cloud failure (BH-1058 fixture) → detected unprompted → alerted on both surfaces | [BH-1058](https://brighthiveio.atlassian.net/browse/BH-1058) |

### Track B, Point 2 — SQL Server with no MCP (disk-space monitoring) (0/4 🟢)

_Suzanne's demo commitment #2, Frank's literal named example: "how MCP will connect to the SQL server when the server does not have an MCP... monitoring the disk space and alerting when it's at 20% capacity left." Direct rebuttal to Frank's stated disbelief that this is technically possible — must be demoed against REAL infrastructure per test-behavior-real.md, not a mock, since a mocked page is exactly what triggered his "this is not live" reaction on 2026-07-09._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | T-5 | BH-1057 SQL Server provisioned in staging (RDS Web edition — NOT Express, no SQL Server Agent otherwise) | [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) |
| ⬜ | T-4 | BH-1045 disk/job query wired through existing WarehousePort/SynapseConnection chain — zero new connectivity | [BH-1045](https://brighthiveio.atlassian.net/browse/BH-1045) |
| ⬜ | T-3 | Demo data seeded: real filler data landing near 20% free space, real SQL Server Agent jobs (mix of pass/fail) | [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) |
| ⬜ | T-2 | Dry run: watchdog polls real SQL Server, detects low disk, alerts — no MCP on the SQL Server side, ever. Requires BH-1067's source_disk_low renderer to actually show text (detection without it is silent). | [BH-1045](https://brighthiveio.atlassian.net/browse/BH-1045), [BH-1054](https://brighthiveio.atlassian.net/browse/BH-1054), [BH-1067](https://brighthiveio.atlassian.net/browse/BH-1067) |

### Track B, Point 3 — Fix-recurrence surfacing (0/4 🟢)

_Suzanne's demo commitment #3: "the ability to build skills that help surface the fixes the agent applied when they are not abided by so we can avoid the recurrence of the same kind of issue." Mechanism: self-healing-pipelines.md's surgical-PR loop (GC-11), wired to this spec's watchdog signals — with a CRITICAL safety fix required first (see below)._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | T-5 | CRITICAL: BH-1047's code-level exclusion of github_merge_pull_request from the remediation loop's tool list — 'never auto-merge' was previously prompt-only, zero code enforcement | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |
| ⬜ | T-4 | root_cause_class classifier wired (DATA_SHAPE vs JOB_RUNTIME) — routes correctly, never fabricates a fix | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |
| ⬜ | T-3 | DATA_SHAPE signal routes into GC-11's existing surgical-PR loop, human-approval-gated | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |
| ⬜ | T-2 | Demo dry run: a detected failure surfaces a surgical PR with a plain-language diagnosis, requires human approval, never auto-merges | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |

### T-1 — Full dress rehearsal (0/0 🟢)

_Run the entire demo script end-to-end against real staging infrastructure, exactly as it will be shown to Frank. No mocks — this is the whole point after 2026-07-09's "this is not live" reaction._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | T-1 (2026-07-16) | All 3 points demoed live: watchdog detects a real dbt failure; SQL Server disk-low alert fires from a real RDS instance; a surgical PR opens and is shown NOT auto-merging | _manual_ |
| 🔲 | T-1 | Demo script + talking points finalized (Suzanne/Matt) | _manual_ |

### T-0 — Demo day (0/0 🟢)

_Decision gate._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | 2026-07-17 | Demo delivered to Frank | _manual_ |
| 🔲 | Post | Decision recorded (Won / Lost / Extended) with rationale | _manual_ |

### Track C — Lineage-aware data quality (post-demo, honest framing for 7/17) (0/7 🟢)

_New capability, scoped 2026-07-12 after Kuri's example: a pipeline can run with ZERO errors while a source column silently degrades (NULLs where real values used to be), poisoning Gold/Diamond numbers with no alert anywhere. NOT achievable by 7/17 — this is genuinely new, multi-week work. Full spec: docs/specs/lineage-aware-data-quality.md. For the demo: show the anomaly-detection half (real, shipped, GC-12) and frame the lineage-tracing half honestly as "we glue dbt/Databricks' own lineage to what they can't see themselves" — a real differentiator, not a gap to hide._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Post-demo | BH-1062 — fetch + parse dbt manifest.json/catalog.json (reuses existing artifact-fetch plumbing) | [BH-1062](https://brighthiveio.atlassian.net/browse/BH-1062) |
| ⬜ | Post-demo | BH-1063 (platform-core, 2-3 files confirmed pass 6 — no public schema touch, mirrors AnomalyEventNode's cheaper OGM-only pattern) — load parsed DAG into Neo4j as a queryable lineage graph | [BH-1063](https://brighthiveio.atlassian.net/browse/BH-1063) |
| ⬜ | Post-demo | BH-1064 — wire anomaly events to walk the graph forward, closing the already-deferred BH-673 bridge | [BH-1064](https://brighthiveio.atlassian.net/browse/BH-1064) |
| ⬜ | Post-demo | BH-1066 — CONFIRMED pass 5: GC-12 anomaly notifications have zero rendering in Slack/webapp today, independent of this epic's own changes. BH-1064's enrichment has nothing to enrich that a human sees until this ships. | [BH-1066](https://brighthiveio.atlassian.net/browse/BH-1066) |
| ⬜ | Post-demo | BH-1068 — Snowflake-native lineage adapter (Snowpipe/Tasks/Streams/Dynamic Tables via ACCOUNT_USAGE) — cheaper than the Databricks half, reuses the existing SnowflakeConnection | [BH-1068](https://brighthiveio.atlassian.net/browse/BH-1068) |
| ⬜ | Post-demo | BH-1069 — brightbot call site for upsert_lineage_graph (formerly informal 'BH-1063a'), real ogm_api.py plumbing + GraphQL-errors-key check | [BH-1069](https://brighthiveio.atlassian.net/browse/BH-1069) |
| ⬜ | Post-demo | BH-1070 — test coverage gap: metric-snapshot.ts (BH-1063b's own cited precedent) has zero existing tests; non-blocking tech debt, tracked for visibility | [BH-1070](https://brighthiveio.atlassian.net/browse/BH-1070) |

### Non-blocking, tracked separately (0/7 🟢)

_Real work, correctly scoped OUT of the 7/17 critical path — don't let these stall Track B above._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Post-demo | BH-1044 Databricks storage-model decision (brightbot-only secret recommended, needs Kuri confirm) | [BH-1044](https://brighthiveio.atlassian.net/browse/BH-1044) |
| ⬜ | Post-demo | BH-1053 BrightSignals 3-way split-brain unification | [BH-1053](https://brighthiveio.atlassian.net/browse/BH-1053) |
| ⬜ | Post-demo | BH-1055 dispatcher concurrency hardening | [BH-1055](https://brighthiveio.atlassian.net/browse/BH-1055) |
| ⬜ | Post-demo | BH-1059 AgentCore/CEMAF migration tracking for the dispatcher's LangGraph Cloud dependency | [BH-1059](https://brighthiveio.atlassian.net/browse/BH-1059) |
| ⬜ | Post-demo | BH-1060 customer-PII redaction evaluation for diagnosis text | [BH-1060](https://brighthiveio.atlassian.net/browse/BH-1060) |
| ⬜ | Post-demo | BH-1037/1048-1052 ingestion observability (Airbyte/Step-Functions/queue watchdogs) — not named in Frank's 3 points, build after Track B lands | [BH-1048](https://brighthiveio.atlassian.net/browse/BH-1048), [BH-1049](https://brighthiveio.atlassian.net/browse/BH-1049), [BH-1050](https://brighthiveio.atlassian.net/browse/BH-1050), [BH-1051](https://brighthiveio.atlassian.net/browse/BH-1051), [BH-1052](https://brighthiveio.atlassian.net/browse/BH-1052) |
| ⬜ | Post-demo | BH-115/1038-1041 BrightRoutines MCP/A2A surface — separate concern, unaffected by Track B | [BH-1038](https://brighthiveio.atlassian.net/browse/BH-1038), [BH-1039](https://brighthiveio.atlassian.net/browse/BH-1039), [BH-1040](https://brighthiveio.atlassian.net/browse/BH-1040), [BH-1041](https://brighthiveio.atlassian.net/browse/BH-1041) |


## 🏁 Who's done what

**Lanes**
- **Kuri Chinca** — All engineering tickets currently assigned (BH-1038–1060) — see phases below for suggested split if delegated
- **Suzanne** — Client relationship, demo script, sales-gate commitments
- **Matt** — Kickoff logistics, BrightHive Studio setup, client-side asset coordination

| Owner | ✅ Done | 🔵 In flight | 🟡 Queued | Last shipped |
|---|---|---|---|---|
| **Kuri Chinca** | 1 | 1 | 32 | [BH-1065](https://brighthiveio.atlassian.net/browse/BH-1065) verify: does anything render anomaly… |

## 📊 Summary

- **1/34** tickets done · 0 in progress · 33 to do
- PRs: 4 merged · 0 ready for review · 1 draft

## 📋 Tickets by status

### 🟡 To Do (32)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-1036](https://brighthiveio.atlassian.net/browse/BH-1036) | Monitoring Agents — proactive pipeline discovery &amp; health (dbt,… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#96](https://github.com/brighthive/agentic-project-mgmt/pull/96)<br>[🟢 Merged agentic-project-mgmt#94](https://github.com/brighthive/agentic-project-mgmt/pull/94) |
| [BH-1037](https://brighthiveio.atlassian.net/browse/BH-1037) | Ingestion Observability — source syncs, batch, and event-processing… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#94](https://github.com/brighthive/agentic-project-mgmt/pull/94) |
| [BH-1038](https://brighthiveio.atlassian.net/browse/BH-1038) | spec(routines): MCP/A2A surface for routine suggestions — list/schedu… | Kuri Chinca | — |
| [BH-1039](https://brighthiveio.atlassian.net/browse/BH-1039) | feat(mcp): expose routineSuggestionsForWorkspace + schedule/dismiss… | Kuri Chinca | — |
| [BH-1040](https://brighthiveio.atlassian.net/browse/BH-1040) | feat(mcp): expose scheduledRoutinesForWorkspace + unscheduleRoutine… | Kuri Chinca | — |
| [BH-1041](https://brighthiveio.atlassian.net/browse/BH-1041) | test(e2e): MCP client end-to-end — list/schedule/dismiss routine… | Kuri Chinca | — |
| [BH-1042](https://brighthiveio.atlassian.net/browse/BH-1042) | spec(monitoring): pipeline monitoring agent — project → pipeline… | Kuri Chinca | — |
| [BH-1043](https://brighthiveio.atlassian.net/browse/BH-1043) | feat(monitoring): dbt job/run health poller — detect failed/stale… | Kuri Chinca | — |
| [BH-1044](https://brighthiveio.atlassian.net/browse/BH-1044) | feat(monitoring): Databricks job/cluster health adapter (DatabricksPo… | Kuri Chinca | — |
| [BH-1045](https://brighthiveio.atlassian.net/browse/BH-1045) | feat(monitoring): generic ETL pipeline adapter port + registry entry | Kuri Chinca | — |
| [BH-1046](https://brighthiveio.atlassian.net/browse/BH-1046) | feat(monitoring): proactive alert path — detected issue → Slack/inbox… | Kuri Chinca | — |
| [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) | feat(monitoring): auto-remediation loop for known fix patterns… | Kuri Chinca | — |
| [BH-1048](https://brighthiveio.atlassian.net/browse/BH-1048) | spec(ingestion-obs): source sync / batch / event-processing… | Kuri Chinca | — |
| [BH-1049](https://brighthiveio.atlassian.net/browse/BH-1049) | feat(ingestion-obs): Airbyte/source-sync health signals surfaced to… | Kuri Chinca | — |
| [BH-1050](https://brighthiveio.atlassian.net/browse/BH-1050) | feat(ingestion-obs): batch job observability (Step Functions… | Kuri Chinca | — |
| [BH-1051](https://brighthiveio.atlassian.net/browse/BH-1051) | feat(ingestion-obs): event-processing (streaming/queue) lag +… | Kuri Chinca | — |
| [BH-1052](https://brighthiveio.atlassian.net/browse/BH-1052) | feat(ingestion-obs): unify ingestion signals into the monitoring… | Kuri Chinca | — |
| [BH-1053](https://brighthiveio.atlassian.net/browse/BH-1053) | decision+fix(notifications): EventBridge dispatcher (Path A) is… | Kuri Chinca | — |
| [BH-1054](https://brighthiveio.atlassian.net/browse/BH-1054) | feat(monitoring): watchdog poller — the actual missing proactivity… | Kuri Chinca | — |
| [BH-1055](https://brighthiveio.atlassian.net/browse/BH-1055) | infra(dispatcher): add concurrency cap + fan-out load test to… | Kuri Chinca | — |
| [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) | URGENT: provision staging BYOW SQL Server connection — 7/17 demo… | Kuri Chinca | — |
| [BH-1058](https://brighthiveio.atlassian.net/browse/BH-1058) | provision a dbt Cloud job that can be deliberately triggered to… | Kuri Chinca | — |
| [BH-1059](https://brighthiveio.atlassian.net/browse/BH-1059) | track: scheduled_agent_dispatcher's LangGraph Cloud dependency is… | Kuri Chinca | — |
| [BH-1060](https://brighthiveio.atlassian.net/browse/BH-1060) | security: evaluate customer PII/data-value redaction for diagnosis… | Kuri Chinca | — |
| [BH-1062](https://brighthiveio.atlassian.net/browse/BH-1062) | feat(dbt-lineage): fetch + parse manifest.json/catalog.json,… | Kuri Chinca | — |
| [BH-1063](https://brighthiveio.atlassian.net/browse/BH-1063) | feat(lineage): load parsed dbt/Databricks DAG into Neo4j as… | Kuri Chinca | — |
| [BH-1064](https://brighthiveio.atlassian.net/browse/BH-1064) | feat(lineage): wire longitudinal-monitoring anomalies to walk the… | Kuri Chinca | — |
| [BH-1066](https://brighthiveio.atlassian.net/browse/BH-1066) | feat: render longitudinal anomaly notifications in Slack + webapp… | Kuri Chinca | — |
| [BH-1067](https://brighthiveio.atlassian.net/browse/BH-1067) | feat: renderers for 5 new watchdog notification stages (Slack +… | Kuri Chinca | — |
| [BH-1068](https://brighthiveio.atlassian.net/browse/BH-1068) | feat(lineage): Snowflake-native lineage adapter (Snowpipe/Tasks/Strea… | Kuri Chinca | — |
| [BH-1069](https://brighthiveio.atlassian.net/browse/BH-1069) | feat(lineage): brightbot call site for upsert_lineage_graph (BH-1063a) | Kuri Chinca | — |
| [BH-1070](https://brighthiveio.atlassian.net/browse/BH-1070) | test: add missing unit/integration test coverage for metric-snapshot.… | Kuri Chinca | — |

### 🔵 In Review (1)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-1061](https://brighthiveio.atlassian.net/browse/BH-1061) | Lineage-Aware Data Quality — glue dbt/Databricks' own lineage to… | Kuri Chinca | [🟡 Draft agentic-project-mgmt#97](https://github.com/brighthive/agentic-project-mgmt/pull/97)<br>[🟢 Merged agentic-project-mgmt#95](https://github.com/brighthive/agentic-project-mgmt/pull/95) |

### ✅ Done (1)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-1065](https://brighthiveio.atlassian.net/browse/BH-1065) | verify: does anything render anomaly JSON metadata into a visible… | Kuri Chinca | — |


## 🕒 Recent activity (14 days)

- **2026-07-12** · [BH-1042](https://brighthiveio.atlassian.net/browse/BH-1042) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1059](https://brighthiveio.atlassian.net/browse/BH-1059) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1060](https://brighthiveio.atlassian.net/browse/BH-1060) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1058](https://brighthiveio.atlassian.net/browse/BH-1058) — To Do · Kuri Chinca
- **2026-07-12** · [BH-1055](https://brighthiveio.atlassian.net/browse/BH-1055) — To Do · Kuri Chinca
- **2026-07-12** · [BH-1052](https://brighthiveio.atlassian.net/browse/BH-1052) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1049](https://brighthiveio.atlassian.net/browse/BH-1049) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1044](https://brighthiveio.atlassian.net/browse/BH-1044) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1062](https://brighthiveio.atlassian.net/browse/BH-1062) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1050](https://brighthiveio.atlassian.net/browse/BH-1050) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1051](https://brighthiveio.atlassian.net/browse/BH-1051) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1063](https://brighthiveio.atlassian.net/browse/BH-1063) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1054](https://brighthiveio.atlassian.net/browse/BH-1054) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1046](https://brighthiveio.atlassian.net/browse/BH-1046) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1070](https://brighthiveio.atlassian.net/browse/BH-1070) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) — To Do · Kuri Chinca
- **2026-07-12** · [BH-1045](https://brighthiveio.atlassian.net/browse/BH-1045) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1069](https://brighthiveio.atlassian.net/browse/BH-1069) — Needs Refinement · Kuri Chinca
- **2026-07-12** · [BH-1064](https://brighthiveio.atlassian.net/browse/BH-1064) — Needs Refinement · Kuri Chinca

_(+14 older updates not shown.)_

## 📝 Daily Notes

<!-- TRACKER:MANUAL:BEGIN daily-notes -->

_Filled during the trial — one entry per trial day. Use `### Day N — YYYY-MM-DD` headings._

<!-- TRACKER:MANUAL:END daily-notes -->

## ❓ Open Questions

<!-- TRACKER:MANUAL:BEGIN open-questions -->

_Questions for the customer or for the team. Mark `(customer)` or `(team)` and date-stamp on resolution._

<!-- TRACKER:MANUAL:END open-questions -->
