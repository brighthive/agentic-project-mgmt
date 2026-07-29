# Loopcapital — Live Tracker

_Last refreshed **2026-07-29 04:45 UTC** by `make loopcapital-tracker`. Auto sections are overwritten — manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, ❓ Open Questions) are preserved._

> **Trial dates**: Demo 1: 2026-07-09 (done) — Demo 2 / decision gate: 2026-07-17 · **Epic**: [BH-1036](https://brighthiveio.atlassian.net/browse/BH-1036)

---

## 🚨 Blockers

<!-- TRACKER:MANUAL:BEGIN blockers -->

**🚨 (no ticket) — Trial cannot start: 5 items still needed from Loop Capital** (raised 2026-07-28,
from `artifacts/2026-07-client-docs-trial-scope-and-demo.md` Doc 1, "What Brighthive needs from
Loop Capital"). None of these block the Demo (Doc 2, hosted workspace on representative data) —
they block the live SQL Server 2019 Trial connection (Doc 1) specifically. 🔲 = awaiting Loop Capital.

| | Item | Detail |
|---|---|---|
| 🔲 | Server reachability | DNS name/public IP for the SQL Server 2019 VM + confirmation TCP 1433 is reachable from Brighthive's provided static egress IP |
| 🔲 | Dedicated SQL login | Least-privilege login: read on in-scope DBs + read on SSISDB/ReportServer catalogs + SQL Agent job/disk views |
| 🔲 | In-scope DB list | Which databases are in scope for the trial |
| 🔲 | SSISDB/ReportServer confirmation | Confirm packages are deployed to SSISDB / reports to ReportServer catalog, OR provide the `.dtsx`/`.rdl` files directly |
| 🔲 | Known-bad sample artifacts | A couple of representative "known-bad" artifacts (a flawed SSIS package, a slow SSRS report, a quality-issue table) for recognizable diagnosis demos |

Timeline per Frank's Slack note: server ready "early next week" — live connection walkthrough
(connect together, catalog a database, run first quality check + health check live) is held
until then.

**Consolidated readiness snapshot**: [`TRIAL_STATEMENT.md`](TRIAL_STATEMENT.md) — aggregates
epic `BH-1245`, spec `docs/specs/loopcapital-trial-readiness.md`, tickets `BH-1246`–`BH-1254`,
`SECURITY_REVIEW_GATE.md`, and `TRIAL_FLOW.md` into one page. Start there for Trial status.

**🚨 (no ticket) — Snowflake MFA enrollment blocks live `get_lineage` + lineage-graph population** (raised 2026-07-16 by @kuri). The dbt-mcp `get_lineage` parse step now genuinely succeeds (finds the real model + source), but a full run fails on Snowflake demanding MFA enrollment for the dbt Cloud service account. Needs Snowflake account-admin access — not fixable in-session. The other two infra bugs on this path (GitHub App authorization + dbt Cloud repo↔project linking) were **fixed** 2026-07-16 — writeup: `platform-saas-ai-context/docs/architecture/DBT_CLOUD_LEARNINGS.md`. **Demo impact**: §2 (lineage) and §6 (bronze/silver/gold graph) are demoable as **real, tested code you show and explain**, not a live "watch it answer" moment on Loop Capital's own project. Do NOT script these as live chat questions.

<!-- TRACKER:MANUAL:END blockers -->

## 🎯 This Week

<!-- TRACKER:MANUAL:BEGIN this-week -->

**2026-07-17 — Demo 2 / decision gate with Frank (T-0).** Run sheet is `demo.md` (every claim verified against deployed staging code + a passing test the day it was written). Priorities, in order:

1. **Lead with the proactive loop (GC-14 → GC-17)** — the strongest, most demoable capability and the direct answer to all three of Suzanne's commitments to Frank. Show the Slack alert → the agent's diagnosis in chat → open the real merged PR `brighthive-dbt/loopcapital-dbt-demo#1` to prove it isn't a mock (MERGED-by-a-human = the never-auto-merge safety gate, demoed).
2. **SQL Server, no MCP (GC-15)** — Frank's literal named example; demo the disk-low alert against the real Docker sandbox, not a mock.
3. **Legacy Analyst Analyzer (§5)** — SSIS/SSRS diagnosis against Loop Capital's own real sandbox artifacts; storage optimization live against OneTen's real Snowflake. Set the timing expectation (SSIS package read takes 3–9 min — kick it early).
4. **Run `demo.md`'s pre-demo checklist ~30 min before** — do not demo against a red check.
5. Be upfront about the honest gaps (see 🚨 Blockers and ❓ Open Questions) — the "not yet, here's exactly what's blocking it" framing is stronger than a vague "it's real but variable."

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

### Track B, Point 1 — Proactive monitor/detect/alert loop (GC-14) (0/6 🟢, 3 🟡)

_Suzanne's demo commitment #1: "the engineering agent and how it proactively monitors, detects and resolves issues with the ability to alert the user on what it finds." This is the watchdog capability node — the actual missing-proactivity primitive this whole spec was built to close. Golden Case: docs/specs/golden-cases-loopcapital.md#GC-14 (Frank's ops team learns their nightly Asset Management dbt job broke before a portfolio manager asks why the SSRS holdings report looks wrong)._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | T-5 (by 2026-07-12) | BH-1042 contract finalized — types/registry/MCP tool, no ambiguity for implementers | [BH-1042](https://brighthiveio.atlassian.net/browse/BH-1042) |
| 🟡 | T-4 | BH-1054 watchdog node registered + wired to existing scheduled dispatcher | [BH-1054](https://brighthiveio.atlassian.net/browse/BH-1054) |
| 🟡 | T-4 | BH-1043 dbt job/run health poller — detects a real failed run | [BH-1043](https://brighthiveio.atlassian.net/browse/BH-1043) |
| 🟡 | T-3 | BH-1046 alert path — Slack + webapp both show the detected failure (dual-write verified) | [BH-1046](https://brighthiveio.atlassian.net/browse/BH-1046) |
| ⬜ | T-3 | CRITICAL, filed pass 35: BH-1067 renderers for 5 of 6 new stage values — dual-write alone is not enough; dbt_run_stale/databricks_job_failure/databricks_cluster_unhealthy/etl_job_failure/source_disk_low have zero visible text on either surface without this, identical to GC-12's confirmed dead-end (BH-1065/1066) | [BH-1067](https://brighthiveio.atlassian.net/browse/BH-1067) |
| ⬜ | T-2 | End-to-end dry run: real dbt Cloud failure (BH-1058 fixture) → detected unprompted → alerted on both surfaces | [BH-1058](https://brighthiveio.atlassian.net/browse/BH-1058) |

### Track B, Point 2 — SQL Server with no MCP (disk-space monitoring) (GC-15) (2/4 🟢, 2 🟡)

_Suzanne's demo commitment #2, Frank's literal named example: "how MCP will connect to the SQL server when the server does not have an MCP... monitoring the disk space and alerting when it's at 20% capacity left." Direct rebuttal to Frank's stated disbelief that this is technically possible — must be demoed against REAL infrastructure per test-behavior-real.md, not a mock, since a mocked page is exactly what triggered his "this is not live" reaction on 2026-07-09. Golden Case: docs/specs/golden-cases-loopcapital.md#GC-15._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🟢 | T-5 — DONE 2026-07-13 | BH-1057: local Docker SQL Server sandbox built + verified (clients/trials/loopcapital/sandbox/), replaces the original AWS RDS plan. SQL Server Agent enabled via MSSQL_AGENT_ENABLED, no billable resource needed. | [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) |
| 🟡 | T-4 | BH-1045 disk/job query wired through existing WarehousePort/SynapseConnection chain — zero new connectivity | [BH-1045](https://brighthiveio.atlassian.net/browse/BH-1045) |
| 🟢 | T-3 — DONE 2026-07-13 | Demo data seeded: sandbox's fill_disk.sh verified real ~18% free space, real SQL Server Agent jobs (one real Succeeded, one real Failed run) — run ./setup.sh before the demo | [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) |
| 🟡 | T-2 | Dry run: watchdog polls real SQL Server, detects low disk, alerts — no MCP on the SQL Server side, ever. Requires BH-1067's source_disk_low renderer to actually show text (detection without it is silent). | [BH-1045](https://brighthiveio.atlassian.net/browse/BH-1045), [BH-1054](https://brighthiveio.atlassian.net/browse/BH-1054), [BH-1067](https://brighthiveio.atlassian.net/browse/BH-1067) |

### Track B, Point 3 — Fix-recurrence surfacing (GC-16, gated on GC-17) (0/4 🟢, 4 🟡)

_Suzanne's demo commitment #3: "the ability to build skills that help surface the fixes the agent applied when they are not abided by so we can avoid the recurrence of the same kind of issue." Mechanism: self-healing-pipelines.md's surgical-PR loop (GC-11), wired to this spec's watchdog signals — with a CRITICAL safety fix required first (see below). Golden Cases: docs/specs/golden-cases-loopcapital.md#GC-16 (the demo scene — a recurring pipeline break gets a reviewable PR, never an auto-merge) and #GC-17 (the safety precondition GC-16 cannot demo without — GC-17 is its own gating case, not a sub-step of GC-16, and is the cheapest of the four to make live since it needs no infrastructure)._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🟡 | T-5 | GC-17 (safety precondition, cheapest to unblock — pure static test, no infra dependency): BH-1047's code-level exclusion of github_merge_pull_request from the remediation loop's tool list — 'never auto-merge' was previously prompt-only, zero code enforcement | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |
| 🟡 | T-4 | root_cause_class classifier wired (DATA_SHAPE vs JOB_RUNTIME) — routes correctly, never fabricates a fix | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |
| 🟡 | T-3 | DATA_SHAPE signal routes into GC-11's existing surgical-PR loop, human-approval-gated | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |
| 🟡 | T-2 | GC-16 demo dry run: a detected failure surfaces a surgical PR with a plain-language diagnosis, requires human approval, never auto-merges — requires GC-17 to have already passed | [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) |

### T-1 — Full dress rehearsal (0/0 🟢)

_Run the entire demo script end-to-end against real staging infrastructure, exactly as it will be shown to Frank. No mocks — this is the whole point after 2026-07-09's "this is not live" reaction._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | T-1 (2026-07-16) | All 3 points demoed live: watchdog detects a real dbt failure; SQL Server disk-low alert fires from the real Docker sandbox; a surgical PR opens and is shown NOT auto-merging | _manual_ |
| 🔲 | T-1 | Demo script + talking points finalized (Suzanne/Matt) | _manual_ |

### T-0 — Demo day (0/0 🟢)

_Decision gate._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | 2026-07-17 | Demo delivered to Frank | _manual_ |
| 🔲 | Post | Decision recorded (Won / Lost / Extended) with rationale | _manual_ |

### Track C — Lineage-aware data quality (post-demo, honest framing for 7/17) (0/8 🟢)

_New capability, scoped 2026-07-12 after Kuri's example: a pipeline can run with ZERO errors while a source column silently degrades (NULLs where real values used to be), poisoning Gold/Diamond numbers with no alert anywhere. NOT achievable by 7/17 — this is genuinely new, multi-week work. Full spec: docs/specs/lineage-aware-data-quality.md. For the demo: show the anomaly-detection half (real, shipped, GC-12) and frame the lineage-tracing half honestly as "we glue dbt/Databricks' own lineage to what they can't see themselves" — a real differentiator, not a gap to hide._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Post-demo | BH-1062 — fetch + parse dbt manifest.json/catalog.json (reuses existing artifact-fetch plumbing) | [BH-1062](https://brighthiveio.atlassian.net/browse/BH-1062) |
| ⬜ | Post-demo | BH-1063 (platform-core, 2-3 files confirmed pass 6 — no public schema touch, mirrors AnomalyEventNode's cheaper OGM-only pattern) — load parsed DAG into Neo4j as a queryable lineage graph. CORRECTED pass 50: that mirror is incomplete for tenancy — LineageNode needs its own native workspaceId field, since its dependsOn relationship (unlike AnomalyEventNode's dataAsset) never chains to WorkspaceNode. | [BH-1063](https://brighthiveio.atlassian.net/browse/BH-1063) |
| ⬜ | Post-demo | BH-1064 — wire anomaly events to walk the graph forward, closing the already-deferred BH-673 bridge. Traversal MUST match on LineageNode.relationName (never uniqueId/name, pass 10), reuse the org's existing _fqn_variants() normalization for real format drift (pass 46), AND filter on workspaceId (pass 50) — three real correctness/isolation requirements, not one. | [BH-1064](https://brighthiveio.atlassian.net/browse/BH-1064) |
| ⬜ | Post-demo | BH-1066 — CONFIRMED pass 5: GC-12 anomaly notifications have zero rendering in Slack/webapp today, independent of this epic's own changes. BH-1064's enrichment has nothing to enrich that a human sees until this ships. | [BH-1066](https://brighthiveio.atlassian.net/browse/BH-1066) |
| ⬜ | Post-demo | BH-1068 — Snowflake-native lineage adapter (Snowpipe/Tasks/Streams/Dynamic Tables via ACCOUNT_USAGE) — cheaper than the Databricks half connection-wise, reuses the existing SnowflakeConnection. CORRECTED pass 45: needs a permission/latency guard too — the recommended least-privilege role posture silently fails ACCOUNT_USAGE reads (already happened once in this org's real Longaeva POC role, #825), so this is not free just because the connection is reused. | [BH-1068](https://brighthiveio.atlassian.net/browse/BH-1068) |
| ⬜ | Post-demo | BH-1069 — brightbot call site for upsert_lineage_graph (formerly informal 'BH-1063a'), real ogm_api.py plumbing + GraphQL-errors-key check. ADDED pass 49: the per-model loop MUST share ONE OGMAPISession, not the bare default — that idiom re-authenticates via a live Cognito login on every construction, safe for existing once-per-turn call sites but not for a per-model loop over a real manifest's hundreds of models. | [BH-1069](https://brighthiveio.atlassian.net/browse/BH-1069) |
| ⬜ | Post-demo | BH-1070 — test coverage gap: metric-snapshot.ts (BH-1063b's own cited precedent) has zero existing tests; non-blocking tech debt, tracked for visibility | [BH-1070](https://brighthiveio.atlassian.net/browse/BH-1070) |
| ⬜ | Post-demo | BH-1074 — filed pass 72: Databricks lineage adapter (DatabricksLineageSource) closes Gap 4, which had NO ticket of any kind despite every other spec gap being tracked. Distinct from BH-1044 (Track B's Databricks job/cluster health monitoring — a different Protocol, easily confused since both are 'the Databricks ticket'). | [BH-1074](https://brighthiveio.atlassian.net/browse/BH-1074) |

### Non-blocking, tracked separately (0/7 🟢)

_Real work, correctly scoped OUT of the 7/17 critical path — don't let these stall Track B above._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Post-demo | BH-1044 Databricks credential storage/lookup design — RESOLVED pass 24 to a concrete pattern (mirror dbt's per-connection direct-boto3 secret read, keyed on workspace_id+service_id, no caching); ticket status is Needs Refinement (design settled, code not yet built), no longer an open decision | [BH-1044](https://brighthiveio.atlassian.net/browse/BH-1044) |
| ⬜ | Post-demo | BH-1053 BrightSignals 3-way split-brain unification | [BH-1053](https://brighthiveio.atlassian.net/browse/BH-1053) |
| ⬜ | Post-demo | BH-1055 dispatcher concurrency hardening | [BH-1055](https://brighthiveio.atlassian.net/browse/BH-1055) |
| ⬜ | Post-demo | BH-1059 AgentCore/CEMAF migration tracking for the dispatcher's LangGraph Cloud dependency | [BH-1059](https://brighthiveio.atlassian.net/browse/BH-1059) |
| ⬜ | Post-demo | BH-1060 customer-PII redaction decision for diagnosis text across ALL 4 real sinks (Slack, webapp inbox, GitHub PR body, AND CloudWatch audit logs via @audit_action — the 4th sink confirmed pass 28, not in the original 3-sink framing); scrub_text() only catches secret shapes (JWT/API-key/etc.), not PII values — non-blocking for 7/17, real gap before production customer data | [BH-1060](https://brighthiveio.atlassian.net/browse/BH-1060) |
| ⬜ | Post-demo | BH-1037/1048-1052 ingestion observability (Airbyte/Step-Functions/queue watchdogs) — not named in Frank's 3 points, build after Track B lands | [BH-1048](https://brighthiveio.atlassian.net/browse/BH-1048), [BH-1049](https://brighthiveio.atlassian.net/browse/BH-1049), [BH-1050](https://brighthiveio.atlassian.net/browse/BH-1050), [BH-1051](https://brighthiveio.atlassian.net/browse/BH-1051), [BH-1052](https://brighthiveio.atlassian.net/browse/BH-1052) |
| ⬜ | Post-demo | BH-115/1038-1041 BrightRoutines MCP/A2A surface — separate concern, unaffected by Track B | [BH-1038](https://brighthiveio.atlassian.net/browse/BH-1038), [BH-1039](https://brighthiveio.atlassian.net/browse/BH-1039), [BH-1040](https://brighthiveio.atlassian.net/browse/BH-1040), [BH-1041](https://brighthiveio.atlassian.net/browse/BH-1041) |

### Track E — Agentic SQL Server profiling & DB-level quality health checks (added pass 81, tickets filed pass 82, user-raised) (0/3 🟢, 2 🟡)

_Kuri's follow-up ask (2026-07-13): part of the broader BrightHive SaaS vision, connect MCP against Microsoft SQL Server so a legacy DB can be agentically identified, scanned, and quality-health-checked — a PROFILER at the DB/warehouse level, not just per-table. Verified: most plumbing already exists (SynapseConnection already connects to bare SQL Server with zero code changes; introspect_warehouse_schema already does warehouse-level table discovery with no pre-registered DataAssetNode needed) but the profiler/quality- check layer is entirely asset-ID-gated today — no "point it at a whole DB" mode exists, and discovery + profiling are never chained end to end. See docs/specs/proactive-pipeline-ingestion-monitoring.md's new "Track E" section for full detail. Naming decision (is SQL Server a distinct WarehouseType, or a reuse of azure_synapse's connector?) RESOLVED pass 82 against the real webapp UI convention — a genuine new connection type, not a reuse. 3 tickets filed under epic BH-1036._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🟡 | Post-demo | BH-1075 — new sql_server WarehouseType/WarehouseServiceProvider connection type across brightbot/platform-core/webapp; connector code reuses SynapseConnection unchanged, only the enum/UI discriminator is new | [BH-1075](https://brighthiveio.atlassian.net/browse/BH-1075) |
| 🟡 | Post-demo | BH-1076 — new orchestration chaining introspect_warehouse_schema (discovery) -> per-table profiling (quality_check_agent/analyze_dataset_structure) for tables with no pre-registered DataAssetNode | [BH-1076](https://brighthiveio.atlassian.net/browse/BH-1076) |
| ⬜ | Post-demo | BH-1077 — a new DB-level (not per-table) summary report shape aggregating BH-1076's per-table outputs — today's profiler output is always per-asset, never rolled up | [BH-1077](https://brighthiveio.atlassian.net/browse/BH-1077) |

### Trial (Doc 1) — 9 numbered success criteria (0/9 🟢)

_Client-facing "Trial Scope & Success Criteria" doc sent to Frank Sung 2026-07-28. Source: artifacts/2026-07-client-docs-trial-scope-and-demo.md Doc 1. Core = 1-4, 7-8; Supporting = 5, 6, 9. This is the Trial (live SQL Server 2019 connection into Loop Capital's own Azure VM) — a distinct engagement from the Demo tracked in the next phase; do not merge the two. Blocked from starting at all until the 5 items in the Blockers section above are resolved. Cross-reference to internal GC-14..17 mechanism per LOOPCAPITAL.md's success-criteria mapping table. Spec: docs/specs/loopcapital-trial-readiness.md. Tracking moved to its own epic BH-1245 ("Loop Capital Trial Execution") — each row below links to its verification ticket (BH-1246-BH-1254); none are Done since the underlying mechanism has only run against sandbox/EC2 stand-ins, never Loop Capital's real server._

| | Day | Outcome | Linked |
|---|---|---|---|
| ⬜ | Core — #1 | Connect & catalog — browsable catalog (tables/columns/types) shortly after credentials received. No SQL Server connector work started; also gated on blocker items 1-3. | [BH-1246](https://brighthiveio.atlassian.net/browse/BH-1246) |
| ⬜ | Core — #2 | Data quality on their data — quality score + readable report + generated SQL, plain-language root cause. Quality-agent capability exists per Doc 2 demo bullets; not yet run against Loop Capital's own SQL Server. | [BH-1247](https://brighthiveio.atlassian.net/browse/BH-1247) |
| ⬜ | Core — #3 | Ask in plain language — business question answered correctly, SQL shown. Not yet run against Loop Capital's own SQL Server. | [BH-1248](https://brighthiveio.atlassian.net/browse/BH-1248) |
| ⬜ | Core — #4 | Proactive SQL Server health — unprompted, names a specific job failure or disk-pressure condition. Analogous in spirit to GC-15 but GC-15 is not demo-gating internally — verify separately for the Trial. | [BH-1249](https://brighthiveio.atlassian.net/browse/BH-1249) |
| ⬜ | Supporting — #5 | SSIS diagnostics — >=1 true structural issue on a package/.dtsx. Legacy Analyst Analyzer (Track A) ships this capability class against sandbox artifacts; not yet run against Loop Capital's real .dtsx/deployed packages. | [BH-1250](https://brighthiveio.atlassian.net/browse/BH-1250) |
| ⬜ | Supporting — #6 | SSRS diagnostics — >=1 true performance anti-pattern on a report/.rdl. Capability exists (Track A), not yet run against Loop Capital's real artifacts. | [BH-1251](https://brighthiveio.atlassian.net/browse/BH-1251) |
| ⬜ | Core — #7 | Autonomy loop (headline) — detect -> diagnose -> governed PR -> pause for approval in Slack -> cannot self-approve. Internal mechanism may exist (GC-16/GC-17, BH-1047's code-level github_merge_pull_request exclusion) — verify against Loop Capital's own stack before marking done, and explicitly test the Slack-approval-gate, not just GitHub-PR-review. | [BH-1252](https://brighthiveio.atlassian.net/browse/BH-1252) |
| ⬜ | Core — #8 | Governed & auditable — tamper-evident audit trail, PII tagged, nothing written without review. Internal mechanism may exist (GC-17's binding-layer exclusion is one input); PII tagging (BH-1060) is a confirmed code gap, now escalated — gated on BH-1060 reaching Ready for Dev before running against real data. | [BH-1253](https://brighthiveio.atlassian.net/browse/BH-1253) |
| ⬜ | Supporting — #9 | Platform capability — external agent calls governed MCP lookups, BrightAgent proposes a recurring routine. Scoped to the hosted demo workspace (Doc 2 territory), gated on BH-1172/BH-1038-1041. | [BH-1254](https://brighthiveio.atlassian.net/browse/BH-1254) |

### Demo (Doc 2) — Your Brighthive Demo, What to Expect (0/1 🟢)

_Pre-POC guided walkthrough on representative/synthetic data — a separate engagement from the Trial above, run in the hosted Brighthive demo workspace, not a live connection into Loop Capital's environment. Source: same artifacts file, Doc 2. Items below are what the doc commits to showing live; the deferred-to-POC integration table (Synapse/Databricks/ADLS/Entra ID SSO/ADF/Snowflake Cortex/Power BI/governance-at-scale) is explicitly NOT tracked here since none of it is scoped to this Demo or the Trial._

| | Day | Outcome | Linked |
|---|---|---|---|
| 🔲 | Demo | Governed multi-agent workflow end-to-end (Quality Agent -> Engineering Agent PR -> human merge). Overlaps in spirit with GC-14/16/17 internal mechanism, but on representative demo data, not Loop Capital's own environment. | _manual_ |
| 🔲 | Demo | Ask a question, see the reasoning (NL question -> SQL shown -> viz gated on governance checks). Not yet verified against the demo-workspace surface specifically. | _manual_ |
| ⬜ | Demo | Governance that runs (auto PII tagging, lineage, policy enforcement, audit trail). Cross-check against BH-1060 (PII redaction) before claiming live. | [BH-1060](https://brighthiveio.atlassian.net/browse/BH-1060) |
| 🔲 | Demo | Orchestration & Slack (BrightAgent supervisor routing, proactive alerts + approvals). | _manual_ |
| 🔲 | Demo | MCP interface + OSI preview (external agent e.g. Claude in an IDE calling governed MCP lookups; OSI export previewed). OSI framed as emerging standard, not overclaimed, per Doc 2. | _manual_ |
| 🔲 | Demo | Legacy-aware analysis (SSIS/SSRS diagnostics + storage-cost optimization scan on demo data). Capability shipped per Track A (COMPLETE) — verify it's wired into the demo-workspace walkthrough specifically, not just the sandbox. | _manual_ |


## 🏁 Who's done what

**Lanes**
- **Kuri Chinca** — All engineering tickets currently assigned (BH-1038–1060) — see phases below for suggested split if delegated
- **Suzanne** — Client relationship, demo script, sales-gate commitments
- **Matt** — Kickoff logistics, BrightHive Studio setup, client-side asset coordination

| Owner | ✅ Done | 🔵 In flight | 🟡 Queued | Last shipped |
|---|---|---|---|---|
| **Kuri Chinca** | 2 | 8 | 35 | [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) provision the Loop Capital SQL Server… |
| **_unassigned_** | 0 | 1 | 22 | — |

## 📊 Summary

- **2/68** tickets done · 6 in progress · 60 to do
- PRs: 197 merged · 1 ready for review · 6 draft

## 📋 Tickets by status

### 🟡 To Do (57)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-1037](https://brighthiveio.atlassian.net/browse/BH-1037) | Ingestion Observability — source syncs, batch, and event-processing… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#94](https://github.com/brighthive/agentic-project-mgmt/pull/94) |
| [BH-1038](https://brighthiveio.atlassian.net/browse/BH-1038) | spec(routines): MCP/A2A surface for routine suggestions — list/schedu… | Kuri Chinca | — |
| [BH-1039](https://brighthiveio.atlassian.net/browse/BH-1039) | feat(mcp): expose routineSuggestionsForWorkspace + schedule/dismiss… | Kuri Chinca | — |
| [BH-1040](https://brighthiveio.atlassian.net/browse/BH-1040) | feat(mcp): expose scheduledRoutinesForWorkspace + unscheduleRoutine… | Kuri Chinca | — |
| [BH-1041](https://brighthiveio.atlassian.net/browse/BH-1041) | test(e2e): MCP client end-to-end — list/schedule/dismiss routine… | Kuri Chinca | — |
| [BH-1042](https://brighthiveio.atlassian.net/browse/BH-1042) | spec(monitoring): pipeline monitoring agent — project → pipeline… | Kuri Chinca | [🟢 Merged brightbot#884](https://github.com/brighthive/brightbot/pull/884)<br>[🟢 Merged brighthive-e2e#62](https://github.com/brighthive/brighthive-e2e/pull/62) |
| [BH-1044](https://brighthiveio.atlassian.net/browse/BH-1044) | feat(monitoring): Databricks job/cluster health adapter (DatabricksPo… | Kuri Chinca | — |
| [BH-1048](https://brighthiveio.atlassian.net/browse/BH-1048) | spec(ingestion-obs): source sync / batch / event-processing… | Kuri Chinca | — |
| [BH-1049](https://brighthiveio.atlassian.net/browse/BH-1049) | feat(ingestion-obs): Airbyte/source-sync health signals surfaced to… | Kuri Chinca | — |
| [BH-1050](https://brighthiveio.atlassian.net/browse/BH-1050) | feat(ingestion-obs): batch job observability (Step Functions… | Kuri Chinca | — |
| [BH-1051](https://brighthiveio.atlassian.net/browse/BH-1051) | feat(ingestion-obs): event-processing (streaming/queue) lag +… | Kuri Chinca | — |
| [BH-1052](https://brighthiveio.atlassian.net/browse/BH-1052) | feat(ingestion-obs): unify ingestion signals into the monitoring… | Kuri Chinca | — |
| [BH-1053](https://brighthiveio.atlassian.net/browse/BH-1053) | decision+fix(notifications): EventBridge dispatcher (Path A) is… | Kuri Chinca | — |
| [BH-1055](https://brighthiveio.atlassian.net/browse/BH-1055) | infra(dispatcher): add concurrency cap + fan-out load test to… | Kuri Chinca | — |
| [BH-1058](https://brighthiveio.atlassian.net/browse/BH-1058) | provision a dbt Cloud job that can be deliberately triggered to… | Kuri Chinca | — |
| [BH-1059](https://brighthiveio.atlassian.net/browse/BH-1059) | track: scheduled_agent_dispatcher's LangGraph Cloud dependency is… | Kuri Chinca | — |
| [BH-1060](https://brighthiveio.atlassian.net/browse/BH-1060) | security: evaluate customer PII/data-value redaction for diagnosis… | Kuri Chinca | [🟢 Merged brightbot#846](https://github.com/brighthive/brightbot/pull/846) |
| [BH-1061](https://brighthiveio.atlassian.net/browse/BH-1061) | Lineage-Aware Data Quality — glue dbt/Databricks' own lineage to… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#101](https://github.com/brighthive/agentic-project-mgmt/pull/101)<br>[🔵 Review agentic-project-mgmt#99](https://github.com/brighthive/agentic-project-mgmt/pull/99)<br>[🟢 Merged agentic-project-mgmt#98](https://github.com/brighthive/agentic-project-mgmt/pull/98) |
| [BH-1062](https://brighthiveio.atlassian.net/browse/BH-1062) | feat(dbt-lineage): fetch + parse manifest.json/catalog.json,… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#104](https://github.com/brighthive/agentic-project-mgmt/pull/104)<br>[🟢 Merged agentic-project-mgmt#100](https://github.com/brighthive/agentic-project-mgmt/pull/100) |
| [BH-1063](https://brighthiveio.atlassian.net/browse/BH-1063) | feat(lineage): load parsed dbt/Databricks DAG into Neo4j as… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#102](https://github.com/brighthive/agentic-project-mgmt/pull/102)<br>[🟢 Merged brightbot-slack-server#128](https://github.com/brighthive/brightbot-slack-server/pull/128) |
| [BH-1064](https://brighthiveio.atlassian.net/browse/BH-1064) | feat(lineage): wire longitudinal-monitoring anomalies to walk the… | Kuri Chinca | — |
| [BH-1066](https://brighthiveio.atlassian.net/browse/BH-1066) | feat: render longitudinal anomaly notifications in Slack + webapp… | Kuri Chinca | — |
| [BH-1067](https://brighthiveio.atlassian.net/browse/BH-1067) | feat: renderers for 5 new watchdog notification stages (Slack +… | Kuri Chinca | [🟢 Merged brightbot-slack-server#143](https://github.com/brighthive/brightbot-slack-server/pull/143)<br>[🟢 Merged brightbot-slack-server#141](https://github.com/brighthive/brightbot-slack-server/pull/141)<br>[🟢 Merged brightbot-slack-server#136](https://github.com/brighthive/brightbot-slack-server/pull/136) |
| [BH-1068](https://brighthiveio.atlassian.net/browse/BH-1068) | feat(lineage): Snowflake-native lineage adapter (Snowpipe/Tasks/Strea… | Kuri Chinca | — |
| [BH-1069](https://brighthiveio.atlassian.net/browse/BH-1069) | feat(lineage): brightbot call site for upsert_lineage_graph (BH-1063a) | Kuri Chinca | — |
| [BH-1070](https://brighthiveio.atlassian.net/browse/BH-1070) | test: add missing unit/integration test coverage for metric-snapshot.… | Kuri Chinca | — |
| [BH-1071](https://brighthiveio.atlassian.net/browse/BH-1071) | docs: NOTIFICATION_SYSTEM_PLAN.md is stale — 4+ claims describe… | Kuri Chinca | — |
| [BH-1074](https://brighthiveio.atlassian.net/browse/BH-1074) | feat(lineage): Databricks lineage adapter (DatabricksLineageSource)… | Kuri Chinca | — |
| [BH-1077](https://brighthiveio.atlassian.net/browse/BH-1077) | feat(quality): DB-level rollup report aggregating per-table… | Kuri Chinca | — |
| [BH-1087](https://brighthiveio.atlassian.net/browse/BH-1087) | feat(monitoring): dbt_run_failure webapp detail parity — platform-cor… | Kuri Chinca | — |
| [BH-1091](https://brighthiveio.atlassian.net/browse/BH-1091) | feat(monitoring): post-merge verification loop — VERIFYING cooldown… | Kuri Chinca | — |
| [BH-1092](https://brighthiveio.atlassian.net/browse/BH-1092) | feat(monitoring): verify surgical PR actually opened after agent… | Kuri Chinca | — |
| [BH-1107](https://brighthiveio.atlassian.net/browse/BH-1107) | Add SQL Server as a UI-connectable warehouse source & destination… | _unassigned_ | [🟢 Merged brightbot#864](https://github.com/brighthive/brightbot/pull/864)<br>[🟢 Merged brightbot#863](https://github.com/brighthive/brightbot/pull/863)<br>[🟢 Merged brighthive-e2e#56](https://github.com/brighthive/brighthive-e2e/pull/56) |
| [BH-1108](https://brighthiveio.atlassian.net/browse/BH-1108) | Surface pipeline health, watchdog findings & PR fix-suggestions… | _unassigned_ | [🟢 Merged brighthive-e2e#48](https://github.com/brighthive/brighthive-e2e/pull/48)<br>[🟢 Merged brighthive-platform-core#1065](https://github.com/brighthive/brighthive-platform-core/pull/1065)<br>[🟢 Merged brighthive-platform-core#1064](https://github.com/brighthive/brighthive-platform-core/pull/1064) |
| [BH-1109](https://brighthiveio.atlassian.net/browse/BH-1109) | Add Microsoft Teams as a notification delivery channel (parity with… | _unassigned_ | [🟢 Merged brighthive-e2e#49](https://github.com/brighthive/brighthive-e2e/pull/49)<br>[🟢 Merged brighthive-platform-core#1067](https://github.com/brighthive/brighthive-platform-core/pull/1067)<br>[🟢 Merged brighthive-platform-core#1066](https://github.com/brighthive/brighthive-platform-core/pull/1066) |
| [BH-1111](https://brighthiveio.atlassian.net/browse/BH-1111) | dbt dependency-edge writer + lineage traversal + DAG viewer (Phase… | _unassigned_ | [🟢 Merged brightbot#873](https://github.com/brighthive/brightbot/pull/873)<br>[🟢 Merged brighthive-e2e#51](https://github.com/brighthive/brighthive-e2e/pull/51) |
| [BH-1113](https://brighthiveio.atlassian.net/browse/BH-1113) | currentUser throws on null firstName/lastName for workspace-owner… | _unassigned_ | [🟢 Merged brighthive-platform-core#1071](https://github.com/brighthive/brighthive-platform-core/pull/1071)<br>[🟢 Merged brighthive-platform-core#1070](https://github.com/brighthive/brighthive-platform-core/pull/1070) |
| [BH-1114](https://brighthiveio.atlassian.net/browse/BH-1114) | Bronze/silver/gold medallion-tier quality gating — no code exists… | _unassigned_ | [🟢 Merged agentic-project-mgmt#123](https://github.com/brighthive/agentic-project-mgmt/pull/123)<br>[🟢 Merged agentic-project-mgmt#122](https://github.com/brighthive/agentic-project-mgmt/pull/122)<br>[🟢 Merged agentic-project-mgmt#121](https://github.com/brighthive/agentic-project-mgmt/pull/121) |
| [BH-1116](https://brighthiveio.atlassian.net/browse/BH-1116) | Ingestion agent self-service: autonomously connect BYOW warehouse… | Kuri Chinca | [🟢 Merged brighthive-platform-core#1076](https://github.com/brighthive/brighthive-platform-core/pull/1076)<br>[🟢 Merged brighthive-platform-core#1075](https://github.com/brighthive/brighthive-platform-core/pull/1075) |
| [BH-1117](https://brighthiveio.atlassian.net/browse/BH-1117) | Analyst agent is blind to warehouse_type; cannot report table… | _unassigned_ | [🟢 Merged brightbot#895](https://github.com/brighthive/brightbot/pull/895)<br>[🟢 Merged brightbot#894](https://github.com/brighthive/brightbot/pull/894)<br>[🟢 Merged brightbot#891](https://github.com/brighthive/brightbot/pull/891) |
| [BH-1118](https://brighthiveio.atlassian.net/browse/BH-1118) | Branded BrightAgent[bot] identity for agent-authored commits and PRs | _unassigned_ | — |
| [BH-1119](https://brighthiveio.atlassian.net/browse/BH-1119) | Semantic view + warehouse answers must be grounded and proactive,… | _unassigned_ | [🟢 Merged brightbot#905](https://github.com/brighthive/brightbot/pull/905)<br>[🟢 Merged brightbot#890](https://github.com/brighthive/brightbot/pull/890) |
| [BH-1120](https://brighthiveio.atlassian.net/browse/BH-1120) | Read-only warehouse SQL tool so the agent runs totals/disk queries… | _unassigned_ | [🟢 Merged brightbot#922](https://github.com/brighthive/brightbot/pull/922)<br>[🟢 Merged brightbot#904](https://github.com/brighthive/brightbot/pull/904)<br>[🟢 Merged brightbot#903](https://github.com/brighthive/brightbot/pull/903) |
| [BH-1167](https://brighthiveio.atlassian.net/browse/BH-1167) | Loop Capital dbt run fails on Snowflake MFA — blocks pipeline… | Kuri Chinca | — |
| [BH-1172](https://brighthiveio.atlassian.net/browse/BH-1172) | MCP surface not deployed in prod — brightagent-mcp.app.brighthive.net… | _unassigned_ | [🟢 Merged brighthive-platform-core#1127](https://github.com/brighthive/brighthive-platform-core/pull/1127) |
| [BH-1175](https://brighthiveio.atlassian.net/browse/BH-1175) | Prod webapp authenticated inner pages never reach networkidle —… | _unassigned_ | — |
| [BH-1178](https://brighthiveio.atlassian.net/browse/BH-1178) | 26 DataAssets in Prod Test Workspace have null tableFQN — backfill gap | Kuri Chinca | — |
| [BH-1245](https://brighthiveio.atlassian.net/browse/BH-1245) | Loop Capital Trial Execution — client-delivery verification of the… | _unassigned_ | — |
| [BH-1246](https://brighthiveio.atlassian.net/browse/BH-1246) | verify(trial): SQL Server connect & catalog against LC's real Azure… | _unassigned_ | — |
| [BH-1247](https://brighthiveio.atlassian.net/browse/BH-1247) | verify(trial): data quality check + SQL-shown against LC's real… | _unassigned_ | — |
| [BH-1248](https://brighthiveio.atlassian.net/browse/BH-1248) | verify(trial): NL question answered with SQL shown against LC's… | _unassigned_ | — |
| [BH-1249](https://brighthiveio.atlassian.net/browse/BH-1249) | verify(trial): proactive SQL Server health against LC's real Azure… | _unassigned_ | — |
| [BH-1250](https://brighthiveio.atlassian.net/browse/BH-1250) | verify(trial): SSIS diagnostics against LC's real deployed packages… | _unassigned_ | — |
| [BH-1251](https://brighthiveio.atlassian.net/browse/BH-1251) | verify(trial): SSRS diagnostics against LC's real reports (criterion… | _unassigned_ | — |
| [BH-1252](https://brighthiveio.atlassian.net/browse/BH-1252) | verify(trial): autonomy loop + Slack-approval-gate against LC's… | _unassigned_ | — |
| [BH-1253](https://brighthiveio.atlassian.net/browse/BH-1253) | verify(trial): governed audit trail + PII tagging against LC's real… | _unassigned_ | — |
| [BH-1254](https://brighthiveio.atlassian.net/browse/BH-1254) | verify(trial): platform capability (MCP external-agent + routine… | _unassigned_ | — |

### 🟢 In Progress (6)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-1043](https://brighthiveio.atlassian.net/browse/BH-1043) | feat(monitoring): dbt job/run health poller — detect failed/stale… | Kuri Chinca | [🟢 Merged brightbot#848](https://github.com/brighthive/brightbot/pull/848)<br>[🟢 Merged brighthive-platform-core#1057](https://github.com/brighthive/brighthive-platform-core/pull/1057)<br>[🟢 Merged brighthive-webapp#1300](https://github.com/brighthive/brighthive-webapp/pull/1300) |
| [BH-1045](https://brighthiveio.atlassian.net/browse/BH-1045) | feat(monitoring): generic ETL pipeline adapter port + registry entry | Kuri Chinca | [🟢 Merged agentic-project-mgmt#98](https://github.com/brighthive/agentic-project-mgmt/pull/98) |
| [BH-1046](https://brighthiveio.atlassian.net/browse/BH-1046) | feat(monitoring): proactive alert path — detected issue → Slack/inbox… | Kuri Chinca | — |
| [BH-1047](https://brighthiveio.atlassian.net/browse/BH-1047) | feat(monitoring): auto-remediation loop for known fix patterns… | Kuri Chinca | [🟢 Merged brightbot#858](https://github.com/brighthive/brightbot/pull/858)<br>[🟢 Merged brightbot#854](https://github.com/brighthive/brightbot/pull/854)<br>[🟢 Merged brightbot#852](https://github.com/brighthive/brightbot/pull/852) |
| [BH-1054](https://brighthiveio.atlassian.net/browse/BH-1054) | feat(monitoring): watchdog poller — the actual missing proactivity… | Kuri Chinca | [🟢 Merged brightbot#842](https://github.com/brighthive/brightbot/pull/842)<br>[🟢 Merged brighthive-platform-core#1047](https://github.com/brighthive/brighthive-platform-core/pull/1047) |
| [BH-1076](https://brighthiveio.atlassian.net/browse/BH-1076) | feat(quality): chain warehouse discovery -> per-table profiling for… | Kuri Chinca | [🟢 Merged brightbot#873](https://github.com/brighthive/brightbot/pull/873)<br>[🟢 Merged brightbot#869](https://github.com/brighthive/brightbot/pull/869)<br>[🟢 Merged brightbot#868](https://github.com/brighthive/brightbot/pull/868) |

### 🔵 In Review (3)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-1036](https://brighthiveio.atlassian.net/browse/BH-1036) | Monitoring Agents — proactive pipeline discovery &amp; health (dbt,… | Kuri Chinca | [🟢 Merged agentic-project-mgmt#132](https://github.com/brighthive/agentic-project-mgmt/pull/132)<br>[🔵 Review agentic-project-mgmt#131](https://github.com/brighthive/agentic-project-mgmt/pull/131)<br>[🟢 Merged agentic-project-mgmt#130](https://github.com/brighthive/agentic-project-mgmt/pull/130) |
| [BH-1075](https://brighthiveio.atlassian.net/browse/BH-1075) | feat(warehouse): new sql_server WarehouseType/WarehouseServiceProvide… | Kuri Chinca | [🟡 Draft agentic-project-mgmt#125](https://github.com/brighthive/agentic-project-mgmt/pull/125) |
| [BH-1110](https://brighthiveio.atlassian.net/browse/BH-1110) | Persist watchdog run + remediation PR state to platform-core… | _unassigned_ | [🟡 Draft agentic-project-mgmt#125](https://github.com/brighthive/agentic-project-mgmt/pull/125)<br>[🟢 Merged brightbot#883](https://github.com/brighthive/brightbot/pull/883)<br>[🟢 Merged brightbot#866](https://github.com/brighthive/brightbot/pull/866) |

### ✅ Done (2)

| Key | Summary | Assignee | PR |
|---|---|---|---|
| [BH-1057](https://brighthiveio.atlassian.net/browse/BH-1057) | provision the Loop Capital SQL Server sandbox (Docker, local) —… | Kuri Chinca | — |
| [BH-1065](https://brighthiveio.atlassian.net/browse/BH-1065) | verify: does anything render anomaly JSON metadata into a visible… | Kuri Chinca | — |


## 🕒 Recent activity (14 days)

- **2026-07-28** · [BH-1060](https://brighthiveio.atlassian.net/browse/BH-1060) — Needs Refinement · Kuri Chinca
- **2026-07-28** · [BH-1254](https://brighthiveio.atlassian.net/browse/BH-1254) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1253](https://brighthiveio.atlassian.net/browse/BH-1253) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1252](https://brighthiveio.atlassian.net/browse/BH-1252) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1251](https://brighthiveio.atlassian.net/browse/BH-1251) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1250](https://brighthiveio.atlassian.net/browse/BH-1250) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1249](https://brighthiveio.atlassian.net/browse/BH-1249) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1248](https://brighthiveio.atlassian.net/browse/BH-1248) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1247](https://brighthiveio.atlassian.net/browse/BH-1247) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1246](https://brighthiveio.atlassian.net/browse/BH-1246) — Needs Refinement · _unassigned_
- **2026-07-28** · [BH-1245](https://brighthiveio.atlassian.net/browse/BH-1245) — Needs Refinement · _unassigned_
- **2026-07-23** · [BH-1178](https://brighthiveio.atlassian.net/browse/BH-1178) — Needs Refinement · Kuri Chinca
- **2026-07-23** · [BH-1175](https://brighthiveio.atlassian.net/browse/BH-1175) — Needs Refinement · _unassigned_
- **2026-07-23** · [BH-1172](https://brighthiveio.atlassian.net/browse/BH-1172) — Needs Refinement · _unassigned_
- **2026-07-22** · [BH-1167](https://brighthiveio.atlassian.net/browse/BH-1167) — Needs Refinement · Kuri Chinca
- **2026-07-17** · [BH-1120](https://brighthiveio.atlassian.net/browse/BH-1120) — Needs Refinement · _unassigned_
- **2026-07-17** · [BH-1119](https://brighthiveio.atlassian.net/browse/BH-1119) — Needs Refinement · _unassigned_
- **2026-07-17** · [BH-1118](https://brighthiveio.atlassian.net/browse/BH-1118) — Needs Refinement · _unassigned_
- **2026-07-17** · [BH-1117](https://brighthiveio.atlassian.net/browse/BH-1117) — Needs Refinement · _unassigned_
- **2026-07-16** · [BH-1116](https://brighthiveio.atlassian.net/browse/BH-1116) — Needs Refinement · Kuri Chinca

_(+16 older updates not shown.)_

## 📝 Daily Notes

<!-- TRACKER:MANUAL:BEGIN daily-notes -->

### T-1 — 2026-07-16 — live verification / dress rehearsal

Ran the full demo surface against real, deployed staging code + real e2e — output captured in `demo.md`. Verified working:

- **GC-14 → GC-17 proactive loop**: watchdog detects a broken nightly dbt job before anyone asks (`pipeline_watchdog_task.py`; `test_gc_14_proactive_monitor_alert.py`, 3 passed); SQL-Server-no-MCP disk/job detection (`sql_server_pipeline_source.py`, real-behavior tests); root-cause → dbt fix → **real GitHub PR** `brighthive-dbt/loopcapital-dbt-demo#1` (MERGED by a human); `github_merge_pull_request` proven never bound to the remediation agent (`test_gc_17_auto_merge_exclusion.py`).
- **Legacy Analyst Analyzer (§5)**: `.dtsx`/`.rdl` `ElementTree` parsers find the real planted gaps in Loop Capital's own sandbox artifacts (`test_ssis_ssrs_diagnostics_real_fixtures.py`, 2 passed); full chat-level diagnosis against Loop Capital's own identity passed 3×; **storage optimization** verified live against OneTen's real Snowflake (8 real `execute_sql_query_tool` calls, 21 tables / 214 columns).
- **Whole-warehouse discover→profile scan** (BH-1076): real-behavior tests green against the live SQL Server sandbox.

Real bugs found and fixed during verification: `get_lineage` needs a fully-qualified `unique_id` (prompt never said so); GitHub App authorization; dbt Cloud repo↔project linking (repo moved to `brighthive-dbt` org). Remaining blocker: Snowflake MFA on the service account (see 🚨 Blockers).

Honest "not a live moment" calls locked in for the script: §2 lineage and §6 bronze/silver/gold graph are shown as real tested code, not a live chat question; SSIS/SSRS diagnosis does **not** auto-open a PR; Loop Capital's own workspace has zero routines / zero data assets, so longitudinal drift + BrightRoutines demo on OneTen/sandbox only.

### T-0 — 2026-07-17 — demo day

Decision gate with Frank. Run sheet: `demo.md`. This-week block above has the priority order + pre-demo checklist. Record the decision (Won / Lost / Extended) + rationale below after the demo.

<!-- TRACKER:MANUAL:END daily-notes -->

## ❓ Open Questions

<!-- TRACKER:MANUAL:BEGIN open-questions -->

_Honest gaps documented in `demo.md` — do not claim these live. Resolve/date-stamp as they close._

- **(team) SSIS/SSRS diagnosis → auto-opened GitHub PR is not wired** (raised 2026-07-16). Diagnosis itself is real; the analyst agent has zero GitHub write tools bound, so there's no one-click PR flow like GC-16's dbt remediation. If Frank asks: "it can diagnose and suggest the dbt migration path today; auto-opening the PR from that suggestion isn't wired yet."
- **(team) Recurrence *prevention* vs. re-diagnosis** (raised 2026-07-16). GC-16 correctly diagnoses and fixes each occurrence today; proving the *same class* of issue is actually prevented from recurring is the open next step — tracked by `test_gc_16_recurrence_actually_prevented_not_just_redetected`.
- **(team) Snowflake account-admin access** to clear the MFA blocker on the dbt Cloud service account — gating live `get_lineage` and lineage-graph population (see 🚨 Blockers).
- **(team) BrightRoutines MCP/A2A external trigger** (BH-1038–1041): scoped, not built. If asked "can another system trigger this," the answer is "roadmap, not built yet."
- **(team) Loop Capital's own workspace is empty** — `routineSuggestionsForWorkspace`, `scheduledRoutinesForWorkspace`, and `workspace.dataAssets` all return empty for `e3fc0917-…` (expected for a fresh synthetic demo workspace, not a bug). Demo longitudinal drift + BrightRoutines on OneTen / the sandbox instead.

<!-- TRACKER:MANUAL:END open-questions -->
