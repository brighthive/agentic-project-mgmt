---
title: "Proactive Pipeline & Ingestion Monitoring — job/run-status watchdog + surgical remediation"
epic: "BH-1036"
author: "drchinca"
status: "Draft"
created: "2026-07-10"
generates: "tickets"
tags: [monitoring, observability, dbt, databricks, etl, ingestion, brightsignals, self-healing, brightbot, platform-core, watchdog]
related:
  features: []
  pocs: []
  specs: ["longitudinal-monitoring.md", "longitudinal-monitoring-capability.md", "self-healing-pipelines.md"]
---

# Proactive Pipeline & Ingestion Monitoring

> Full contract: `~/.claude/rules/spec-driven.md`. Written for handover — another engineer
> should be able to implement §2–§10 without asking a clarifying question. This spec was
> built across 34+ verification passes (2026-07-10 through 2026-07-12, ongoing); inline "Verified pass N"
> annotations in §1 are provenance for claims that overturned an earlier, wrong assumption —
> trust them over any older memory note or ticket text they cite, since each was checked
> against real code or, for passes 12-13/15, live AWS data. Full pass-by-pass log: §Related.

## Contents

- [**Start Here** (5-minute executive summary)](#start-here-executive-summary-added-pass-18)
- [Glossary](#glossary)
- [1. Context](#1-context) — problem, current state, hard limitations, gaps
- [2. Interface Contract](#2-interface-contract-mde)
- [3. Invariants](#3-invariants-dbc) — 12, DbC
- [4. Acceptance Criteria](#4-acceptance-criteria-bdd--gherkin) — 12 scenarios
- [5. Out of Scope](#5-out-of-scope)
- [6. Dependencies](#6-dependencies)
- [7. Correctness Properties](#7-correctness-properties) — 6
- [8. Eval Criteria](#8-eval-criteria)
- [9. Observability Contract](#9-observability-contract)
- [10. Test Coverage Update](#10-test-coverage-update)
- [Areas Involved](#areas-involved)
- [Ticket Breakdown](#ticket-breakdown) — 24 tickets across BH-1036/1037/115/453
- [Related](#related)

## Start Here (executive summary, added pass 18)

**If you're picking this up cold and have 5 minutes, read this section only.**

**What this is**: a spec for making dbt/Databricks/ETL job-status and ingestion-source
monitoring genuinely proactive (unprompted detection + alert + safe auto-remediation),
answering a Loop Capital sales-gate commitment for a **2026-07-17 demo**.

**Two things are time-critical and NOT architecture work — do these first, in this order:**
1. **BH-1057** (SQL Server demo fixture, ~3-5hrs, RDS Web edition, zero code changes) — the
   literal Frank-committed demo scenario ("SQL server has no MCP... disk at 20%") has NO
   staging infrastructure today. This blocks the actual 7/17 demo, not just this spec.
2. **BH-1058** (dbt failure fixture, ~1-2hrs, one-time UI setup) — needed for BH-1043's test,
   less urgent than #1.

**Everything else is architecture/implementation work, sequenced as**:
`BH-1042 (contract) → {BH-1043 dbt, BH-1044 Databricks, BH-1054 watchdog} → {BH-1045 SQL
Server, BH-1046 delivery verify, BH-1047 remediation}`, and separately `BH-1048 (ingestion
contract) → {BH-1049 Airbyte, BH-1050 Step Functions, BH-1051 queue/DLQ} → BH-1052 (unify)`.
BH-1053 (BrightSignals unification) and BH-1055 (dispatcher hardening) are real but
**non-blocking** — don't let them stall the critical path.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  ADDED pass 25 (triple-click-zoom) — the full dependency graph, PUSH vs PULL   │
│  options called out where this loop found a cheaper push-based alternative     │
└────────────────────────────────────────────────────────────────────────────────┘

  BH-1042 (contract: PipelineSource Protocol, PIPELINE_SOURCE_ADAPTERS registry,
           PipelineHealthSignal DTO, get_pipeline_health MCP tool, §8 eval design)
      │
      ├──▶ BH-1043 (dbt watchdog — wraps EXISTING dbt_cloud_tools.py, adds backoff)
      ├──▶ BH-1044 (Databricks watchdog — GREENFIELD connector + credentials, mirrors
      │             dbt's per-CONNECTION direct-boto3 secretsmanager pattern exactly)
      └──▶ BH-1054 (watchdog capability node — rides EXISTING scheduled_agent_dispatcher,
                     owns the dual-write: per-member fanout + resolveSignal() derivation,
                     NOT a same-payload-twice call; cooldown keyed on (workspace_id,
                     source_type, job_id, failure_type) — 4-tuple, not 3)
             │
             ├──▶ BH-1045 (SQL Server disk/job query — existing WarehousePort/Synapse
             │             connection chain PLUS a NEW VIEW SERVER STATE grant, a real
             │             customer-side permission action, not "zero new anything")
             ├──▶ BH-1046 (delivery verify — dbt_run_failure ONLY, narrow scope,
             │             does NOT duplicate BH-1067's 5-stage renderer work)
             └──▶ BH-1047 (remediation — builds GC-11's loop for the FIRST time, since
                           self-healing-pipelines.md is itself unbuilt; REMEDIATION_TOOLS
                           via direct import, github_merge_pull_request omitted by
                           construction, mirrors retrieval_agent_react.py's real pattern)

  BH-1048 (ingestion contract, separate from the job-status contract above)
      │
      ├──▶ BH-1049 (Airbyte — PUSH option confirmed cheaper: extend platform-core's
      │             airbyte_notification_webhook's existing no-op failure branch,
      │             reuses its real auth client + connection mapping, vs. building a
      │             new brightbot poller from zero)
      ├──▶ BH-1050 (Step Functions — PUSH option confirmed cheaper: extend the LIVE
      │             data_ingestion_stack.py EventBridge rule already routing FAILED
      │             executions to Slack via SNS, vs. a new execution-history poller)
      └──▶ BH-1051 (queue/DLQ — THREE options, evaluate cheapest first: (a) extend
                    cadenceToCron [touches shared scheduling infra], (b) new scoped
                    EventBridge rule [also shared], (c) native CloudWatch Alarm on the
                    queue's own metrics [ZERO new BrightHive scheduling code — try
                    this first])
             │
             └──▶ BH-1052 (CORRECTED pass 25 — not pure verification: BH-1049/1050's
                           push options live in DIFFERENT repos/mechanisms than BH-1054's
                           direct dual-write — BH-1050's existing SNS→Slack path in
                           particular may need a NEW addition to also reach NotificationInbox,
                           since SNS→Slack alone doesn't touch the webapp today)

  Cross-cutting, non-blocking: BH-1053 (dual-write unification), BH-1055 (dispatcher
  hardening), BH-1059 (AgentCore migration tracking), BH-1060 (PII redaction decision)
```

**One open human decision, not resolved by this spec**: BH-1044 (Databricks) recommends
brightbot-only secret storage over a platform-core schema change, for the demo timeline —
needs Kuri's explicit confirm/override (see Jira comment on BH-1044).

**One CRITICAL safety requirement, non-negotiable, added pass 24**: BH-1047 (remediation
wiring) MUST ensure the remediation loop's tool surface excludes `github_merge_pull_request`
at the code level. "Never auto-merge" is currently a system-PROMPT instruction only, on the
same shared dbt-agent toolset this spec's remediation loop reuses — with zero code-level lock
and zero branch-protection backstop. Do not consider BH-1047 done without the unit test that
enumerates bound tools and asserts merge capability is absent (see §7 Property 2, §4 Gherkin
scenario "remediation loop's tool surface excludes merge capability").

**A SECOND critical safety fix, non-negotiable, added pass 26**: the spec's original
`get_pipeline_health` MCP tool signature had `workspace_id` as a caller-supplied parameter —
a P0 cross-tenant spoofing bug, now fixed to source workspace scoping from principal only,
exactly like `get_anomalies`. Do not consider BH-1042 done without the isolation test (see §7
Property 8, §4 Gherkin scenario "get_pipeline_health cannot be spoofed to read another
workspace's signals") AND the existing repo-wide `test_no_principal_fields_in_tool_args` test
passing for this new tool.

**Everything below this point is the full, exhaustively-verified spec** (§1-10 + 26 rounds of
architecture/infrastructure/security verification, each citing real code or live AWS data —
see §Related for the full pass-by-pass log). Read it when implementing, not before deciding
what to do first.

## Glossary

- **BYOW** — Bring Your Own Warehouse; a customer-hosted data warehouse (Snowflake, SQL
  Server, etc.) connected to BrightHive via a warehouse connection, rather than data
  ingested into BrightHive's own storage.
- **MCP** — Model Context Protocol; the tool-calling interface BrightHive agents/external
  callers use to invoke platform capabilities.
- **A2A** — Agent-to-Agent; external agent/service calls into BrightHive via MCP, as opposed
  to a human using the webapp/Slack.
- **OTel** — OpenTelemetry; the tracing/metrics standard used for the Observability Contract.
- **DMV** — Dynamic Management View; a SQL Server system view (e.g.
  `sys.dm_os_volume_stats`) exposing runtime health/state without needing an agent installed
  on the server.
- **GC-11 / GC-12** — Golden Case 11 / 12; numbered acceptance scenarios from the Longaeva
  POC scorecard, each backing one spec (`self-healing-pipelines.md`, `longitudinal-monitoring.md`).
- **`run_context`** — the existing dispatch metadata (ingestion / scheduled / on-demand) that
  tells an agent capability node why it's running; see `longitudinal-monitoring-capability.md`.
- **Capability node** — a detection/action unit registered inside an existing agent (e.g.
  `quality_check_agent`, `dbt_agent`) and invoked through the platform's existing dispatcher —
  not a new standalone service.
- **Surgical PR** — a pull request whose diff is scoped to exactly the failure being fixed (no
  incidental rewrites), always subject to human approval; defined in `self-healing-pipelines.md`.
- **Watchdog** — this spec's term for a capability node that polls for job/run-STATUS failures
  on a schedule, as opposed to GC-12's data-quality metric snapshots.
- **Nightshift** — the informal name for scheduled, unattended agent runs (see
  `longitudinal-monitoring.md` §"Use Case / Goal").

## 1. Context

Sales-gate feedback (Loop Capital, Frank, 2026-07-09 demo; follow-up 2026-07-17) named a
specific gap: BrightHive demonstrated *reactive* agents (respond when asked) but not
*proactive* ones ("check, find the issue, alert me, and fix it," unprompted). Frank
specifically challenged the MCP-to-SQL-server connectivity claim: "if the SQL server does
not have any MCP or any other service to connect, how are you going to actually monitor
the SQL jobs?" — citing disk-space monitoring at a 20%-remaining threshold as his concrete
example.

This spec was preceded by two rounds of architecture audit (2026-07-10, both in
`~/.claude/projects/-Users-bado-iccha-brighthive/memory/`:
`project_brightsignals_vs_brightroutines_audit.md`,
`project_existing_monitoring_specs_discovery.md`) that overturned the original plan (a new
Jira epic BH-1036 proposing a from-scratch `PipelineMonitorPort` + alert pipeline). Two
existing systems already cover most of the intended scope:

- **BrightSignals** (BH-409) — the event/notification substrate. **Confirmed (2026-07-10,
  by direct code read, not inference) to be a THREE-way split-brain, sharper than pass 1's
  two-path finding** (see `project_brightsignals_three_way_split_brain.md`):
  1. Old `NOTIFICATIONS_TABLE` (workspace_id/event_id) — written by
     `writeNotificationSignal()`/`publishNotification`; **the ONLY table the live Slack/SSE
     poller reads** (`brightbot-slack-server/src/notifications/poller.ts`).
  2. New per-user `NotificationInbox` (USER#uid/WS#wsid#eventId) — written by the
     post-2026-07-08 "agnostic and truthful" `notificationRecipients` resolver (platform-core
     commit 895c90d4, #1012). Feeds the **webapp inbox only** — the Slack poller never reads
     this table.
  3. EventBridge `bh.org.ingestion` → `notification_dispatcher` Lambda (written by
     `put_ingestion_status_update()`) — the Lambda is confirmed never wired into any deployed
     CDK stack. Dead end-to-end.
  **No single write today reaches both Slack and webapp.** A caller must write to (1) AND
  separately go through (2) — there is no shared entrypoint. `dbt_run_failure` is already a
  registered (unused) category in path 1's taxonomy (`notifications.ts:251`) — the slot
  exists, nothing populates it, and even populated it would only reach Slack, not webapp.
  **Verified pass 20 — "multi-channel" for this spec means exactly these 2 channels, not 3.**
  BH-409's own epic description lists "Email (SES — already configured)" as a channel, but
  this is aspirational, matching the EventBridge dispatcher's dead-code pattern exactly:
  `notification_dispatcher/delivery.py` has a real `deliver_email()` (boto3 SES) registered in
  a `_CHANNEL_ADAPTERS` dict, but the Lambda is never instantiated in any CDK stack — zero
  hits for it outside its own folder. `brightbot-slack-server` has zero SES references. No
  BrightSignals-shaped event has ever triggered a real email. Slack + webapp is the FULL live
  channel set today — this spec's dual-write is not an incomplete 2-of-3, it covers everything
  real. Email delivery, if ever built, is BH-412's scope (BrightSignals MVP, still unbuilt),
  not a gap in this spec.
- **Longitudinal Monitoring** (GC-12, BH-601, **SHIPPED + staging-verified 2026-06-18**) —
  stateful *data-quality* anomaly detection (row_count_drift, cardinality_breakdown,
  distributional_skew, null_spike), running as a **capability node inside
  `quality_check_agent`**, triggered by the **existing scheduled dispatcher + `run_context`**
  (explicitly "no new EventBridge," per BH-670), wired to BrightSignals, MCP-readable via
  `get_anomalies`. **Verified 2026-07-10 (pass 3) by direct code read**: BH-670 is fully
  wired — `run_context=SCHEDULED` flows end-to-end
  (`scheduled_agent_dispatcher/actions/langgraph_action.py:44-76` →
  `quality_check_task.py:42,113` → `quality_check_agent.py:1546-1598,1752` →
  `longitudinal_node.py:187-243`), landed via BH-768 (PR #724, merged 2026-06-25). This is a
  fully closed precedent, not a caveated one — the ticket table's "⏳ cadence wiring remains"
  note is stale (predates BH-768 by 7 days).
- **Self-Healing Pipelines** (GC-11, BH-526, Draft, unbuilt) — a detect→diagnose→**surgical
  PR** loop for 4 failure modes (schema_drift, missing_partition, broken_stage,
  dbt_contract), proven in a sandbox, reusing the dbt agent's existing scoped-PR path, with a
  hard human-approval gate (never auto-merges).

**What this spec actually adds** (the genuine gap, confirmed absent by grep — zero hits for
`watchdog`/`health_check`/`proactive_monitor` anywhere in `brightbot`/`platform-core`):

1. A **job/run-status watchdog** — distinct from GC-12's *data-quality* metrics — that
   proactively polls dbt Cloud job/run state, Databricks job/cluster state, and generic ETL
   job state (including on-prem SQL Server Agent jobs with no exposed MCP/service), on the
   *same scheduling pattern GC-12 already proved* (capability node + existing dispatcher, no
   new infra).
2. An explicit **dual-write** into both live BrightSignals surfaces (old table for Slack, new
   `NotificationInbox` for webapp) so this new signal source doesn't repeat the exact
   single-surface bug the split-brain already causes — with a documented migration path to
   BH-1053's eventual unified entrypoint, once it ships.
3. **Wiring the watchdog's output into self-healing-pipelines.md's surgical-PR loop**, rather
   than inventing a separate "auto-remediation" mechanism.
4. A concrete, demoable answer to the SQL-Server-with-no-MCP objection: query the source
   through its **existing warehouse connection** (the one already required to catalog/query
   it as a BYOW source), not a new agent/collector.

### Use Case / Goal

A workspace connects a dbt project, a Databricks workspace, and/or a BYOW SQL Server. With
zero further user action: job failures, stale runs, and (for SQL Server) low-disk conditions
are detected on a schedule, an alert reaches the user via Slack/in-app before they ask, and —
for the 4 known-safe failure modes — a surgical PR is opened automatically for human review.
Success = Frank's 7/17 demo shows all three: (a) unprompted detection+alert, (b) SQL-Server
disk monitoring with no MCP on the SQL Server, (c) a fix surfaced without a human writing it
from scratch.

### How It Works Today

- dbt job/run status: on-demand only, via `brightbot/brightbot/agents/dbt_agent/tools/dbt_cloud_tools.py`
  (`list_jobs`, `_fetch_run_status`, `_fetch_run_details_with_logs`). Nothing polls this in
  the background.
- Data-quality anomalies: **proactive, shipped** — see GC-12 above.
- Ingestion sync/webhook events: reactive-push only — `put_ingestion_status_update()`
  (`new_openmetadata_webhook_lambda/utils/ingestion_status_event.py`) writes on webhook
  callback (e.g. Airbyte sync completion), not on a poll — a silently-hung sync with no
  callback never fires.
- Notification delivery: THREE independent paths (old `NOTIFICATIONS_TABLE` → Slack poller;
  new `NotificationInbox` → webapp; EventBridge → dead dispatcher Lambda). No single write
  reaches both live surfaces (Slack + webapp) — see §1 Gaps.
- SQL Server / generic ETL: **zero code**. No adapter, no connectivity path documented.

### Hard Limitations

- BrightSignals is a confirmed THREE-way split-brain (old signal table / new per-user inbox /
  dead EventBridge dispatcher) — this spec's watchdog must not become a FOURTH independent
  producer. Rather than blocking on BH-1053 (which may take longer than the 7/17 demo
  allows), this spec resolves the immediate risk itself: the watchdog performs an explicit
  dual-write to both live surfaces (Invariant 1/6) and migrates to BH-1053's unified
  entrypoint once that ships — see §4 Scenario "BH-1053 unification supersedes the
  dual-write."
- Longitudinal monitoring's dispatcher pattern is proven for *data-quality* signals computed
  from a warehouse query; job/run-STATUS signals come from a different API shape (dbt Cloud
  REST, Databricks Jobs API, `msdb.dbo.sysjobs`) and need their own polling client per source,
  even though the *scheduling* mechanism is shared.
- **Verified 2026-07-10 (pass 3), genuine structural mismatch — not just an uncovered case**:
  self-healing-pipelines.md's `FailureMode` protocol (`inject/detect/heal`, all SQL-`conn`-based)
  fits its 4 modes because each is a *data-shape* defect: SQL-diagnosable, DDL/DML-fixable,
  and `heal()`'s contract ("apply the fix, re-run detect(), see it clear") holds. A job-status
  failure (dbt job timeout, Databricks cluster unhealthy, SQL Server Agent job erroring) has
  NO such shape — no conn-queryable signature, and "retry the job" or "escalate to a human" is
  not a scoped DDL statement. **This spec does NOT extend GC-11's taxonomy with fabricated new
  modes.** Instead: a job-status failure's remediation is one of two paths — (a) if its root
  cause resolves to one of GC-11's 4 existing data-shape modes (e.g. the dbt job failed BECAUSE
  of an upstream schema-drift condition), it routes into the EXISTING surgical-PR loop
  unchanged; (b) if it has no data-shape root cause, the only valid remediation action is
  retry / escalate-with-diagnosis / alert-only — never a surgical PR. See §3 Invariant 9.
- **Verified 2026-07-10 (pass 4)**: `dbt_cloud_tools.py` (the on-demand tool this spec's dbt
  watchdog reuses as its poll target) has ZERO rate-limit/backoff/retry handling — confirmed
  by grep, zero hits for 429/backoff/tenacity/rate-limit anywhere in the file. This was
  tolerable for on-demand, human-triggered calls (a failure surfaces as an error the human
  retries); it is NOT tolerable for an unattended background watchdog polling every connected
  workspace on a fixed cadence, which must add its own backoff (Invariant 10). Credentials are
  confirmed per-CONNECTION, not strictly per-workspace (Secrets Manager entry
  `dbt/cloud-api/{service_id}`, `credentials_tools.py:166-201`) — **SHARPENED pass 24
  (triple-click-zoom)**: `service_id` is `TransformationServiceNode.id`
  (`typedefs.ts:873-874`), and a single workspace CAN have multiple `TransformationService`
  nodes (`WorkspaceNode.transformationServices: [TransformationServiceNode!]!`,
  `typedefs.ts:289/463` — a plural relationship). `_find_connected_dbt_service()`
  (`credentials_tools.py:154-163`) explicitly picks the FIRST `provider == "DBT_CLOUD"`
  service, which is fine for today's single-dbt-connection-per-workspace common case but is
  NOT a structural guarantee — the watchdog's per-workspace throttling/cooldown reasoning
  (same class of concern as Invariant 3's cooldown-key fix, pass 17) should key on
  `(workspace_id, service_id)` if a workspace with 2+ dbt connections is ever a real case,
  not assume `workspace_id` alone identifies one credential set. This is a self-throttling
  concern, not a cross-tenant one, but the granularity assumption should be explicit, not
  implicit.

  **ALSO SHARPENED pass 24**: the credential-read path itself is NOT purely
  platform-core-mediated as later prose (BH-1044) implies — brightbot's OWN
  `_retrieve_dbt_cloud_api_token()` (`credentials_tools.py:166-200`) calls
  `boto3.client("secretsmanager").get_secret_value(SecretId=f"dbt/cloud-api/{service_id}")`
  DIRECTLY (lines 180-182), duplicating (not going through) platform-core's own write/read
  path (`dbt-cloud-api-secret.ts:16-83`, which platform-core uses for its own GraphQL-resolved
  credential flow). BH-1044's "mirror this pattern for Databricks" is therefore directionally
  correct in citing direct-boto3 access as the real precedent — but should mirror
  brightbot's OWN direct-read function specifically, not assume access is mediated entirely
  through platform-core. Confirmed: NO in-memory/TTL cache wraps this credential read
  (grep, zero hits) — every call hits Secrets Manager fresh, so there is no
  credential-caching cross-workspace leakage risk to inherit either, unlike the earlier
  cooldown-key finding.

  Separately, `_analyze_run_errors` (`dbt_cloud_tools.py:485-494`) fans out
  concurrently via an uncapped `asyncio.gather` — the watchdog must bound this per Invariant 11,
  not inherit it unbounded across every workspace polling concurrently.
- **Verified 2026-07-10 (pass 4)**: Databricks has ZERO existing application code in brightbot
  (confirmed by grep — zero hits outside third-party library internals). BH-1044 is greenfield
  work, not an integration on top of an existing tool the way BH-1043 is.
- **Verified 2026-07-10 (pass 5)**: sub-hourly watchdog cadences are NOT supported at the
  product layer. EventBridge Scheduler itself can express minute-level cron, but
  `cadenceToCron()` (`brighthive-platform-core/src/graphql/service/workflow/routine-scheduler-client.ts:165-180`)
  only knows `DAILY|WEEKLY|BIWEEKLY|MONTHLY|QUARTERLY` (all hardcoded to 08:00), and
  `_to_scheduler_cron` (`brightbot/routes/scheduled_agents_routes.py:271-294`) validates field
  count only, no minimum-interval check. This is fine for dbt/Databricks job-status polling
  (hourly-ish is adequate) but NOT fine for ingestion queue-depth/DLQ monitoring (BH-1051),
  which needs sub-hourly — arguably sub-5-minute — polling to be proactive rather than
  theatrical. See §1 Gaps item 6 and Out of Scope for how this spec handles it.
- **Verified 2026-07-10 (pass 5)**: BH-1050's original framing ("reuse BH-844 Step Functions
  groundwork") was WRONG — zero hits for `describe_execution`/`list_executions` (the
  POLLING calls) anywhere in application code. BH-844 itself could not be confirmed to exist
  in any repo's code/docs/commit history (searched all 4 relevant repos — zero hits on
  "844"). BH-1050 is greenfield for a PULL/polling approach.
  **CORRECTED pass 22 (triple-click-zoom) — this framing missed a real, already-shipped
  PUSH-based precedent that changes BH-1050's real options, the same class of correction
  found for BH-1049's Airbyte webhook (pass 13).** Confirmed:
  `brighthive-data-organization-cdk/brighthive_data_cdk/data_ingestion_stack.py:844-853` —
  a REAL, LIVE `events.Rule` matching `source: ["aws.states"], detail_type: ["Step
  Functions Execution Status Change"], detail: {"status": ["FAILED"], "stateMachineArn":
  [...]}`, targeting an SNS topic that already delivers to Slack (lines 838-841,887-889;
  shipped in commit `3c5a269`, "Add: slack notification setup for the dataingestion
  statemachine (#113)"). This is EXACTLY the native, zero-polling EventBridge pattern AWS
  provides for Step Functions monitoring — it already exists for the data-ingestion state
  machine specifically. **BH-1050's real options are therefore, like BH-1049's Airbyte
  case: (a) extend this EXISTING rule's target/pattern to also reach BrightSignals'
  dual-write (cheaper — reuses shipped infra, may need to widen the `stateMachineArn` filter
  or add BrightSignals as a second SNS subscriber), or (b) build a genuinely new poller
  (the original greenfield framing, now confirmed as option (b) only, not the only path).**
  Confirmed real state machines this rule could plausibly extend to:
  `data_ingestion_stack.py:821-825` (data-ingestion, Glue→warehouse-sync→OpenMetadata),
  `sfn_dynamic_execution.py:230-234` (dynamic ingestion executor, cron trigger currently
  disabled), `unstructured_data_ingestion_sfn.py:342-347` (S3-triggered KB sync),
  `brighthive_core/dbt_validation_stack.py:165-170` (a DIFFERENT existing state machine,
  "dbt-job-status-state-machine") — **CHECKED pass 22, CONFIRMED NOT AN OVERLAP with
  BH-1043, but a real, separate gap worth flagging.** This state machine is a synchronous
  provisioning-gate, not a monitoring watchdog: it's invoked once per GraphQL mutation
  right after the platform triggers a dbt Cloud job itself (`project.ts:~2995-3038` →
  `startStateMachineExecution`), polls via `dbt_job_status_lambda`
  (`lambdas/dbt_validation/main.py`) in a 20s Wait/Choice loop until the run finishes, then
  on SUCCESS writes the resolved schema ID onto `ProjectNode` in Neo4j. It has no periodic
  cadence, no dashboard, no alerting consumer — it exists only to know when it's safe to
  read the dbt run's own output. **CONFIRMED it fails COMPLETELY SILENTLY on dbt run
  failure**: the Lambda returns `{"retry": False, "status": "Failed"}`, the state machine
  reaches its `otherwise` branch and ends "successfully" from Step Functions' own
  perspective, the only trace is a bare `print("[ERROR] Failed:", e)` (CloudWatch-only), and
  the GraphQL caller (`project.ts`) doesn't even inspect the execution result
  (`startStateMachineExecution` returns `true` unconditionally, fire-and-forget). This is a
  REAL, PRE-EXISTING gap independent of this whole spec — a dbt provisioning failure during
  project setup notifies no human today. NOT this spec's problem to fix (out of scope for
  BH-1036/1037), but flagged here since a cold engineer investigating "why didn't
  provisioning finish" would otherwise waste time not knowing this silent-failure path
  exists — file separately if Loop Capital or another customer hits it.
- **Verified 2026-07-10 (pass 5)**: BH-1049's original framing ("Airbyte/source-sync health
  signals") assumed a pollable Airbyte status API exists in brightbot — it doesn't. Sync
  execution routes through Platform Core GraphQL
  (`ingestion_tools.py:375-391` → `syncConnections` mutation); the only direct Airbyte HTTP
  client found (`airbyte_registry.py`) fetches the public connector *registry* (metadata about
  connector types), unrelated to sync status, unauthenticated, no rate-limit handling. BH-1049
  is greenfield: it needs either a new GraphQL query surfacing sync status (if platform-core
  tracks it server-side) or a new direct client, not a "polling wrapper around an existing tool."
  **CORRECTED pass 13 (triple-click-zoom) — "CONFIRMED greenfield" was accurate for
  brightbot specifically, but misleading at the ORG level, and a materially cheaper path
  exists one repo over.** `brighthive-platform-core/airbyte_notification_webhook/runtime/
  app.py` already has: (a) a working, authenticated Airbyte REST client
  (`generate_airbyte_token`, `:47-59`, hits `{airbyte_url}/api/v1/applications/token`; an
  authenticated `POST {api_url}/api/v1/connections/get`, `:141-159`); (b) the exact
  workspace→connection mapping BH-1049 would otherwise need to invent — Neo4j Source nodes
  already store `airbyteSourceId`/`airbyteConnectionIds[]` (`ogm-types.ts:11659-11660`),
  resolved via `ogm_client.get_source_by_source_id_and_workspace_id(...)`
  (`app.py:97-101`), alongside the ingestion-service node's own `api_url`/
  `airbyte_client_id`/`airbyte_client_secret`; (c) a REACTIVE webhook that already fires on
  every sync completion/failure — but its failure branch (`app.py:88-90`) is CURRENTLY A
  NO-OP: `app.log.error(...); return {}`, no DB write, no notification, nothing proactive.
  **This changes BH-1049's real options**: instead of building a brand-new PULL-based
  poller from zero (auth, connection discovery, rate limits, all new), BH-1049 could extend
  this EXISTING PUSH-based webhook's failure branch to perform the dual-write this spec's
  watchdog pattern requires — cheaper than a new poller, and arguably MORE proactive (a
  webhook fires immediately on failure; a poller only catches it on its next cycle). The
  ticket must explicitly evaluate BOTH options (extend the reactive webhook vs. build a new
  poller) rather than defaulting to "greenfield poller" — see BH-1049's ticket for the
  updated scope.
  **RESOLVED pass 25 (triple-click-zoom) — the ONE open question Option A left ("can this
  Python Lambda even reach the TypeScript dual-write functions?") is now confirmed YES, via
  an already-proven mechanism, not a new one.** `airbyte_notification_webhook` is pure
  Python/Chalice (`app.py:1-6`, `requirements.txt` — boto3/requests, no Node runtime) —
  `writeNotificationSignal`/`NotificationInbox.deliver` are TypeScript functions running in
  a SEPARATE Node.js Apollo Lambda process (`src/server.ts`); direct cross-language calls
  are impossible, only HTTP can bridge them. CONFIRMED this Lambda ALREADY proves the exact
  mechanism needed: it makes authenticated GraphQL-over-HTTP calls into platform-core today
  (`Neo4jOGMClient`, `chalicelib/neo4j_client.py:47-55`, POSTing `{query, operationName,
  variables}` with Cognito-JWT auth via `OGMAuthClient`) — just against the OGM subgraph,
  not the Core API schema. The dual-write targets are reachable over that SAME HTTP
  mechanism, on the Core API schema instead, using `x-service-key` auth (not Cognito JWT):
  `publishNotification` (`schema/typedefs.ts:5007`, resolver
  `resolvers.ts:471`→`notifications.ts:554-564`, calls `writeNotificationSignal` directly
  at line 563) and `notificationRecipients` (`schema/typedefs.ts:5004`, resolver
  `resolvers.ts:470`→`notifications.ts:436-552`, calls `NotificationInbox.deliver` at line
  530) are BOTH real, existing GraphQL mutations reachable this way. BH-1049's Option A is
  therefore FULLY BUILDABLE with zero new IPC/protocol invention — swap the OGM endpoint for
  the Core API endpoint, swap Cognito-JWT auth for `x-service-key`, call
  `publishNotification`/`notificationRecipients` instead of the Neo4j OGM mutations this
  Lambda already calls.
- **Verified 2026-07-10 (pass 5)**: BH-815 ("Ingestion flows / platform sources disagree on
  staging") could NOT be confirmed fixed — zero git history hits referencing it in either
  repo. Must be treated as still open; do not assume resolved.

### Gaps

1. No background poller for dbt/Databricks/ETL job-run status (the watchdog itself).
2. BrightSignals' 3-way split-brain unresolved (BH-1053) — this spec's watchdog works around
   it via an explicit dual-write (Invariant 1/6) rather than waiting on the unification.
3. No SQL-Server-with-no-MCP connectivity story — needed for the 7/17 demo specifically.
4. No failure-mode taxonomy extension in self-healing-pipelines.md for job/run-status failures
   (only data shape failures today).
5. No ingestion-sync *poll* (only reactive webhook) — a source that stops calling back silently
   never alerts. Compounded by Gap 6: even once built, this poll cannot run sub-hourly without
   a scheduling change.
6. No sub-hourly scheduling capability — `cadenceToCron`/`_to_scheduler_cron` cap out at daily
   granularity in practice. Blocks BH-1051 (queue-depth/DLQ) specifically; does not block
   BH-1043/1044/1049/1050 (hourly-class cadence is adequate for job-status/sync-status checks).
7. **Verified 2026-07-10 (pass 11) — `scheduled_agent_dispatcher` has ZERO concurrency cap
   and ZERO fan-out testing.** `ScheduledAgentDispatcherStack` (BH-952, commit 6a9b7b80) sets
   no `reserved_concurrent_executions`, no DLQ, no `max_event_age`. The only existing
   concurrency test (`test_scheduled_agents_overlap_lock.py`) verifies per-SCHEDULE reentrancy
   (the same schedule can't double-fire) — NOT multi-workspace fan-out. GC-12 has run on this
   dispatcher safely so far at presumably-low concurrent volume; this spec's watchdog
   (BH-1054) PLUS the 3 ingestion watchdogs (BH-1049/1050/1051) all add MORE concurrent
   consumers of the same unthrottled dispatcher, likely at hourly (not nightshift) cadence —
   meaningfully raising the risk of many workspaces' schedules landing on the same EventBridge
   tick with no documented behavior. This violates pluggable-scalable.md's PS-8 (per-workspace
   fairness) and PS-18 (scaling observability / "alarm on unable to scale") — the dispatcher
   satisfies neither today. NOT blocking for a single-workspace 7/17 demo, but IS a real
   pre-existing risk this spec's tickets compound and should surface, not silently inherit.
   **CORRECTED pass 26 (triple-click-zoom) — this load projection is now STALE relative to
   BH-1049/1050/1051's confirmed designs; the actual dispatcher-load increase is smaller than
   "4 new watchdogs" implies.** Only BH-1054 (and its dependents BH-1043/1044/1045) are
   CONFIRMED new dispatcher consumers — BH-1054 rides the SAME existing scheduled dispatcher
   path GC-12 already uses. BH-1049 (Airbyte) and BH-1050 (Step Functions) both confirmed a
   cheaper PUSH-based Option A that adds ZERO new dispatcher load if chosen — extending an
   existing webhook Lambda (BH-1049) or an existing EventBridge→SNS rule (BH-1050) neither
   one touches `scheduled_agent_dispatcher` at all. BH-1051 (queue/DLQ) confirmed a CloudWatch
   Alarm option that also adds ZERO dispatcher load. **Revised real load addition, if Option A
   is chosen for BH-1049/1050 and the Alarm option for BH-1051: ONLY BH-1054 (+ its 3
   sibling adapters BH-1043/1044/1045, which are all POLLED FROM WITHIN the same BH-1054
   capability node, not separate dispatcher schedules) adds new dispatcher consumers — a
   materially smaller compounding effect than the original "4 new watchdogs" framing
   assumed.** This does NOT remove the need for BH-1055's hardening (BH-1054 alone is still a
   new, currently-uncapped consumer riding an already-unthrottled, unmonitored dispatcher),
   but it does mean BH-1055's own load-test sizing (currently "50-100 workspaces") should be
   revisited against this smaller confirmed consumer count if BH-1049/1050/1051 land on their
   push/alarm options — check BH-1049/1050/1051's actual chosen implementation before
   finalizing BH-1055's load-test parameters, don't plan against the original 4-watchdog
   worst case if it's no longer the real shape.
   **Sharpened pass 12 with a LIVE AWS pull (not code-only inference)**: staging's
   account-level unreserved concurrency pool is 1,000; 62 total Lambdas exist; ZERO have
   `ReservedConcurrentExecutions` set, including the dispatcher itself. The risk is
   BIDIRECTIONAL — the dispatcher can flood the shared pool under many-workspace fan-out, AND
   conversely a burst on any OTHER unrelated Lambda in the account can starve the dispatcher
   with zero isolation either way. **CONFIRMED pass 13 (live `describe-alarms` pull, 28 total
   alarms)**: zero alarms exist for this Lambda or account-level concurrency anywhere — this
   is a fully confirmed gap, not an inference. A copyable alarm-pattern template exists
   elsewhere in the account (`StagingEnhancedOmWebhook`'s custom-namespace alarm) that BH-1055
   should clone rather than design from scratch. Tracked as BH-1055 (parented BH-1036 for now;
   conceptually fits BH-171 AWS DevOps & Infrastructure better — Jira tooling limitation
   prevented a clean epic move this pass, noted on the ticket).

## 2. Interface Contract (MDE)

**Ownership split, fixed pass 34 (cold-read gap — two engineers could have collided without
this)**: **BH-1042 owns** the `PipelineHealthSignal`/`PipelineSource`/`RootCauseClass`/
`Capability`/`RequestContext` type definitions, the `PIPELINE_SOURCE_ADAPTERS` registry +
`build_pipeline_source()` factory, and the `get_pipeline_health` MCP tool + its Invariant-14
isolation test — everything below EXCEPT the node registration steps. **BH-1054 owns** the
`pipeline_watchdog_node.py` file itself and the 4 registration steps (adding it to
`quality_check_agent.py`'s graph) — it imports and calls into BH-1042's types/registry, it
does not redefine them. If BH-1042 hasn't landed yet, BH-1054 blocks on it for the type
imports; they are not parallelizable from a cold start without one waiting on the other's
types existing.

```
# Watchdog capability node — mirrors quality_check_agent's GC-12 SCHEDULING shape only
# (run_context=SCHEDULED flowing through the existing dispatcher, verified passes 3/19 —
# that finding stands). **Corrected pass 30**: GC-12 has ZERO actual OTel observability to
# mirror — `docs/specs/golden-cases/SPEC-GOLDEN-CASES.md:479-508` documents it as "No code,
# no ticket (GAP-8)"; quality_check_agent.py only has plain logger.info() calls, no spans, no
# dotted log events. §9 below follows this repo's SPEC-LEVEL house style for OTel GenAI
# semantic conventions (consistent across other specs' §9 sections), not prior art from GC-12
# — this watchdog is the FIRST real instrumentation of this capability-node class, not a copy.
async def check_pipeline_health(
    *, workspace_id: str, run_context: str, source: PipelineSource,
) -> list[PipelineHealthSignal]: ...
# TYPE NOTE (fixed pass 34, cold-read gap — `RunContext` was used but never defined anywhere
# in this doc): verified against real code, `run_context` is a plain `str` in production
# (`quality_check_task.py:42,63,113`, values "SCHEDULED"/"INGESTION"/"ON_DEMAND" — no enum
# class exists). Use `str` here to match; do not introduce a `RunContext` type that doesn't
# exist in the codebase this watchdog lives in.

# Registration (verified pass 7 — this was previously asserted as "rides the existing
# dispatcher" with no concrete wiring; here is the concrete wiring, mirroring GC-12's own
# registration exactly):
#
# HOST AGENT: governance_agent, NOT dbt_agent. dbt_agent's dbt_cloud_tools.py is the ON-DEMAND
# TOOL SURFACE this watchdog polls (a dependency), not where the watchdog itself lives.
# governance_agent is where longitudinal_node.py (GC-12's own capability node) already lives —
# this watchdog is architecturally the same kind of thing (a scheduled health-check capability
# node), so it belongs alongside its sibling, not inside the tool surface it calls.
#
# Concrete registration steps, mirroring longitudinal_node.py's real wiring
# (quality_check_agent.py:1546-1598,1752 → longitudinal_node.py:187-243):
#   1. New file brightbot/brightbot/agents/governance_agent/sub_agents/pipeline_watchdog_node.py
#      — make_pipeline_watchdog_node() returning the node function, mirroring
#      make_longitudinal_node()'s shape (reads run_context from state, branches on it).
#   2. brightbot/brightbot/agents/governance_agent/sub_agents/quality_check_agent.py — add
#      graph.add_node("run_pipeline_watchdog", make_pipeline_watchdog_node()), alongside the
#      existing graph.add_node("run_longitudinal_monitoring", make_longitudinal_node()) at
#      line 1752 — same graph, sibling node, same run_context branching convention.
#   3. CORRECTED pass 9 (triple-click-zoom) — verified against real code, the earlier wording
#      overstated where the run_context branching lives. `add_edge("record_capability_
#      execution", "run_longitudinal_monitoring")` (quality_check_agent.py:1800-1801) is a
#      PLAIN, UNCONDITIONAL edge — there is no conditional-edge routing keyed on run_context
#      anywhere in this graph. The SCHEDULED-vs-INGESTION branch happens INSIDE
#      longitudinal_node.py's own function body (lines 216, 349-358), not at the graph-edge
#      level. Step 3 is therefore: `graph.add_edge("record_capability_execution",
#      "run_pipeline_watchdog")` — one more plain edge, same shape — and
#      `make_pipeline_watchdog_node()`'s OWN function body must contain the run_context
#      early-return/branch (mirroring longitudinal_node.py:349-352's "no config → skip"
#      pattern), not a graph-level conditional. Do NOT add a new dispatcher entrypoint; this
#      reuses the exact same scheduled path GC-12 already proved end-to-end (BH-670/BH-768).
#   4. Per-source polling clients (PipelineSource implementations for dbt/Databricks/ETL) are
#      called FROM this node, not registered as separate graph nodes — the node is the single
#      scheduled entrypoint; adapter dispatch happens inside it via the PipelineSource registry.
#   5. **CONFIRMED GAP, pass 9**: there is no per-workspace opt-in lever at the dispatcher or
#      graph level for which capability nodes run — EVERY registered node runs for EVERY
#      workspace on EVERY scheduled `quality_check_task` invocation (confirmed:
#      `SCHEDULABLE_ACTIONS`/`ACTION_REQUIRED_INPUTS`, `scheduled_agents_routes.py:71-90`,
#      select which GRAPH runs, not which NODES inside it run). This matches Invariant 8's
#      design (no connection configured → the node's own internal skip fires, never an error)
#      but means BH-1054 CANNOT reuse any existing per-workspace toggle — it must build its
#      own internal "no pipeline source configured → skip silently" check, exactly like
#      longitudinal_node.py already does for its own config absence. This is not extra scope
#      beyond what Invariant 8 already required, but it should not be assumed "already solved
#      by the dispatcher" either — confirmed there is no dispatcher-level mechanism to lean on.

# TYPE NOTE (fixed pass 34, cold-read gap, SHARPENED pass 37): `Capability` and
# `RequestContext` below are NOT existing brightbot types — they come from
# pluggable-scalable.md's canonical Ports & Adapters ILLUSTRATION (`~/.claude/rules/
# pluggable-scalable.md:11`), not a real importable module. Both are NEW, to be defined by
# whoever builds BH-1042, in `pipeline_watchdog_node.py` or a sibling module.
#
# CORRECTED pass 37 — the earlier draft's RequestContext was a THINNED-DOWN version of the
# canonical illustration, dropping 2 of 6 fields without flagging the omission. The REAL
# canonical shape (rules file, verbatim): "the ambient bundle every port call carries —
# workspace_id, correlation_id, principal, deadline, budget_remaining, tenant_tier.
# Propagated via contextvar; stamped onto spans per ai-observability." The earlier draft
# below only had workspace_id + optional deadline — missing correlation_id (needed to trace
# a single watchdog poll cycle across its async calls to dbt_cloud_tools.py/
# quality_tools.py/the dual-write, exactly the kind of cross-call tracing this spec's own §9
# Observability Contract needs) and principal (needed for THIS SPEC'S OWN Invariant 14 —
# "workspace scoping SHALL be resolved exclusively from the validated MCP principal," which
# requires a principal object to resolve FROM; omitting it from RequestContext while
# requiring it in Invariant 14 is an internal inconsistency, not a deliberate simplification).
#   Capability = Literal["JOB_STATUS", "DISK_METRICS"]  # plain string enum, no need for more
#   @dataclass(frozen=True)
#   class RequestContext:
#       workspace_id: str
#       principal: "Principal"          # RESTORED pass 37 — required by this spec's own
#                                        # Invariant 14; the MCP principal object, not a
#                                        # caller-supplied workspace_id (per get_anomalies'/
#                                        # get_pipeline_health's corrected convention)
#       correlation_id: str | None = None  # RESTORED pass 37 — for tracing one poll cycle
#                                        # across the watchdog's async calls; optional here
#                                        # only because no existing brightbot correlation-id
#                                        # generator was confirmed to exist for this pass —
#                                        # do NOT treat "optional" as "skip it," wire a real
#                                        # generator (e.g. uuid4()) at implementation time
#       deadline: datetime | None = None  # optional; wire up only if a real timeout need appears
#       budget_remaining: float | None = None  # OMITTED deliberately for THIS spec — no
#                                        # per-workspace $ budget concept exists yet in
#                                        # brightbot's pipeline-watchdog context; do not
#                                        # invent one here, this is a genuine, scoped omission
#                                        # (unlike correlation_id/principal, which were
#                                        # accidental)
#       tenant_tier: str | None = None  # OMITTED deliberately for THIS spec, same reasoning
#                                        # as budget_remaining — no tenant-tier concept is
#                                        # consumed anywhere in this spec's invariants
# Do not go looking for these in an existing brightbot module — they don't exist yet.

# PipelineSource: discriminated union over existing connection types, no new vendor SDK at call sites
class PipelineSource(Protocol):
    def capabilities(self) -> frozenset[Capability]: ...   # e.g. JOB_STATUS, DISK_METRICS
    async def poll_health(self, *, ctx: RequestContext) -> list[PipelineHealthSignal]: ...

# Registry (verified pass 9 — modeled EXACTLY on the real, established BrightHive convention:
# CONNECTION_CLASSES: dict[str, type[WarehouseConnection]], brightbot/tools/warehouse_connections.py:1230-1235,
# dispatched by WarehouseConnectionFactory.create_connection() at lines 1241-1259. Plain
# module-level dict, string key, no decorator magic — same shape as AGENT_REGISTRY
# (workflow_agent/registry.py:31). This is the ONLY registry convention with 2+ confirmed
# instances in the codebase — follow it, don't invent a different shape.)
PIPELINE_SOURCE_ADAPTERS: dict[str, type[PipelineSource]] = {
    DBT: DbtPipelineSource,
    DATABRICKS: DatabricksPipelineSource,
    ETL_GENERIC: EtlGenericPipelineSource,
}

def build_pipeline_source(*, source_type: str, config: dict[str, Any]) -> PipelineSource:
    # CORRECTED pass 16 (triple-click-zoom) — verified against the REAL
    # WarehouseConnectionFactory.create_connection() (warehouse_connections.py:1238-1260),
    # not paraphrased. Two real divergences found and fixed here:
    #
    # 1. `config: dict` was under-typed relative to the real precedent's own
    #    `params: dict[str, Any]` (constructor signatures at warehouse_connections.py:53,
    #    251, 436, 716 all use `dict[str, Any]`, never a bare `dict`) — fixed above.
    #
    # 2. Bracket-indexing (`PIPELINE_SOURCE_ADAPTERS[source_type]`) raises a raw, unhelpful
    #    `KeyError` on an unknown/typo'd source_type. The REAL precedent does NOT do this —
    #    it uses `.get(wh_type)` (warehouse_connections.py:1249) and only raises after
    #    exhausting its lookup, with a hand-written, actionable `ValueError`
    #    ("Cannot determine warehouse connection type...", lines 1258-1260). Mirror THAT
    #    error-handling shape, not a bare KeyError:
    adapter_cls = PIPELINE_SOURCE_ADAPTERS.get(source_type)
    if adapter_cls is None:
        raise ValueError(
            f"Unknown pipeline source_type {source_type!r} — no adapter registered in "
            f"PIPELINE_SOURCE_ADAPTERS. Known types: {sorted(PIPELINE_SOURCE_ADAPTERS)}"
        )
    return adapter_cls(config=config)
    # NOTE: the real precedent is also a CLASS with an instance method
    # (`WarehouseConnectionFactory.create_connection(self, ...)`, not `@classmethod`/
    # `@staticmethod`), while this spec keeps `build_pipeline_source` as a bare module-level
    # function — a deliberate divergence, not an oversight: `AGENT_REGISTRY`
    # (workflow_agent/registry.py:31) is the OTHER real 2+-instance registry precedent in
    # this codebase and IS a bare module-level dict/function, so both real shapes exist in
    # this org's own code. A bare function is simpler and sufficient here since this
    # factory carries no instance state (unlike WarehouseConnectionFactory, which doesn't
    # actually need instance state either, but was written as a class first) — confirm this
    # choice at implementation time rather than assume either shape is "more correct."

# COST OF ADDING A NEW ADAPTER TYPE (verified pass 9 against the real warehouse-registry
# precedent — corrects BH-1044/1045's earlier "registry entry, single switch site" framing,
# which understated this): tracing the hypothetical warehouse-side addition of a new type
# touches (1) a type Literal/enum definition, (2) the new connection/adapter class itself,
# (3) a type-mapping function (external string -> internal type), (4) type-specific branches
# inside the consuming tool class, and (5) a platform-core GraphQL enum change IF the type is
# a cross-repo contract.
#
# RESOLVED pass 10 (was flagged unverified in pass 9): dbt IS a live cross-repo contract —
# `TransformationServiceProvider` enum (platform-core src/graphql/schema/typedefs.ts:266-269)
# already has DBT_CLOUD (+ DEEPNOTE). Databricks and generic-ETL have ZERO coverage anywhere
# in platform-core's schema (confirmed by grep, not inferred) — item (5) genuinely applies to
# BH-1044 (Databricks), UNLESS Databricks connections are stored as brightbot-only secrets with
# no platform-core-visible service record (mirroring dbt's own Secrets Manager pattern,
# `dbt/cloud-api/{service_id}`, which does NOT require a schema change per se — the schema
# entry backs the WORKSPACE-FACING connection config, not the secret storage). This distinction
# — "is there a customer-configurable connection UI backed by a GraphQL type" vs. "is this a
# brightbot-internal secret the watchdog reads" — determines whether BH-1044 needs a
# platform-core PR. Make this decision explicit in BH-1044, don't leave it implicit.

# PipelineHealthSignal — complete field list (verified pass 7; prior revisions only
# mentioned fields scattered across §2/§7/§9, this is the single source of truth):
@dataclass(frozen=True)
class PipelineHealthSignal:
    workspace_id: str
    source_type: Literal["dbt", "databricks", "etl"]
    job_id: str                       # the dbt job id / Databricks job id / ETL job identifier
    failure_type: str                 # the category/stage value, e.g. "dbt_run_failure",
                                       # "source_disk_low" — see the taxonomy list below.
                                       # Cooldown key (Invariant 3, Property 1) is
                                       # (workspace_id, source_type, job_id, failure_type) —
                                       # a 4-tuple, CORRECTED pass 17: job_id alone is not
                                       # globally unique across customers' dbt Cloud/
                                       # Databricks accounts, and BrightRoutines' own
                                       # workspace-safety comes from query-layer
                                       # partitioning, not its key shape — this spec's
                                       # cooldown key must include workspace_id explicitly
                                       # rather than relying on partitioning alone.
    severity: Literal["info", "warning", "critical"]
    root_cause_class: "RootCauseClass"   # DATA_SHAPE | JOB_RUNTIME, see below
    detected_at: datetime
    diagnosis: str                    # plain-language root-cause summary, shown in both
                                       # the Slack/webapp alert and (if DATA_SHAPE) the PR body

# Its delivery function MUST perform the
# dual-write BH-1053 resolves (or the single unified write, if BH-1053 picks that option):
#   1. writeNotificationSignal()-equivalent write to the OLD NOTIFICATIONS_TABLE (Slack poller reads this)
#   2. notificationRecipients-equivalent write to NotificationInbox (webapp reads this)
# A signal that only performs (1) is Slack-visible but webapp-invisible, and vice versa —
# this is the exact bug BH-1053 catches. Do NOT add a third parallel event table.
#
# EXACT REAL SIGNATURES, verified pass 15 (triple-click-zoom) — not paraphrased, and this
# closes a gap: earlier passes treated "dual-write" as roughly "call two functions with the
# same payload." CONFIRMED that is WRONG — the two paths take genuinely different shapes,
# and BH-1053 remains unshipped (no unification exists; both paths are still independent,
# confirmed by direct read — neither imports the other):
#
#   (1) writeNotificationSignal(input: WriteNotificationInput) — Promise<WriteNotificationResult>
#       (platform-core/src/graphql/service/aws/notification-signal.ts:46)
#       Fields: workspaceId, stage, status ("passed"|"failed"|"degraded" — enforced, :65-67),
#       optional assetId/assetName/runContext/metadata(string)/ttlDays/visibility/
#       idempotencyKey/targetUserId. ONE row per workspace EVENT (not per user) —
#       PutItemCommand into NOTIFICATIONS_TABLE_NAME.
#
#   (2) NotificationInbox.deliver(params) — (notification-inbox.ts:80-124)
#       Fields: userId (REQUIRED, per-recipient), workspaceId, eventId, stage, status,
#       timestamp, category (DERIVED by resolveSignal(), NOT caller-supplied),
#       displayJson/detailJson (PRE-RENDERED presentation payloads, ALSO built by
#       resolveSignal() — not the raw PipelineHealthSignal fields), detailType, ttl.
#       ONE call PER WORKSPACE MEMBER — the real caller, notificationRecipients
#       (notifications.ts:436-552), loops over Workspace.findActiveMembersByWorkspaceId
#       and calls .deliver() once per member.
#
# CONSEQUENCE FOR THIS TICKET'S IMPLEMENTER: a watchdog's PipelineHealthSignal payload does
# NOT directly satisfy write (2)'s shape. Before calling NotificationInbox.deliver(), the
# delivery function MUST: (a) resolve the workspace's active member list (a real, separate
# lookup — NOT already done by anything in this spec's watchdog node), (b) run the signal
# through resolveSignal() (or an equivalent classifier) to derive category/displayJson/
# detailJson — the SAME renderer machinery Invariant 15 already flags as missing a
# registered case for 5 of this spec's 6 new stage values. "Dual-write" is therefore real
# integration work with two structurally different targets, not a trivial fan-out of
# identical arguments — size estimates for BH-1054/BH-1046 should account for this.
#
# CRITICAL, verified pass 35 (cross-checking a rendering gap found in the sibling
# lineage-aware-data-quality.md spec — GC-12's anomaly notifications were found to dead-end
# with zero visible content because neither brightbot-slack-server nor brighthive-webapp has
# a rendering CASE for the "longitudinal" stage; the dual-write succeeds but nothing displays):
# THE SAME GAP EXISTS HERE, CONFIRMED BY DIRECT CODE CHECK, for 5 of the 6 new stage values.
#   - "dbt_run_failure" — SAFE. Real renderer exists on BOTH sides: brightbot-slack-server's
#     formatter.ts:152→423 (renderDbtFailureDetails, reads job_id/model_name/error into real
#     text) AND brighthive-webapp's mappers.ts:33 ("dbt run failed" label) +
#     constants.ts:159 (grouped under pipeline). This one is genuinely reused, not just
#     registered-and-ignored.
#   - "dbt_run_stale", "databricks_job_failure", "databricks_cluster_unhealthy",
#     "etl_job_failure", "source_disk_low" — ALL 5 DO NOT EXIST in either repo's stage
#     type union (brightbot-slack-server's NotificationStage, types.ts:2-36;
#     brighthive-webapp's BackendStage, types.ts:22-50). At runtime, Slack falls through to
#     formatter.ts:172's `default: return []` (no detail text); webapp has no label in
#     mappers.ts/constants.ts. The dual-write to NOTIFICATIONS_TABLE/NotificationInbox would
#     SUCCEED, but produce a notification with NO VISIBLE CONTENT for 5 of these 6 stages —
#     identical to the bug found in the sibling spec, just not yet shipped/discovered here.
#
# CONSEQUENCE: this spec's own Invariant 1 ("SHALL reach BOTH live surfaces... a signal
# visible on only one surface is an incomplete emission") does not go far enough — a signal
# can be technically present in BOTH tables and STILL be invisible to a human on both, because
# "present in the table" and "rendered as visible text" are different layers. See new
# Invariant 15 below. New tickets required (see §6 Dependencies, §Ticket Breakdown) to add
# real renderers for these 5 stages in BOTH repos, mirroring dbt_run_failure's own pattern —
# this is NOT optional polish, it's the difference between "the demo works" and "the demo
# silently shows an empty notification."

# PipelineHealthSignal also carries a root_cause_class, set by the watchdog's classifier,
# that determines which remediation path applies (see Invariant 9):
class RootCauseClass(Enum):
    DATA_SHAPE = "data_shape"   # resolves to one of self-healing-pipelines.md's 4 modes
    JOB_RUNTIME = "job_runtime" # no data-shape signature; retry/escalate/alert-only

# MCP tool — mirrors get_anomalies (BH-671) precedent
# CRITICAL, FIXED pass 26 — the original draft (workspace_id as a request param) was a P0
# cross-tenant spoofing bug, caught by re-deriving this signature against get_anomalies'
# actual convention (never re-checked since pass 1 drafted it). workspace_id is NEVER a
# parameter — sourced from the validated MCP principal only, exactly like get_anomalies_impl
# (brightbot/mcp/tools/longitudinal.py). This is a repo-wide, TESTED invariant
# (test_no_principal_fields_in_tool_args, tests/unit/mcp_server/test_tool_invariants.py) —
# violating it here would have been spoofable: a Workspace-A caller passing Workspace-B's id.
GET /mcp/tools/get_pipeline_health
  Request:  { source_type: "dbt" | "databricks" | "etl" | None }
  # workspace_id resolved server-side from principal.workspace_id — NOT a request field.
  Response 200: { signals: list[PipelineHealthSignal], as_of: datetime }
  Response 4xx: { error: "forbidden" }
  # "workspace_not_found" removed — meaningless once workspace_id isn't caller-supplied;
  # the principal's own workspace always exists by construction.
```

**Registration is lightweight, not a BH-115-style phased rollout** (verified 2026-07-10, pass 6
— `get_anomalies` traced end-to-end as the precedent). `get_anomalies` lives in the always-on
`_CORE_TOOL_MODULES` bucket (`brightbot/mcp/server.py:46-52`), outside BH-115's
`_*_TOOL_MODULES` phase/feature-flag system entirely — that phase system describes a
historical rollout structure, not a per-new-tool requirement. Concrete file list for
`get_pipeline_health` (a READ tool, so the catalog row is documentation/drift-guard, not an
active permission gate — `enforce_tool_permission()` in `server.py:154-172` only raises for
`write=True` tools):

1. `brightbot/mcp/tools/<module>.py` — `@mcp.tool() async def get_pipeline_health(...)` inside a `register(mcp)` function (reuse the `longitudinal` module or add a sibling).
2. `brightbot/mcp/server.py` — add the module to `_CORE_TOOL_MODULES` if new (no-op if reusing an already-registered module).
3. `brightbot/mcp/capabilities.py` — one `_t("get_pipeline_health", ..., <ToolPermission>)` catalog row. **CI-enforced** (`tests/unit/mcp_server/test_permissions.py:130-149` asserts every live tool has a catalog cell) — skipping this fails CI, not silently.
4. Live-tool enumeration tests (`test_tool_invariants.py`, `test_mcp_live_tools.py`-style lists) — add the new tool name wherever such lists exist.
5. A unit test for the tool's own implementation + registration, per `brightbot/mcp/tools/CLAUDE.md` convention.

## 3. Invariants (DbC)

1. `WHEN a PipelineHealthSignal is emitted, THE System SHALL reach BOTH live surfaces
   (Slack via the OLD NOTIFICATIONS_TABLE write path, webapp via NotificationInbox) — a
   signal visible on only one surface is an incomplete emission, not a partial success.
   No FOURTH parallel event table SHALL be introduced. **SHARPENED pass 15**: these two
   writes are NOT interchangeable-shape calls. writeNotificationSignal() takes ONE row per
   workspace event; NotificationInbox.deliver() requires a PER-MEMBER fanout (one call per
   active workspace member, via Workspace.findActiveMembersByWorkspaceId) plus
   category/displayJson/detailJson DERIVED by resolveSignal() — not the raw
   PipelineHealthSignal fields passed straight through. The delivery function MUST perform
   both the member-list lookup and the resolveSignal() classification before calling
   NotificationInbox.deliver(), not just re-serialize the same signal object twice.`
2. `WHEN the watchdog is scheduled, THE System SHALL ride the EXISTING scheduled dispatcher +
   run_context (BH-670 precedent) — no new EventBridge rule, no new cron infra.`
3. `WHEN the same underlying failure — keyed by (workspace_id, source_type, job_id,
   failure_type) — persists across polling cycles within a cooldown window, THE System SHALL NOT re-emit a duplicate
   alert. Default cooldown = 1 hour, workspace-overridable (config seam per code-style.md's
   "no hardcoded values without an override" convention — no magic number without a named
   constant). **Verified pass 31 by direct code read (corrects an imprecise citation)**:
   replicate BrightRoutines' cooldown IDIOM — a `cooldown_until` timestamp field, set once when
   the alert fires (`cooldown_until = now + cooldown_window`), checked on each subsequent poll
   via `cooldown_until > now → suppress` (the actual comparison lives at
   `brightbot/routines/detector.py:478-482`, not 476-480 as an earlier memory note claimed).
   **There is NO shared storage to import** — BrightRoutines' `cooldown_until` is a field on
   its own `RecurringAutomationPattern` DynamoDB item (`routines/dtos.py:257`), keyed by
   `pattern_id`, tightly coupled to that data model. This spec's watchdog needs its OWN item
   shape keyed by `(source_type, job_id, failure_type)` — copy the TTL-comparison PATTERN,
   do not attempt to reuse or extend BrightRoutines' actual table/store.
   **CRITICAL, verified pass 17 (triple-click-zoom) — the real precedent's key alone is NOT
   workspace-safe, and neither is this spec's proposed composite key as drafted.** Confirmed:
   BrightRoutines' real workspace-safety comes from `pattern_store.list_patterns_by_status
   (workspace_id=workspace_id, ...)` (`detector.py:466-468`) PARTITIONING the query by
   workspace BEFORE the `pattern_id`/`cooldown_until` check ever runs — `pattern_id` alone
   is NOT globally unique across workspaces in storage, it only behaves safely because every
   lookup is pre-filtered to one workspace. The composite key `(source_type, job_id,
   failure_type)` as written here has the SAME gap: `job_id` (e.g. a dbt Cloud job ID) is
   NOT guaranteed unique across different customers' dbt Cloud accounts, and two workspaces
   sharing a colliding `job_id`+`failure_type` could suppress each other's alerts if the
   cooldown store is not ALSO partitioned by workspace at the query/lookup layer. FIX:
   `workspace_id` MUST be part of either (a) the cooldown key itself
   (`(workspace_id, source_type, job_id, failure_type)`, a 4-tuple, not 3), or (b) the
   storage partition the lookup queries against — mirroring BrightRoutines' actual pattern,
   not just its comparison idiom. BH-1054's implementer MUST pick one explicitly; do not
   ship a 3-tuple key against unpartitioned storage.`
4. `IF a signal's root_cause_class is DATA_SHAPE but has no matching mode in
   self-healing-pipelines.md's 4-mode taxonomy, THEN THE System SHALL fall back to
   alert-only — it SHALL NOT guess a fix.`
5. `WHEN a SQL Server is monitored for disk/job health, THE System SHALL do so through the
   EXISTING warehouse-connection machinery already required to catalog it as a BYOW source —
   no new on-host collector for this signal class. Concrete call chain (verified pass 7 —
   "WarehousePort" is Ports & Adapters terminology, not a literal class name; the real
   equivalent is confirmed to exist): get_warehouse_connection_info(workspace_id)
   (brightbot/tools/platform_queries.py:361) resolves credentials → WarehouseTool(...)
   (brightbot/utils/warehouse.py:184) builds the connection via
   WarehouseConnectionFactory.create_connection() (warehouse_connections.py:1241) →
   .connection.execute_query(sql) (warehouse.py:510) runs the DMV query. Existing consumers
   of this exact pattern: sv_qc_tools.py:114, workflow_agent/tools.py:174 — follow their
   usage, don't reinvent. **Known gap**: no dedicated SQL-Server dialect class exists today
   (SynapseConnection is the nearest match, Azure Synapse dialect, not true SQL Server) — this
   spec's BH-1045 must add one (or confirm Synapse's dialect is close enough for
   sys.dm_os_volume_stats specifically) before this invariant is satisfiable end-to-end.
   **SECOND KNOWN GAP, found pass 12 (triple-click-zoom), CRITICAL — the "no new
   connectivity, protocol, or on-host software" claim is TRUE but INCOMPLETE, missing a
   permission grant.** Confirmed against platform-core: EVERY BYOW connection type's real
   provisioning code (`azure_synapse.ts:114-131`, `snowflake.ts:156`, `redshift.ts:124,140`)
   grants ONLY database/schema/table-level `GRANT SELECT` — no code, doc, or onboarding copy
   anywhere in platform-core mentions `VIEW SERVER STATE`, `sysadmin`, or any server-level
   grant (grep, zero hits). `sys.dm_os_volume_stats` requires server-level `VIEW SERVER
   STATE` (or sysadmin), NOT the database-level SELECT a standard BYOW setup grants. This
   means a customer's EXISTING BYOW connection (even a true SQL Server one, once BH-1045's
   dialect gap above is closed) would get a permissions error (SQL error 229/18456-class,
   NOT a connectivity failure) the first time this query runs — confirmed
   `WarehouseServiceConfigOutput` (`typedefs.ts:2908-2917`) has no field recording granted
   permission level, and `azure_synapse.ts:133-138`/`byow-preview.ts:402-403` catch ALL query
   failures generically with no permission-error differentiation. BH-1045 or a new companion
   ticket MUST add: (a) a NEW grant step (`GRANT VIEW SERVER STATE TO [user]`) to the
   provisioning flow, (b) setup documentation telling the customer this specific new grant is
   needed, (c) permission-error-specific handling so a missing grant fails with an actionable
   message, not a generic query error. This is a genuine, if small, customer-side
   administrative action — "no new connectivity/protocol/on-host software" undersells it as
   zero customer action, which it is not.`
   **CONFIRMED pass 38 (triple-click-zoom) — the exact query text, never shown before this
   pass (only referenced by DMV name in every earlier pass), verified to pass the REAL
   `SynapseConnection.execute_query()` safety guard as written:**
   ```sql
   SELECT
       DB_NAME(vs.database_id) AS database_name,
       mf.name AS logical_file_name,
       vs.total_bytes,
       vs.available_bytes,
       CAST(vs.available_bytes * 100.0 / vs.total_bytes AS DECIMAL(5,2)) AS percent_free
   FROM sys.master_files AS mf
   CROSS APPLY sys.dm_os_volume_stats(mf.database_id, mf.file_id) AS vs
   ```
   Confirmed against the real guard (`warehouse_connections.py:360-383`,
   `warehouse_base.py:131-164`): the multi-statement check (`";" in query.rstrip(";")`)
   strips trailing semicolons FIRST, then checks for any remaining — a single trailing `;`
   (habit-appended) passes cleanly; there is no keyword blocklist for `CROSS APPLY`, no
   schema-prefix check for `sys.`-qualified identifiers (the guard does zero semantic SQL
   parsing, no AST, no `sqlparse`), no multi-line-string check (`.lstrip().upper()
   .startswith("SELECT")` only inspects the leading token), and no query-length/JOIN-count
   limit anywhere in either function. This exact query is confirmed buildable and
   guard-compliant TODAY — the remaining gaps are the dialect class (above) and the
   permission grant (above), not the query text itself.
6. `WHILE BrightSignals' 3-way split-brain (BH-1053, see §6) is unresolved as a UNIFIED write
   path, THE System's watchdog SHALL perform the explicit dual-write in Invariant 1 itself —
   it SHALL NOT wait for BH-1053 to add a fourth ad-hoc path.`
7. `WHEN a surgical PR is opened from a watchdog-detected failure, THE System SHALL require
   human approval before merge — no auto-merge path exists for any failure mode.
   **CRITICAL, verified pass 24 — this is NOT currently a code-level guarantee anywhere in
   BrightHive, it must become one for this spec specifically.** self-healing-pipelines.md's
   remediation loop "reuses the dbt agent's existing scoped-PR path" — that shared tool
   surface (`brightbot/agents/dbt_agent/tools/github_tools.py`) ALSO contains a fully wired,
   actively-registered `github_merge_pull_request` tool (line 509, calling a real Platform
   Core mutation that actually merges via GitHub's API — not a stub). The ONLY existing
   safeguard is a system-prompt instruction ("only call this when the user explicitly asks,"
   `dbt_react_system_prompt.py:119-122`) — no code-level gate, no state flag, no permission
   check, and no BrightHive-managed GitHub branch protection backstop (confirmed: zero
   branch_protection/required_reviews enforcement anywhere; BrightHive's own docs say this is
   the customer's responsibility). THIS INVARIANT SHALL be satisfied by the remediation loop's
   own tool surface NEVER including `github_merge_pull_request` in its available tools —
   a code-level exclusion in whatever wires tools to the remediation loop's LangGraph node,
   not a restated prompt instruction. Reusing the dbt agent's PR-CREATION path is fine; reusing
   its full toolset (which includes merge) is not, without this exclusion.
   **Confirmed pass 25**: this is the ONLY destructive tool in `github_tools.py` (7 tools
   total: 3 read, 3 additive-write, 1 destructive) — the exclusion above is sufficiently
   scoped, no sibling tool needs the same treatment in this file. Separately and NOT this
   spec's problem to fix: `ActionClass.DESTRUCTIVE` (the tag already on this tool) is
   documented to be pure audit-logging that never blocks execution — a systemic false-safety
   signal across the whole codebase, flagged to Kuri directly, out of scope for BH-1036/1037.
   **CONCRETE MECHANISM, pass 18 (triple-click-zoom) — the exact code shape, verified against
   `dbt_agent_react.py`, not left abstract.** `dbt_agent_react.py`'s own `DBT_REACT_TOOLS`
   (lines 150-205) is a flat `list[...]` literal built by importing each `@tool`-decorated
   function INDIVIDUALLY from `brightbot.agents.dbt_agent.tools` — it is NOT built by
   filtering a pre-bundled list, and `_DBT_PINNED_TOOLS` (a `frozenset[str]` of names, line
   230) only controls prompt-caching pin behavior, NOT which tools are bound — it is
   IRRELEVANT to this exclusion requirement, do not confuse the two. A real, existing
   precedent for cross-agent SUBSET reuse already exists: `retrieval_agent_react.py:32`
   imports exactly one function (`introspect_warehouse_schema`) directly from a submodule of
   `dbt_agent/tools/`, bypassing the package's aggregate `__init__.py` re-export entirely.
   BH-1047 MUST follow this SAME pattern — import individual GitHub tool functions directly
   from `github_tools.py`, not filter `DBT_REACT_TOOLS` by exclusion (which would also drag
   in unrelated dbt-specific tools like `explore_dbt_project`/`register_transformation` that
   don't belong in a remediation agent):
   ```python
   from brightbot.agents.dbt_agent.tools.github_tools import (
       github_read_file, github_list_files, github_list_branches,
       github_create_branch, github_commit_file, github_commit_multiple_files,
       github_create_pull_request,
       # github_merge_pull_request intentionally OMITTED — see Invariant 7.
   )
   REMEDIATION_TOOLS: list = [
       github_read_file, github_list_files, github_list_branches,
       github_create_branch, github_commit_file, github_commit_multiple_files,
       github_create_pull_request,
   ]
   ```
   Pass this list to `create_agent(model=..., tools=REMEDIATION_TOOLS, ...)` (the same
   construction call `dbt_agent_react.py:587-589` uses) — there is no raw `llm.bind_tools()`
   call to write; `create_agent` does that internally. Property 2's unit test enumerates
   THIS list (or whatever the real construction call resolves to) and asserts
   `"github_merge_pull_request"` is absent by name.`
8. `IF a workspace has no dbt/Databricks/SQL-Server connection configured, THEN THE System
   SHALL skip that source's polling — no error, no signal, no cost.`
9. `IF a signal's root_cause_class is JOB_RUNTIME (no data-shape signature), THEN THE System
   SHALL NOT fabricate a new surgical-PR failure mode — its only remediation actions are
   retry, escalate-with-diagnosis, or alert-only. Surgical PRs remain exclusive to
   root_cause_class=DATA_SHAPE signals routed into self-healing-pipelines.md's existing 4
   modes.`
10. `WHEN a source API (dbt Cloud, Databricks Jobs) returns 429 or a rate-limit signal, THE
    System SHALL back off (respecting Retry-After if present, exponential otherwise) and
    SHALL NOT retry that source again within the same poll cycle — a rate-limited poll skips
    that cycle for that source rather than hammering it. This applies even though per-workspace
    credentials mean no cross-tenant rate-limit risk (verified 2026-07-10): a single
    workspace's dbt Cloud account can still be self-rate-limited by its own polling cadence.`
11. `WHEN fanning out concurrent calls within a single poll (e.g. fetching failure details
    across multiple failed job steps), THE System SHALL cap concurrency per source — it SHALL
    NOT reuse dbt_cloud_tools.py's existing uncapped asyncio.gather fan-out pattern
    (_analyze_run_errors, dbt_cloud_tools.py:485-494) without adding a bound, since a
    background watchdog runs this unattended across every connected workspace, amplifying an
    already-uncapped pattern.`
12. `IF a signal source's minimum useful polling interval is sub-hourly (e.g. queue-depth/DLQ
    monitoring, BH-1051), THEN THE System SHALL NOT silently ride the existing
    cadenceToCron()/nightshift scheduling path as-is — cadenceToCron only supports
    DAILY..QUARTERLY (verified 2026-07-10; **SHARPENED pass 21, triple-click-zoom**: the real
    enum, `routine-scheduler-client.ts:165-180`, has 5 cases, not the shorthand's implied 4 —
    DAILY (`0 8 * * *`), WEEKLY (`0 8 * * MON`), BIWEEKLY (`0 8 1,15 * *`), MONTHLY
    (`0 8 1 * *`), QUARTERLY (`0 8 1 1,4,7,10 *`) — finest real granularity is DAILY at
    08:00, zero sub-hourly/sub-daily option exists). The implementer SHALL make an explicit
    choice: extend cadenceToCron + _to_scheduler_cron with a validated sub-hourly case, OR
    use a dedicated, narrowly-scoped EventBridge rule for this signal class only (an
    exception to Invariant 2's "no new EventBridge," justified because Invariant 2 was
    written for job-status/data-quality signals where nightshift cadence is adequate, not
    for sub-hourly-only signal classes it never anticipated). **THIRD OPTION, confirmed
    pass 21**: neither of the above may be the right call at all — a native **CloudWatch
    Alarm on the SQS queue's own `ApproximateNumberOfMessagesVisible`/DLQ-depth metric**
    achieves sub-minute evaluation granularity with ZERO new BrightHive scheduling code
    (no cadenceToCron extension, no new EventBridge rule invoking a brightbot Lambda) —
    confirmed both `cadenceToCron()`'s output and the dispatcher's EventBridge Scheduler
    path are the SAME substrate other watchdogs ride
    (`scheduled_agents_routes.py:271-294`→`_to_scheduler_cron`→
    `scheduled_agent_dispatcher_stack.py:32-38,145-148`), so extending either changes shared
    infra; a scoped CloudWatch Alarm changes nothing shared. BH-1051's implementer MUST
    evaluate this third option BEFORE choosing to extend cadenceToCron or add a new
    EventBridge rule — it may be strictly cheaper and lower-risk than either.`
13. `WHEN a PipelineHealthSignal's diagnosis field is generated from raw job error logs (dbt
    Cloud run details, SQL Server error text), THE System SHALL pass it through the EXISTING
    scrub_text() (brightbot/audit/redaction.py) before it reaches ANY of the 4 sinks (Slack,
    NotificationInbox, GitHub PR body, AND CloudWatch audit logs — see pass 28 below) — no
    sink SHALL receive unscrubbed diagnosis text.
    **Known residual risk, verified pass 23**: scrub_text() only strips credential/secret
    SHAPES (tokens, connection strings, key=value secrets) — it explicitly is NOT a PII
    scrubber (per its own docstring) and does NOT catch customer data values that can appear
    in a raw SQL error (e.g. a failed constraint dumping the offending row's actual data).
    This invariant closes the credential-leakage risk (a real, immediate concern — connection
    strings/tokens DO show up in misconfigured job logs) but does NOT close customer-PII/
    data-value leakage, which has no existing BrightHive pattern to reuse. If the threat model
    requires closing that gap too, it is NEW scope, not a checkbox this invariant satisfies —
    do not let scrub_text()'s existence create false confidence.
    **CRITICAL, pass 28 (triple-click-zoom) — a FOURTH sink found, not previously counted.**
    The `@audit_action` decorator (`brightbot/audit/decorator.py:44-55,95-117`) on
    `github_create_pull_request` binds the FULL function arguments — including `body`, the
    complete PR description containing the diagnosis text — into `emit_action_audit()`
    (`audit_log.py:78-140`), which lands as a JSON log line in CloudWatch Logs. This path
    DOES call `redact()` (`audit_log.py:57-73`) first, but `redact()` is ALSO only
    credential-shape/key-name-based (`token`/`secret`/`password`-named fields plus the same
    credential value patterns as scrub_text()) — it does NOT target PII either. This means
    the SAME residual customer-data-value risk this invariant already flags for Slack/
    NotificationInbox/PR-body ALSO applies to CloudWatch audit logs, arguably at HIGHER risk
    (CloudWatch Logs Insights queries are broad-access within an AWS account, and log
    retention typically outlives a Slack message's visible/searchable lifespan). BH-1060's
    scope MUST be revised to cover all 4 sinks, not the original 3 — see BH-1060's ticket.`
14. `THE get_pipeline_health MCP tool SHALL NOT accept workspace_id as a request parameter —
    workspace scoping SHALL be resolved exclusively from the validated MCP principal
    (principal.workspace_id), exactly matching get_anomalies_impl's convention
    (brightbot/mcp/tools/longitudinal.py). **CRITICAL, verified pass 26**: this spec's own
    original §2 draft violated this — re-derive the signature from get_anomalies' actual
    convention, don't restate the original draft. A caller from Workspace A SHALL NOT be able
    to read Workspace B's pipeline health signals under any request shape. This is enforced
    repo-wide by test_no_principal_fields_in_tool_args
    (tests/unit/mcp_server/test_tool_invariants.py) — the new tool MUST pass that existing
    test, not a bespoke one.`
15. `A dual-write reaching BOTH NOTIFICATIONS_TABLE and NotificationInbox (Invariant 1) SHALL
    NOT be treated as "delivered" unless the signal's stage value also has a registered
    RENDERER on both surfaces. **CRITICAL, verified pass 35**: "present in the table" and
    "rendered as visible text" are different layers — direct code check confirmed
    brightbot-slack-server's formatter.ts:172 default case returns `[]` (empty, no detail
    text) for any NotificationStage not explicitly matched, and brighthive-webapp's
    mappers.ts/constants.ts have no label/grouping fallback either. Of this spec's 6 proposed
    stage values, only "dbt_run_failure" has real renderers today
    (formatter.ts:423 renderDbtFailureDetails; mappers.ts:33 + constants.ts:159). The other 5
    ("dbt_run_stale", "databricks_job_failure", "databricks_cluster_unhealthy",
    "etl_job_failure", "source_disk_low") SHALL NOT be considered demo-ready until a renderer
    exists on both surfaces — see BH-1067. This mirrors the identical dead-end confirmed for
    GC-12's `longitudinal_anomaly` stage in the sibling lineage-aware-data-quality.md spec
    (BH-1065/1066).`

## 4. Acceptance Criteria (BDD — Gherkin)

```gherkin
Feature: Proactive pipeline & ingestion monitoring

  Scenario: dbt job failure detected without being asked, visible on BOTH surfaces
    Given a workspace with a connected dbt Cloud project
    And its last scheduled job run failed
    When the watchdog capability node runs on its scheduled cadence
    Then a "dbt_run_failure" signal is written to the OLD NOTIFICATIONS_TABLE (Slack path)
    And the same signal is written to NotificationInbox (webapp path)
    And the user receives a Slack alert AND sees the item in the webapp inbox — neither alone

  Scenario: SQL Server disk monitoring with no MCP on the SQL Server
    Given a SQL Server connected to BrightHive as a BYOW source (existing warehouse-connection machinery, per Invariant 5 — not a literal "WarehousePort" class)
    And the SQL Server exposes no MCP server or agent of its own
    And the customer has granted VIEW SERVER STATE to BrightHive's service account (per
      Invariant 5's second known gap — a NEW grant beyond BYOW's standard database-level
      SELECT, without which this query fails with a permissions error, not silently)
    And BH-1067 has shipped a "source_disk_low" renderer on both Slack and webapp (per Invariant 15 — without it, this scenario dual-writes successfully but renders no visible text on either surface)
    When the watchdog queries sys.dm_os_volume_stats through the EXISTING warehouse connection
    And a database file's free space drops below the configured threshold (e.g. 20%)
    Then a "source_disk_low" signal is emitted
    And the user is alerted before the disk is exhausted, with real detail text on both surfaces
    And no new connectivity, protocol, or on-host software was installed on the SQL Server
      (the ONE new thing required is the VIEW SERVER STATE grant above — a permission
      change, not a connectivity/protocol/software change)

  Scenario: a missing VIEW SERVER STATE grant fails with an actionable error, not a silent gap
    Given a SQL Server BYOW connection with only the standard database-level SELECT grant
    When the watchdog attempts to query sys.dm_os_volume_stats
    Then the query fails with a permissions error (SQL error 229/18456-class)
    And this is surfaced as a permission-specific, actionable message — NOT the generic
      catch-all error handling azure_synapse.ts:133-138/byow-preview.ts:402-403 use today,
      which does not distinguish a permissions failure from any other query failure

  Scenario: repeated failure does not spam
    Given a "dbt_run_failure" signal was already alerted for job X in workspace A in the
      last cooldown window
    When the watchdog detects the same failure on job X in workspace A again before the
      cooldown expires
    Then no duplicate alert is sent

  Scenario: two workspaces sharing a colliding job_id do not suppress each other's alerts
    Given workspace A and workspace B both have a dbt job with the SAME job_id value
      (plausible across different customers' dbt Cloud accounts)
    And workspace A's job with that id already alerted "dbt_run_failure" within the cooldown
    When workspace B's job with the SAME id also fails with "dbt_run_failure"
    Then workspace B's alert is NOT suppressed by workspace A's cooldown
    And this holds because the cooldown key includes workspace_id (per Invariant 3's pass-17
      correction — a 3-tuple key without workspace_id would have failed this scenario)

  Scenario: DATA_SHAPE root cause routes to the existing surgical-PR loop
    Given a watchdog signal is classified root_cause_class=DATA_SHAPE
    And its root cause matches one of self-healing-pipelines.md's 4 existing modes (e.g. schema_drift)
    When the remediation loop evaluates it
    Then a surgical PR is opened per self-healing-pipelines.md's existing Gherkin scenarios
    And the PR requires human approval — it is never auto-merged

  Scenario: DATA_SHAPE root cause with no matching mode falls back to alert-only
    Given a watchdog signal is classified root_cause_class=DATA_SHAPE
    And its root cause matches none of self-healing-pipelines.md's 4 existing modes
    When the remediation loop evaluates it
    Then it falls back to alert-only and does not attempt a fix

  Scenario: JOB_RUNTIME root cause never gets a fabricated surgical PR
    Given a watchdog signal is classified root_cause_class=JOB_RUNTIME (e.g. a Databricks cluster OOM with no data-shape signature)
    When the remediation loop evaluates it
    Then it never opens a surgical PR for this signal
    And its only actions are retry, escalate-with-diagnosis, or alert-only

  Scenario: rate-limited source backs off instead of hammering
    Given a workspace's dbt Cloud account returns a 429 during a poll cycle
    When the watchdog receives the 429
    Then it backs off (honoring Retry-After if present) and skips that source for this cycle
    And it does NOT retry that same source again within the same poll cycle
    And other workspaces' polls are unaffected (per-workspace credentials, no shared bucket)

  Scenario: a sub-hourly signal source does not silently ride the nightshift cadence
    Given a signal source's minimum useful interval is sub-hourly (e.g. queue-depth/DLQ, BH-1051)
    When its capability node is scheduled
    Then it does NOT use cadenceToCron()'s 5 real cases (DAILY/WEEKLY/BIWEEKLY/MONTHLY/
      QUARTERLY, all fixed at 08:00) as-is
    And an explicit choice was made and documented among THREE options: (a) cadenceToCron/
      _to_scheduler_cron extended with a validated sub-hourly case, (b) a dedicated scoped
      EventBridge rule for this signal class only, or (c) a native CloudWatch Alarm on the
      SQS queue's own ApproximateNumberOfMessagesVisible/DLQ-depth metric — option (c)
      requires ZERO new BrightHive scheduling code and should be evaluated FIRST
    And dbt/Databricks/ETL job-status watchdogs (adequate at hourly-class cadence) are
      unaffected by this choice — it is scoped to sub-hourly sources only

  Scenario: watchdog owns the dual-write while BH-1053 is unresolved
    Given BrightSignals' 3-way split-brain (BH-1053) has not yet been unified
    When the watchdog emits any signal
    Then it explicitly performs both writes itself (old table + NotificationInbox)
    And it does NOT introduce a fourth independent event table while waiting for BH-1053

  Scenario: BH-1053 unification supersedes the dual-write without a behavior change
    Given BH-1053 later ships a single unified write entrypoint
    When the watchdog is updated to call that entrypoint instead of writing both tables itself
    Then the observable behavior (Slack alert + webapp inbox item) is unchanged
    And the watchdog's own dual-write code is deleted, not kept as a fallback

  Scenario: no configured source, no cost
    Given a workspace has no dbt, Databricks, or SQL Server connection configured
    When the watchdog's scheduled cadence fires
    Then no poll, no signal, and no error occur for that source type

  Scenario: diagnosis text is scrubbed before reaching any sink
    Given a raw dbt Cloud error log contains an accidentally-logged connection string with credentials
    When the diagnosis field is generated from that log
    Then scrub_text() runs on the diagnosis BEFORE it is written to Slack, NotificationInbox,
      a GitHub PR body, OR the CloudWatch audit log (4 sinks, corrected pass 28 — the audit
      log via @audit_action was previously uncounted)
    And the credential shape is redacted in all 4 sinks
    But note: this scenario does NOT prove customer PII/data-value redaction in ANY of the 4
      sinks — that is a known, separate, unclosed gap (BH-1060), now scoped across all 4,
      not just the original 3

  Scenario: remediation loop's tool surface excludes merge capability
    Given the remediation loop's LangGraph node is constructed with its bound tools
    When the tool list is enumerated (unit test, not a prompt read)
    Then "github_merge_pull_request" is NOT present in that list
    And this holds even though the SAME tool exists and is registered in dbt_agent's separate, on-demand toolset
    And the exclusion is a code-level tool-binding decision, not a system-prompt instruction

  Scenario: get_pipeline_health cannot be spoofed to read another workspace's signals
    Given a caller is authenticated as a principal belonging to Workspace A
    When they call get_pipeline_health with any request shape, including one attempting to pass a workspace_id for Workspace B
    Then the tool has no workspace_id parameter to accept in the first place
    And the returned signals are scoped exclusively to Workspace A (the caller's own principal.workspace_id)
    And no request shape can cause Workspace B's signals to be returned
```

## 5. Out of Scope

- Rebuilding BrightSignals' delivery/channel-adapter mechanism (it exists across 2 live
  surfaces; see BH-1053 for the eventual unification, which this spec does NOT block on —
  the watchdog performs the dual-write itself per Invariant 6, and migrates to BH-1053's
  unified entrypoint once it ships).
- Data-quality anomaly detection (already GC-12/longitudinal-monitoring.md — this spec is
  job/run-STATUS only).
- On-host collector / agent-installed-on-customer-infrastructure tier (documented as future
  work in BH-1045 for sources with no warehouse connection at all — not needed for the 7/17
  demo, since Frank's example is disk monitoring on an already-connected SQL Server).
- BrightRoutines MCP/A2A exposure (BH-1038–1041) — a separate, unrelated extension of a
  different system (chat-intent scheduling, not health monitoring); tracked independently.
- Auto-merge of any remediation PR, under any circumstance.
- Deciding WHICH sub-hourly scheduling approach to build (extend cadenceToCron vs. a scoped
  EventBridge rule) — Invariant 12 requires the choice be explicit and documented, but this
  spec does not mandate one; BH-1051's implementer decides, scoped narrowly to that signal
  class (see BH-1051 ticket).
- **Deciding whether ingestion signals get a symmetric MCP read tool** (verified pass 28:
  unlike `get_pipeline_health` for the monitoring group, no `get_ingestion_health`-style tool
  is currently spec'd for BH-1048-1052 — ingestion health would only reach Slack/webapp today).
  This spec does not mandate the decision; BH-1048's implementer decides. **If such a tool is
  ever added, it MUST be workspace_id-from-principal-only from the start** (per Invariant 14's
  corrected convention) — do not repeat pass 1's mistake of drafting workspace_id as a caller
  parameter.

## 6. Dependencies

| Dependency | Type | Status |
|---|---|---|
| Old `NOTIFICATIONS_TABLE` write path (`writeNotificationSignal`) | Blocking (watchdog writes here directly) | Live |
| New `NotificationInbox` write path (`notificationRecipients`) | Blocking (watchdog writes here directly) | Live |
| BH-1053 (3-way split-brain → unified write entrypoint) | Non-blocking — watchdog dual-writes until this ships, then migrates | Decision ticket filed, not yet resolved |
| Longitudinal Monitoring dispatcher/run_context pattern (GC-12, BH-670) | Blocking (pattern precedent) | Shipped + staging-verified; BH-670 confirmed fully wired 2026-07-10 (BH-768, PR #724) — closed precedent |
| Self-Healing Pipelines surgical-PR loop (GC-11, BH-526) | Blocking (remediation consumer) | Draft spec, not yet built |
| Existing WarehousePort BYOW connection mechanism (Snowflake/etc.) | Non-blocking (mechanism reused, not built here) | Live |
| **BH-1057: staging BYOW SQL Server connection ITSELF (a real instance, not the mechanism)** | **BLOCKING for the 7/17 demo specifically** — no SQL Server exists to connect through the mechanism above | **RESOLVED-ACTIONABLE pass 15 — RDS Web edition, ~3-5hrs same-day, zero code changes (reuses SynapseConnection/pymssql), concrete runbook in BH-1057. Was CRITICAL/unscoped in pass 14, now well-scoped.** |
| BH-1058: dbt Cloud job with deliberate-failure capability | Blocking for BH-1043's §10 e2e case | **RESOLVED-ACTIONABLE pass 16, CORRECTED pass 27 — one-time human UI setup (~1-2 hrs): create a job + one env-var-toggled model, zero new brightbot code (mirrors BH-1057). CRITICAL fix pass 27: the toggle must trigger a genuine RUNTIME SQL error (e.g. `select 1/0`), NOT `raise_compiler_error` — a compile-time error has no SQL-diagnosable signature and would fail to exercise DATA_SHAPE classification, defeating this fixture's purpose.** |
| dbt_cloud_tools.py, quality_tools.py on-demand tools | Non-blocking (reused as poll targets) | Live |
| AgentCore migration (BH-453) — watchdog node's HOST graph structure | Non-blocking (verified pass 19, SHARPENED pass 29 — not inferred, and now explicitly time-bounded) | LangGraph `StateGraph`/`add_node` unchanged by AgentCore's CURRENT leaf-runtime-only scope (`agentcore-deployment-migration.md`'s "Recommended Approach": only sub-agents — retrieval/analyst/governance/dbt — become AgentCore Container runtimes; the LangGraph Deep Agent SUPERVISOR remains the orchestration runtime) — safe to build on TODAY. **NOT a permanent guarantee**: CEMAF (`brightagent-v3`) is the CONFIRMED long-term supervisor replacement (`langgraph-cloud-detach.md:17,24`), using a structurally different `DAGExecutor` model, not `StateGraph`/`add_node` — this spec's watchdog capability nodes survive today's AgentCore leaf-runtime work unchanged, but would need a REAL redesign (as Goal/Result DTOs, per CEMAF's own migration notes, not a mechanical `add_node` port) once the supervisor layer itself migrates to CEMAF. Treat "unchanged by the migration" as scoped to AgentCore's current phase, not a claim about CEMAF's eventual arrival. |
| `scheduled_agent_dispatcher`'s LangGraph Cloud invocation path (`langgraph_action.py` → `/threads/{id}/runs`) | Non-blocking for THIS spec | Verified pass 19 (`langgraph-cloud-detach.md`, 2026-07-09): explicitly named as "a third, separate LangGraph Cloud dependency... not covered by either track." **BH-1059 filed** (tracking placeholder under BH-453) so this gap is visible when the migration track reaches it, rather than rediscovered later. |
| **BH-1067: renderers for 5 new notification stages on brightbot-slack-server + brighthive-webapp** | **BLOCKING for demo-visibility of `dbt_run_stale`, `databricks_job_failure`, `databricks_cluster_unhealthy`, `etl_job_failure`, `source_disk_low`** — the dual-write (Invariant 1) succeeds today, but nothing renders (Invariant 15) | **Filed pass 35** — mirrors `dbt_run_failure`'s existing pattern (`formatter.ts:423`, `mappers.ts:33`/`constants.ts:159`); not started |
| `airbyte_notification_webhook`'s existing auth client + connection-mapping (`app.py:47-59,97-101,141-159`) | Non-blocking (reused, not built, IF BH-1049 chooses Option A) | **CONFIRMED pass 13** — live, deployed, already-authenticated; its failure branch (`app.py:88-90`) is currently a no-op BH-1049 could extend cheaply instead of building a new poller |
| **BH-1071: `NOTIFICATION_SYSTEM_PLAN.md` stale-docs cleanup** | Non-blocking for 7/17; blocked BY BH-1053's decision (deploy path 3 for real, or retire it) before it can be finalized | **Filed pass 32** — the plan doc (never updated since 2026-04-20) describes 4+ pieces of never-built/undeployed infra as current (a `notification-subscriptions` table that was never created, a speculative DynamoDB Stream, a `notification_dispatcher_stack.py` file that doesn't exist, and SES email delivery the slack-server team's own README labels "Future direction") |

## 7. Correctness Properties

### Property 1: no duplicate alerting for a persistent failure

*For any* failure signal `(workspace_id, source_type, job_id, failure_type)` detected in
consecutive polling cycles within the cooldown window, at most one alert is delivered.
**CORRECTED pass 17**: workspace_id is a required part of this key — job_id alone is not
guaranteed unique across different customers' dbt Cloud/Databricks accounts (see Invariant
3's pass-17 note).

**Validates: §3 Invariant 3, §4 Scenario "repeated failure does not spam"**

### Property 2: remediation never bypasses human approval

*For any* surgical PR opened by the remediation loop, the PR is not merged by any automated
process — merge requires a human-initiated approval action. **Testable at the code level
(verified pass 24)**: the remediation loop's LangGraph node's available-tools list, at
construction time, does NOT include `github_merge_pull_request` — this can be asserted by a
unit test enumerating the node's bound tools, not just by reading the system prompt.

**Validates: §3 Invariant 7, §4 Scenario "DATA_SHAPE root cause routes to the existing surgical-PR loop" and "remediation loop's tool surface excludes merge capability"**

### Property 3: no failure mode is fabricated outside GC-11's existing 4

*For any* watchdog signal, a surgical PR is opened if and only if `root_cause_class ==
DATA_SHAPE` AND the root cause matches one of self-healing-pipelines.md's 4 existing modes.
Every other signal (`DATA_SHAPE` with no match, or `JOB_RUNTIME`) produces no PR, no DDL, no
remediation attempt beyond retry/escalate/alert.

**Validates: §3 Invariant 4 + 9, §4 Scenarios "DATA_SHAPE... falls back to alert-only" and
"JOB_RUNTIME root cause never gets a fabricated surgical PR"**

### Property 4: every emitted signal is visible on both live surfaces

*For any* PipelineHealthSignal successfully emitted, a corresponding row exists in BOTH the
old `NOTIFICATIONS_TABLE` (Slack-visible) and `NotificationInbox` (webapp-visible) — never
in exactly one.

**Validates: §3 Invariant 1, §4 Scenario "dbt job failure detected... visible on BOTH surfaces"**

### Property 5: rate-limiting on one workspace never blocks another

*For any* two workspaces A and B with independent source credentials, a 429/backoff event on
A's poll does not delay, skip, or fail B's poll in the same cycle.

**Validates: §3 Invariant 10, §4 Scenario "rate-limited source backs off instead of hammering"**

### Property 6: sub-hourly sources never silently default to nightshift cadence

*For any* signal source whose minimum useful polling interval is sub-hourly, its actual
scheduled interval is NOT one of `cadenceToCron()`'s DAILY..QUARTERLY values — a code review
or config audit can show which explicit path (extended cadence enum, or scoped EventBridge
rule) was chosen.

**Validates: §3 Invariant 12, §4 Scenario "a sub-hourly signal source does not silently ride
the nightshift cadence"**

### Property 7: diagnosis text never reaches a sink unscrubbed for credential shapes

*For any* PipelineHealthSignal whose diagnosis field is delivered to Slack, NotificationInbox,
or a GitHub PR body, `scrub_text()` has run on that text first. (Scoped narrowly per Invariant
13 — this property covers credential/secret shapes only, not customer PII/data-value content.)

**Validates: §3 Invariant 13, §4 Scenario "diagnosis text is scrubbed before reaching any sink"**

### Property 8: get_pipeline_health cannot leak cross-workspace data

*For any* two workspaces A and B, a principal authenticated for A cannot obtain B's
PipelineHealthSignals through `get_pipeline_health`, regardless of request contents — because
the tool has no `workspace_id` parameter to manipulate in the first place.

**Validates: §3 Invariant 14, §4 Scenario "get_pipeline_health cannot be spoofed to read
another workspace's signals"**

## 8. Eval Criteria

| Evaluator | Node | Mode | Threshold | Method |
|---|---|---|---|---|
| FailureClassificationEvaluator | watchdog capability node | GATE | accuracy >= 0.9 vs. labeled fixture set (dbt/Databricks/ETL failure logs) | LLM judge + deterministic (exact stage-enum match) |
| RootCauseClassEvaluator | watchdog capability node (classifies DATA_SHAPE vs JOB_RUNTIME) | GATE | precision >= 0.95 on DATA_SHAPE (false positives here risk a fabricated/misrouted surgical PR — costlier than a false negative, which only downgrades to alert-only) | LLM judge + deterministic (data-shape signals must have a SQL-diagnosable signature) |
| RemediationScopeEvaluator | self-healing surgical-PR loop | GATE | diff scoped to failure only (0 unrelated file changes) | deterministic (diff analysis) |

**Corrected pass 32 — same false-mirroring pattern pass 30 found for §9/GC-12**:
`RemediationScopeEvaluator` does NOT exist anywhere today, and self-healing-pipelines.md
(GC-11) has NO §8 Eval Criteria section at all to share one FROM — `test_gc_11_self_healing.py`
is a pure `pytest.skip()` stub (GAP-7, no code, no ticket). This is NEW scope this spec
introduces, not a reuse. Since GC-11's own Gherkin already asserts "the diff is scoped to the
failure" in prose without a deterministic check backing it, **this evaluator should be added
to self-healing-pipelines.md's own (currently nonexistent) §8 too**, not left as a
disconnected duplicate — BH-1047 (which already wires this spec's signals into GC-11's loop)
is the natural place to build it once, for both specs' benefit.

**CRITICAL, pass 19 (triple-click-zoom) — this table's "GATE" and "LLM judge + deterministic"
terminology, verified against the REAL eval framework (`brightbot/brightbot/evals/`), does
NOT map cleanly onto it. Four real gaps found, none of which invalidate building these
evaluators, but all of which need resolving before implementation, not left implicit:**

1. **No single real `Evaluator` base class exists — two DIFFERENT real shapes, and it's
   ambiguous which this table's evaluators should implement.** `evals/core/contracts.py`
   defines `OutputGate` (`:191-205`: `name`, `mode: GateMode`, `check(...) -> GateVerdict`)
   — this is the ONLY place `GateMode.GATE`/`GateMode.OBSERVE` (`:163-167`) literally exist,
   matching this table's "Mode" column. But the three real concrete evaluators in this repo
   (`SurfaceEvaluator` layers/surface.py:72, `OfflineRoutingEvaluator` layers/routing.py:53,
   `BehaviorEvaluator` layers/behavior.py:28) use a DIFFERENT shape entirely:
   `evaluate(case: EvalCase) -> EvalVerdict`, no `mode` field at all. Since
   `FailureClassificationEvaluator`/`RootCauseClassEvaluator` live inside a watchdog
   CAPABILITY NODE (not the online-gate middleware layer `OutputGate` serves), BH-1042's
   implementer MUST decide explicitly which real Protocol these implement — do not assume
   "GATE" in this table's Mode column means it automatically gets `OutputGate`'s real
   enforcement machinery; it may not fit that layer at all.
2. **"LLM judge + deterministic" in ONE evaluator has NO real extension point to plug
   into — AND the cited precedent is NOT actually an LLM-judge/deterministic hybrid,
   CORRECTED pass 30.** Every real evaluator in this codebase is purely one or the other:
   `SurfaceEvaluator` is pure deterministic keyword scoring; `core/metrics.py:33,38` wrap
   DeepEval's pure-LLM-judge `GEval`/`AnswerRelevancyMetric`. `record_capability_execution`
   (`quality_check_agent.py:1442-1512`), previously cited as "the closest real precedent for
   blending both," is actually neither — verified its EXACT formula, not paraphrased:
   ```python
   cfg_total = len(configured_rule_results)
   cfg_passed = sum(1 for r in configured_rule_results if r["passed"])
   ai_total = ai_stats.get("evaluated_expectations", 0)
   ai_passed = ai_stats.get("success_count", 0)
   total_checks = cfg_total + ai_total
   total_passed = cfg_passed + ai_passed
   combined_score = (total_passed / total_checks) if total_checks else 0
   ```
   Both terms are PASS/FAIL COUNTS, not an LLM judgment score blended with a deterministic
   one — `ai_stats` comes from an LLM (`quality_model`) GENERATING candidate expectations
   (via `generate_expectations`), which are THEN evaluated deterministically against real
   data (GX/pandas/SQL), producing `success_count`/`failure_count` — the same shape as the
   configured-rule counts. No LLM ever assigns a judgment score here; this is a pooled
   pass-rate over two SOURCES of deterministic checks (human-configured rules + LLM-proposed
   rules), not a hybrid scoring mechanism. It's also UNCONDITIONAL/additive (both terms
   always summed, either can legitimately be 0, `combined_score` defaults to 0 if
   `total_checks == 0`) and carries NO threshold anywhere in the function — it's stored as a
   raw score (`result_data["score"]`, line 1485) with no pass/fail cutoff applied. BH-1042's
   implementer should NOT model `FailureClassificationEvaluator`/`RootCauseClassEvaluator`
   on this precedent for an "LLM judge + deterministic" pattern, because this precedent
   doesn't contain an LLM judge at all — if a genuine LLM-judged score is needed (e.g. the
   LLM itself rates confidence in a classification, not just proposes checks later verified
   deterministically), that combination pattern has NO real precedent anywhere in this
   codebase and must be designed fresh, with an explicit threshold decision this precedent
   also never had to make.
3. **GATE mode is a real, TESTED mechanism that enforces NOTHING in production today.**
   `run_gate_with_heal` (`online/gates.py:56-134`) implements the real retry/heal loop and
   checks `GateMode.GATE` (`gates.py:100`) — but confirmed by grep: no middleware, CI
   workflow, or agent node anywhere calls `run_gate_with_heal`/`OutputGate` outside its own
   unit test (`tests/unit/evals/test_eval_framework_contracts.py`). Labeling these
   evaluators "GATE" in this table does NOT mean anything is currently blocked by them —
   BH-1042/1054 must decide whether to (a) wire into the real `run_gate_with_heal` mechanism
   (giving it its FIRST real production caller), or (b) implement gate-like blocking
   directly inside the watchdog node without that shared machinery. Do not assume "GATE" is
   self-enforcing just because the framework has a type named that.
4. **The labeled fixture set `FailureClassificationEvaluator` needs does not exist —
   confirmed by search, zero dbt/Databricks/ETL failure-log fixtures anywhere in the repo.**
   This is new scope for BH-1042/1054's implementer to build from scratch (labeled failure
   logs across the 6 stage taxonomy values), not an existing corpus to point the evaluator
   at.

**Model tier (verified pass 22, cost estimate)**: use **Haiku** (`claude-haiku-4-5` via Bedrock)
for `FailureClassificationEvaluator` and `RootCauseClassEvaluator` — both are bounded-enum
outputs, not open-ended generation, and this matches GC-12's own precedent
(`quality_model = _haiku(max_tokens=64000)`, `governance_agent/models.py:23,48`, **re-verified
pass 33 by direct read — Haiku is the dominant model tier across this whole agent family**,
`metadata_model`/`schema_model`/`governance_react_model` all use it too) rather than
introducing a new pattern. Reserve Sonnet-class models only for the free-text diagnosis
summary feeding the PR body, if a more fluent write-up is worth the ~4x cost delta. Estimated
cost at realistic scale: **$0.12–$80/month** across 2–200 workspaces (cost scales with actual
failure rate, not poll frequency — most hourly polls find nothing and never invoke an LLM).
Not a blocker at any realistic scale. Note: no `cost_usd`/token-budget emission exists near
GC-12 today either (PS-12 gap) — this spec inherits that gap, doesn't introduce it; flag but
don't block on it.

## 9. Observability Contract

**Verified pass 30 against real BrightHive conventions** (not pattern-guessed): the
`gen_ai.tool.execute` span and dotted log-event strings match this repo's SPEC-LEVEL house
style (consistent across other specs' own §9 sections, e.g. SPEC-MCP-AGENT-RUNNER.md,
SPEC-SV-QC-PIPELINE.md). Note this is a DIFFERENT convention from the currently-DEPLOYED
middleware (`otel_instrumentation.py` emits `langgraph.tool.{name}`/`langgraph.node.{name}`) —
this spec deliberately follows the spec-writing house style for a new capability, consistent
with how every other recent spec's §9 is written, not the older deployed-middleware naming.
Metric names below are corrected to DOT-NAMESPACED form, matching real production metrics
(`langgraph.tool.duration_ms`, `eval.test_cases.total`) — the original draft's
snake_case-with-underscores form (`watchdog_poll_duration_ms`) did not match any real
convention in this codebase.

- **Span**: `gen_ai.tool.execute` with `gen_ai.tool.name=pipeline_health_watchdog`
- **Attributes**: `workspace_id`, `source_type` (`dbt`|`databricks`|`etl`), `run_context`,
  `signal.stage`, `signal.severity`, `cooldown.suppressed` (bool)
- **Log events**: `watchdog.poll.started`, `watchdog.poll.success`, `watchdog.poll.source_unreachable`,
  `watchdog.poll.rate_limited` (429/backoff hit, source+workspace skipped for this cycle — see
  Invariant 10), `watchdog.signal.emitted`, `watchdog.signal.suppressed_cooldown`,
  `watchdog.dualwrite.partial` (fired if one of the two writes in Invariant 1 fails — this is
  the specific failure Property 4 guards against and must be alertable on its own),
  `remediation.pr.opened`, `remediation.fallback.alert_only`
- **Metrics** (dot-namespaced, corrected pass 30): `watchdog.poll.duration_ms` (per
  source_type), `watchdog.signals.emitted_total` (per stage), `watchdog.dualwrite.partial_total`
  (per table — Slack-only vs. webapp-only; should be 0 in steady state),
  `watchdog.rate_limited_total` (per source_type, per workspace_id — sustained non-zero on one
  workspace signals that workspace's own polling cadence is too aggressive for its dbt
  Cloud/Databricks plan tier), `remediation.prs_opened_total`, `remediation.fallback_total`

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brightbot` | `brightbot/tests/` + `brightbot/brightbot/evals/` (L0/L1/L2) | L0: one case per §2 MCP tool contract entry, PLUS the required `capabilities.py` catalog row for `get_pipeline_health` and its addition to the live-tool enumeration tests (`test_permissions.py`, `test_tool_invariants.py`/`test_mcp_live_tools.py`-style lists) — these are CI-pinned and fail closed if skipped (verified pass 6). **CRITICAL, added pass 26: `get_pipeline_health` MUST pass the EXISTING repo-wide `test_no_principal_fields_in_tool_args` test (`test_tool_invariants.py`) — this is not optional/new, it's an existing gate the tool must not violate.** L1: routing case confirming watchdog capability node is reachable via the existing dispatcher (not a new entry point). L2: one case per §3 invariant (1, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14) + FailureClassificationEvaluator gated at 0.9 + RootCauseClassEvaluator gated at 0.95 precision on DATA_SHAPE. Invariant 10/11 cases must mock a 429 response from dbt_cloud_tools.py's HTTP calls (which today has zero backoff handling, confirmed by code read — this is new behavior, not existing coverage) and assert per-workspace isolation (Property 5). Invariant 12 case (BH-1051 only): assert the deployed schedule expression is NOT one of cadenceToCron()'s hardcoded DAILY..QUARTERLY 08:00 values. Invariant 13 case: feed a fixture diagnosis string containing a fake credential shape (e.g. a `postgres://user:pass@host` connection string) through the diagnosis pipeline and assert `scrub_text()` redacted it before any sink write (Property 7). **Invariant 7 case, CRITICAL (verified pass 24): enumerate the remediation loop's bound tools at construction time and assert `github_merge_pull_request` is absent — this is a code-level assertion, not a prompt-content check, and this specific test MUST exist before BH-1047 is considered done (Property 2).** **Invariant 14 case, CRITICAL (verified pass 26): construct two fake principals for Workspace A and B, call `get_pipeline_health` as each, assert A never sees B's signals and vice versa — this test MUST exist before BH-1042 is considered done (Property 8).** |
| `brighthive-platform-core` | `brighthive-platform-core/tests/` | Two tests confirming a watchdog-emitted event round-trips through BOTH the old `NOTIFICATIONS_TABLE` (Slack-visible) and `NotificationInbox` (webapp-visible) with zero new delivery code — one test per table, plus one negative test asserting `watchdog.dualwrite.partial_total` fires if either write is mocked to fail (validates Invariant 1 + 6, Property 4). |
| `brighthive-e2e` | `brighthive-e2e/e2e/` | One feature test: real dbt Cloud sandbox job failure → real staging watchdog poll → real Slack/in-app alert, end-to-end (§4 happy path). One error-path test: SQL Server disk-low scenario against a real staging BYOW SQL Server connection (§4 "SQL Server disk monitoring" scenario) — this is the literal demo scenario and must be proven against a real backend per `test-behavior-real.md`, not mocked. |

**Real-behavior requirement**: the SQL-Server disk-monitoring e2e case is non-negotiable —
it is the direct rebuttal to Frank's stated disbelief and must be demonstrated against a real
connected SQL Server, not a construct/mock.

**CRITICAL, verified 2026-07-10 (pass 14) — both real-behavior fixtures this table assumes
DO NOT EXIST TODAY, and neither was previously tracked as a known gap:**
- **No staging BYOW SQL Server connection exists anywhere** (confirmed by direct search —
  `e2e/fixtures/ground_truth.py` has zero SQL Server entries, zero `sql-server` infra-gap
  tracking slug existed before this pass). The literal 7/17 demo commitment (Suzanne's line
  item #2, disk-monitoring at 20% remaining) currently has NO real infrastructure to run
  against. **BH-1057 filed, urgent** — provisioning this is now the single most
  demo-time-critical open item across all 14 verification passes.
- **No dbt Cloud job exists that can be deliberately triggered to fail** (the one real project,
  395091, is treated as healthy/read-only). **BH-1058 filed** — less time-critical than
  BH-1057 since dbt job-status monitoring isn't Frank's literal named example, but still
  required for BH-1043's §10 case to be executable as written.

Before opening the implementation PR: run all suites above, confirm every new §2/§3/§4/§8 entry
has a corresponding test case, confirm all green. **Confirm BH-1057 and BH-1058 are resolved
first** — a §10 test case that names a fixture which doesn't exist is not a test plan, it's a
placeholder.

## Areas Involved

| Area | Repo | Impact |
|---|---|---|
| Watchdog capability node (dbt/Databricks/ETL job-status polling) | `brightbot` | New capability node in `governance_agent/sub_agents/` (sibling to `longitudinal_node.py`, NOT inside `dbt_agent` — that's the tool surface it polls, resolved pass 7), riding existing dispatcher |
| BrightSignals dual-write (interim) + eventual unification | `brighthive-platform-core` | Watchdog writes to both old table + NotificationInbox directly now; migrates to BH-1053's unified entrypoint once shipped (non-blocking) |
| Surgical-PR remediation wiring | `brightbot` | Extend self-healing-pipelines.md's loop to accept watchdog-sourced triggers |
| MCP read path (`get_pipeline_health`) | `brightbot` (MCP server) | New tool, mirrors `get_anomalies` |
| SQL Server disk/job query | `brightbot` (via existing WarehousePort adapter) | New T-SQL health-check queries through existing connection — no new adapter type |
| Airbyte source-sync watchdog (BH-1049) | `brightbot` (if Option B, poller) OR **`brighthive-platform-core`** (if Option A, extending `airbyte_notification_webhook`'s no-op failure branch) | **CORRECTED pass 13**: NOT brightbot-only as originally scoped — Option A (cheaper, reuses existing auth/connection-mapping code) lives in platform-core's existing webhook Lambda, not a new brightbot poller |

## Ticket Breakdown

Already created in Jira 2026-07-10 and revised in this pass to match this spec (epic BH-1036
unless noted):

| Ticket | Summary | Status |
|---|---|---|
| BH-1053 | Decision: resolve BrightSignals' 3-way split-brain into a unified write entrypoint | Needs Refinement, non-blocking (watchdog dual-writes in the interim, per Invariant 6) |
| BH-1042 | spec: watchdog capability-node contract (dbt/Databricks/ETL job-status) | Needs Refinement, revised to match this spec |
| BH-1054 | feat: watchdog poller — the actual missing proactivity primitive | Needs Refinement, revised to ride existing dispatcher |
| BH-1043 | feat: dbt job/run health poller | Needs Refinement |
| BH-1044 | feat: Databricks job/cluster health adapter | Needs Refinement |
| BH-1045 | feat: generic ETL / SQL-Server disk-via-existing-connection adapter | Needs Refinement, revised — tier-1 answer to Frank's objection |
| BH-1046 | feat: verify watchdog events reach existing delivery (not new delivery code) | Needs Refinement, revised down to verification-only |
| BH-1047 | feat: wire watchdog failures into self-healing-pipelines.md's surgical-PR loop | Needs Refinement, revised to extend GC-11 rather than compete |
| BH-1048 | spec: ingestion signal contract — **CORRECTED pass 31**: "reuses an existing delivery path" was FALSE (the EventBridge→notification_dispatcher chain is undeployed); must choose between deploying that missing infra or routing through the CONFIRMED-real BrightSignals dual-write directly | Needs Refinement, revised pass 31 — real open decision, not settled (BH-1037) |
| BH-1049 | feat: Airbyte/source-sync watchdog — greenfield IN BRIGHTBOT (pass 5) but a cheaper push-based path exists in platform-core's existing airbyte_notification_webhook (pass 13) | Needs Refinement, revised pass 13 — must evaluate extending the existing reactive webhook's no-op failure branch before defaulting to a new poller |
| BH-1050 | feat: batch (Step Functions) watchdog — greenfield for a POLLING approach (pass 5), but a cheaper PUSH option exists (pass 22): extend the LIVE `data_ingestion_stack.py:844-853` EventBridge rule that already routes Step Functions FAILED executions to Slack, same class of fix as BH-1049's Airbyte webhook | Needs Refinement, revised pass 22 — must evaluate extending the existing rule before defaulting to a new poller |
| BH-1051 | feat: event/streaming (queue lag, DLQ) watchdog — requires an explicit sub-hourly scheduling decision (Invariant 12); cadenceToCron caps at daily | Needs Refinement, revised — scheduling gap flagged pass 5 |
| BH-1052 | feat: unify all 3 ingestion watchdogs into the same dual-write/dedup as BH-1054 — **CORRECTED pass 25**: not pure verification if BH-1049/1050 choose Option A, since each lives in a different repo/runtime/mechanism (brightbot direct call, a Chalice Lambda's new HTTP call, an existing SNS→Slack-only path that may not reach NotificationInbox at all) | Needs Refinement (BH-1037), revised pass 25 — real conditional design work, not pure verification |
| BH-1038–1041 | BrightRoutines MCP/A2A surface (BH-115) | Needs Refinement, unaffected by this spec — separate concern |
| BH-1055 | infra: concurrency cap + fan-out load test for scheduled_agent_dispatcher | Needs Refinement, filed pass 11, sharpened with live AWS data pass 12-13 (BH-1036 for now; conceptually fits BH-171) |
| BH-1057 | infra/fixture: provision staging BYOW SQL Server connection — the literal 7/17 demo scenario has zero infra today | Needs Refinement, filed pass 14 (CRITICAL), resolved-actionable with concrete runbook pass 15 (BH-1036) |
| BH-1058 | infra/fixture: dbt Cloud job with deliberate-failure capability, for BH-1043's e2e case | Needs Refinement, filed pass 14, resolved-actionable pass 16, CORRECTED pass 27 — runbook's fixture mechanism must produce a genuine runtime SQL error, not a compile-time error (BH-1036) |
| BH-1059 | track: scheduled_agent_dispatcher's LangGraph Cloud dependency unaddressed by AgentCore/CEMAF migration | Needs Refinement, filed pass 19, tracking placeholder (BH-453, correct epic home) |
| BH-1060 | security: evaluate customer PII/data-value redaction for diagnosis text (scrub_text() covers secrets only) | Needs Refinement, filed pass 23, non-blocking for 7/17, decision-before-production (BH-1036) |
| BH-1067 | feat: renderers for 5 new watchdog notification stages (Slack + webapp) — dbt_run_stale, databricks_job_failure, databricks_cluster_unhealthy, etl_job_failure, source_disk_low | Filed pass 35 — CRITICAL for demo-visibility, blocks BH-1043/1044/1045's alerts from being human-visible (BH-1036) |
| BH-1071 | docs: NOTIFICATION_SYSTEM_PLAN.md is stale — 4+ claims describe undeployed/never-built infra as current | Filed pass 32 — non-blocking for 7/17, blocked by BH-1053's real-vs-retire decision (BH-1036) |

## Related

- **Sibling spec (precedent)**: `longitudinal-monitoring.md` — the scheduling/dispatcher pattern this spec reuses
- **Sibling spec (precedent)**: `longitudinal-monitoring-capability.md` — interface contract detail for the capability-node pattern
- **Downstream consumer**: `self-healing-pipelines.md` — the surgical-PR loop this spec's signals feed into
- **Memory — originating context**: `project_loop_capital_sales_gate.md`, `project_loop_capital_engineering_response.md`
- **Memory — full pass-by-pass verification log (29 passes and counting)**:
  `project_loop_capital_pass_index.md` — one-line summary per pass with pointers to each
  pass's own detail file. Compacted here (was an inline 27-entry list through pass 27; kept
  growing past the point of being skimmable) — read the index file, not this section, for the
  full chronology. Two CRITICAL/P0 findings to know about without opening anything else:
  pass 25 (auto-merge had no code-level lock) and pass 27 (an MCP tool this spec itself drafted
  had a cross-tenant spoofing hole) — both fixed, both need their required tests before their
  owning tickets (BH-1047, BH-1042) are done.
