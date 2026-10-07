---
title: "Executable pilot journeys through MCP"
epic: "BH-1255"
author: "drchinca"
status: Partial
roadmap: "THEME-spec-driven-pipelines.md; implementation ledger in section 6; client acceptance pending"
created: "2026-10-07"
generates: "tickets"
tags: [mcp, pilots, monitoring, workflows, governance]
related:
  specs: [THEME-spec-driven-pipelines.md, THEME-honest-surfaces.md, THEME-governance-enforced.md, THEME-routine-delivery.md]
  features: [mcp-user-journeys.md]
  pocs: []
  bedrock: []
---

# Executable pilot journeys through MCP

## 1. Context

Make the Longaeva and Loop Capital journeys executable from the platform's curated
MCP surface. The October 7 demo-workspace audit found skipped profiling reported as
success, a quality schedule targeting a missing asset, an errored workflow, and no
watchdog schedule. MCP transport passed its separate reliability gate. These facts
do not establish client acceptance. This implementation follows the user's explicit
request to deliver the five journeys, using existing platform contracts and stores.

### Existing implementation

- Project MCP tools already create projects, store specs, propose/apply steps, compile,
  validate, run, and read WorkflowRun/StepRun results through Platform Core.
- Quality tools discover/profile tables, generate expectations and execute library rules.
- Scheduled agents persist in DynamoDB and dispatch through the existing scheduler.
- Remediation excludes self-merge; reviewed repair and Slack approval need separate proof.
- Governance declarations and observability reads exist; an edge or badge alone is not
  proof that the relevant operation was denied.

### Acceptance boundaries

| Journey | Required result | Pilot scope |
|---|---|---|
| Spec to product | Persisted spec and pipeline, terminal run, checked outputs and PR evidence | Longaeva S3/REST/share scaffolds, Atlas enrollment and downstream MCP; Loop governed SQL target |
| Warehouse to quality | Real profiles/checks, history, recurring monitor, delivered alert | Longaeva four anomaly families; Loop SQL Server jobs/disk and quality SQL |
| Failure to repair | Diagnosis, surgical PR, independent approval, rerun and output verification | Longaeva four failure modes; Loop SQL Server/SSIS and Slack approval |
| Recurring automation | Proposal, approval, persisted schedule, execution and delivery result | Longaeva monitoring/Slack; Loop criterion 9 |
| Governance enforcement | Denied operation plus readable decision/audit evidence | Loop criterion 8; broader Longaeva governance is bonus |

Longaeva's internal MCP is a distinct endpoint from BrightHive's MCP. SQL Server
stand-ins and the demo warehouse are not evidence against Loop Capital's actual server.
No passing client verdict is inferred from unit tests or empty baseline fixtures.

## 2. Interface contract

Reuse WorkflowSpec, WorkflowRun/StepRun, Platform Core quality/routine mutations,
scheduled-agent routes and their stores. Extend curated MCP with typed domain inputs
only where a necessary operation has no dedicated tool. Workspace, bearer and acting
identity always come from the authenticated principal.

Existing MCP envelopes remain `ok | error | preview | pending | not_found`.
An accepted asynchronous operation returns its persisted identifier for read-back;
`ok` acknowledges the operation, not successful completion of the work.

### Mutation retry contract

New quality/schedule creation tools require an `idempotency_key` on confirmation.
`MutationStore` is a port with atomic `claim(key, fingerprint)` and
`complete(key, owner_token, result_json)` operations. Its registry initially selects
Redis; tests inject a deterministic fake with failure injection. Records are scoped
by workspace, actor and operation. Completed results are retained at least 24 hours. Matching completed
requests replay their result; different payloads conflict; pending requests do not
execute again. An unknown write outcome remains pending without expiry or automatic
takeover until reconciliation. Redis must use durable persistence and no eviction
for these records; deduplication cannot survive loss of the shared records. Missing
or unavailable shared storage fails before a new mutation; no local fallback.
Confirmed saves stay disabled until `BH_MCP_MUTATION_STORE_READY=true` and the selected
store is configured and verified. Redis requires a dedicated `BH_MCP_MUTATION_REDIS_URL`
after persistence, non-eviction and recovery checks. Previews remain available.
Mutations disable transport-level POST retries;
a single reservation must never wrap multiple ambiguous downstream attempts.

DynamoDB is the durable deployment option behind the same registry-backed port:
atomic conditional reservation, strongly consistent replay reads, owner-checked
completion, no TTL on pending records and a TTL of at least 24 hours on completed
records. Select `BH_MCP_MUTATION_STORE=dynamodb` with an explicitly provisioned
`BH_MCP_MUTATION_TABLE_NAME`; the readiness gate still defaults off. The owning
infrastructure must configure encryption, point-in-time recovery and retention on
deletion, and grant the runtime only the required item operations on that table.
No existing scheduler or cache table is repurposed. Use one regional writer; active-active
Global Tables do not satisfy this claim contract. Completed results have a configurable
UTF-8 byte budget, bounded below DynamoDB's item limit. SDK write retries are disabled;
ambiguous reservations fail closed. Test the adapter with an AWS fake and validate the
real table configuration before enabling confirmed writes.

### Schedule outcome contract

The existing `schedule_pipeline_run` tool adopts the shared retry contract too:
confirmation requires a key; current scope and platform authorization run before
claim or replay; the fingerprint covers normalized cron and every execution input.
No process-local fallback or GET/create/SET race is permitted. The worker owns its
storage client and in-process scheduler operation through completion, even if the
caller times out. A partial schedule write returns pending and cannot be retried
with a new reservation automatically. Execute-workflow owner authorization remains
required at dispatch time. This does not enable service-context quality/profiler runs.

Ship the existing scheduler's authorization correction first: require the current
`RUN/PIPELINE` ALLOW before replay and include actor identity in cache keys. This
narrow correction does not make the existing best-effort cache atomic or durable.
Its new actor-scoped namespace does not read legacy entries. Before rolling that
slice out while scheduling writes are enabled, pause new scheduling confirmations
and drain the configured old result-cache retention window; otherwise an in-flight
retry can create a second schedule. This limitation remains until atomic reservations
replace the cache. Permission lookup failure blocks confirmations and replays even
when the general client-side authorization shadow flag is disabled.
Before moving creation to workers, replace the route's shared boto3 resource with
worker-owned infrastructure and bound admission/deadlines. Reject local-only storage
and missing dispatcher/role configuration instead of caching an unregistered schedule.

Persist and expose `last_run_status="skipped"` when a completed graph reports
`flag_skipped=true`. A transport/graph failure takes precedence over the skip flag.
Preserve the graph's skip reason in `last_run_message`. An enabled skipped schedule
appears as a fleet concern with a configuration-review action, never a successful check.
Existing success/error/running statuses retain their meanings. Older persisted rows
are not silently rewritten based on message text.

### Evidence contract

For each acceptance run record: journey/criterion, environment, workspace reference,
deployed revisions, timestamp, operation/run identifiers, terminal outcome, output
checks, PR/approval/alert references and limitations. Exclude credentials and raw
customer data. A missing required dependency is `blocked`; an unexecuted case is
`not_verified`; neither counts as a pass.

## 3. Invariants

1. No in-process workflow state or retry deduplication is authoritative across replicas.
2. Preview performs no writes. Confirmed writes require MCP scope and the owning
   platform's authorization; confirmation is not a substitute for human PR approval.
3. Existing owner/admin and tenant checks apply through every MCP adapter.
4. Failed, skipped, blocked and running operations cannot be counted as completed work.
5. Required unsupported runtime operations fail explicitly instead of returning fake runs.
6. Repair agents cannot grant their own approval or merge their own changes.
7. Each client acceptance verdict references evidence on its agreed environment.
8. Retried mutations use shared idempotency protection; keys include tenant identity.
9. No production writes or promotion without explicit production approval.

## 4. Acceptance criteria

### AC-PILOT-01 Truthful scheduled outcomes

Given a scheduled profiler finishes with `flag_skipped=true`, when its completion
callback is processed, then its outcome is skipped, its reason survives, and fleet
health reports an enabled monitor that did no work. A failure remains a failure even
when the payload also contains a skip flag.

### AC-PILOT-02 Specification to verified output

Given an authorized workspace and usable target, when an MCP client creates a project,
stores a spec, reviews/applies the proposal, compiles, validates and runs, then it can
read a terminal run and independently check the produced output. Missing runtime
support yields a typed failure; it never yields an indefinitely running invented job.

### AC-PILOT-03 Recurring quality coverage

Given a catalogued asset and authorized caller, when the caller configures a quality
check and its schedule through MCP, then actual results and execution history can be
read back and a controlled failure reaches its configured notification destination.

### AC-PILOT-04 Reviewed remediation

Given a supported failure, when the monitor detects it without a prompt, then the
platform records a diagnosis and scoped PR, waits for an independent authorized human,
and records rerun/output evidence. Loop's case additionally proves Slack approval.

### AC-PILOT-05 Managed recurring work

Given an offered routine, when its owner approves/configures it through MCP, then the
persisted schedule runs and records delivery. Pausing prevents later execution, and
duplicate confirmation does not create a duplicate schedule.

### AC-PILOT-06 Enforced governance

Given a declared blocking rule, when a violating operation is attempted through MCP,
then the owning platform denies it and exposes the decision. An enforcement-service
failure fails closed. A forbidden tenant or acting identity cannot bypass this check.

## 5. Out of scope

New workflow engine, separate scheduler, new customer UI, fabricated client acceptance,
production promotion, and new engine integrations outside the selected pilot paths.

## 6. Dependencies and delivery sequence

Each implementation slice stays independently reviewable under the workspace PR limits.

1. Correct scheduled outcome classification and fleet visibility.
2. Expose missing quality/scheduling/routine operations through existing owner contracts.
3. Complete required runtime dispatch/polling and verify the project journey.
4. Connect reviewed remediation and its human approval surface.
5. Verify enforcement and end-to-end journey evidence in brighthive-e2e.

### Implementation ledger — October 7

These are code/review results, not deployed or client acceptance results.
The user approved BrightBot #1121, this spec's PM #199 and then the quality lifecycle
batch #1122–#1126. All are merged into their target branches. Live staging verification
is deferred at the user's request while implementation continues. New implementation
PRs require their own merge authorization under the workspace contract.

| Slice | PR | Local evidence | Rollout state |
|---|---|---|---|
| Skipped monitoring outcomes | [BrightBot #1121](https://github.com/brighthive/brightbot/pull/1121) | 47 tests | Merged staging; verification deferred |
| Executable generated expectations | [BrightBot #1122](https://github.com/brighthive/brightbot/pull/1122) | 19 tests; JSON/persistence mapping | Merged staging |
| Shared retry store | [BrightBot #1123](https://github.com/brighthive/brightbot/pull/1123) | 11 tests, including real local Redis concurrency | Merged staging |
| Save one DRAFT rule | [BrightBot #1124](https://github.com/brighthive/brightbot/pull/1124) | 45 tests, including MCP invariants | Merged staging; confirmed writes default off |
| Rule inventory and recent executions | [BrightBot #1125](https://github.com/brighthive/brightbot/pull/1125) | 28 tests, including denied reads and paging | Merged staging |
| Activate/deactivate/deprecate | [BrightBot #1126](https://github.com/brighthive/brightbot/pull/1126) | 48 tests; actual transitions/readback/retry coverage | Merged staging; confirmed writes default off |
| Explicit notification destination | [BrightBot #1127](https://github.com/brighthive/brightbot/pull/1127) | 33 tests | Merged staging |
| Durable mutation adapter | [BrightBot #1128](https://github.com/brighthive/brightbot/pull/1128) | 18 tests, including Moto/Stubber and local Redis | Merged staging; writes not enabled |
| Dedicated regional storage | [Platform Core #1322](https://github.com/brighthive/brighthive-platform-core/pull/1322) | 2 synthesis/entry-point tests; isolated synth | Merged staging; isolated stack deployed |
| Scheduler replay authorization | [BrightBot #1129](https://github.com/brighthive/brightbot/pull/1129) | 49 scheduler/invariant tests; four-role review | Open; merge not yet authorized |

The complete quality batch passed 84 combined local tests after integration. Its
staging merge is `17d2ea279bd3b36d60735623aa0e777813df4213`; PM #199 merged to master
as `b750a2416d3927c1ead976c3cb73e7e4ec7153e0`. These are repository revisions, not
proof of the running deployment revision.

Each slice completed architect, senior Python, QA and junior review. Test counts
overlap and must not be added into an aggregate. Inventory pages currently fetch
all matching rules from Core; histories contain at most ten recent executions per
rule, across assets. Cached mutation replies describe their original operation;
inventory reads establish current state. Never reconcile uncertain creations by
fuzzy matching names/parameters or by changing the idempotency key.

### Durable storage rollout

The user approved #1127, #1128, Core #1322 and PM #200 plus the isolated staging
storage deployment. On October 7, `Staging-BPC-McpMutationStoreStack` reached
`CREATE_COMPLETE` in staging/us-east-1. Its table `brightbot-mcp-mutations-staging`
is ACTIVE with the String `mutation_key` partition key, on-demand capacity,
encryption, point-in-time recovery, `expires_at` TTL and deletion protection enabled.
The attached `brightagent-aws` inline policy grants only GetItem/PutItem/UpdateItem
on that table. These are deployment/configuration reads, not MCP journey validation.

Core merge: `f425065fafd341e480c062bf24a29b6e7fb5d0b9`. BrightBot #1128 merge:
`91dcfa728a2507617f96b56936823a49c126eeb1`; #1127 merge:
`99d7d2effef8c68b4710a937f99116e9c6f8ace5`. CloudFormation change set
`awscli-cloudformation-package-deploy-1791347750` added exactly the table and policy.
No runtime environment was changed to enable confirmed writes; no item claims,
quality writes or live journey suite were run. Runtime credential binding,
cross-instance behavior and readiness enablement remain pending.

1. Merge the reviewed adapter and isolated infrastructure PRs after authorization. **Done.**
2. From Platform Core, synthesize `mcp_mutation_store_app.py` with `ENV=Staging`,
   the staging AWS profile and its actual account. Review the isolated
   `Staging-BPC-McpMutationStoreStack` change set: one table, one IAM policy. **Done.**
3. Deploy only this stack with `RuntimeUserName` set to the confirmed existing
   BrightBot runtime IAM user. The documented staging user exists; its actual
   deployment credential binding still needs verification. Do not create credentials.
   **Stack deployed; actual runtime identity verification remains pending.**
4. Check the deployed table's key, encryption, PITR, TTL, deletion protection and
   runtime item permissions; prove competing claims and replay across instances.
5. Configure `BH_MCP_MUTATION_STORE=dynamodb`, the output table name as
   `BH_MCP_MUTATION_TABLE_NAME`, and its `AWS_REGION`. Set readiness true only after
   those checks. Keep completed retention at least 86400 seconds.
6. Verify quality save/inventory/activation through MCP. Record exact operation IDs,
   deployed revisions and results in the evidence harness. Client acceptance remains
   separate from the demo workspace check.

Rollback disables readiness first and retains the table/records. Do not repoint
clients to an empty store or erase pending reservations; reconcile unknown writes
from authoritative operation evidence. Code rollback must preserve the same records
if confirmed mutations remain enabled. This runbook does not authorize production.

Before enabling monitor creation, address execution authorization for scheduled
quality/profiler work (currently service context; owner reauthorization is wired
for execute_workflow only). BrightBot #1127 prevents new implicit Slack DM subscriptions
when an explicit sink_config is supplied. Existing notification subscriptions remain;
an INBOX setting alone does not establish inbox-only delivery. Existing async schedule routes contain
blocking AWS calls; a worker must retain its resources after caller timeout.

Still required: monitor creation/control and delivered alerts; real terminal
pipeline/output evidence and runtime gaps; durable reviewed repair/Slack approval;
observable governance denial; client-specific acceptance evidence. BrightAgent in
the BrightHive Slack workspace is the requested test destination; exact routing
remains to be resolved before messaging. The user designated **@Kuri Chinca** as
the human reviewer; resolve that Slack identity within the BrightHive workspace.

Client infrastructure access, downstream MCP access, designated Slack test channel and
reviewer identity are required for the corresponding client proofs. Record unresolved
dependencies without changing client commercial status. No team messages are sent as
part of implementation; notification tests use an explicitly designated test channel.

## 7. Correctness properties

- Across replicas, a retry must preserve mutation identity and authorization.
- Terminal error takes precedence over skipped; skipped takes precedence over success.
- No agent can convert its own pending repair into an approved repair.

## 9. Observability contract

Use existing persisted run, schedule and governance records. Include workspace and
correlation identifiers in operation logs; redact credentials and customer values.
Expose actionable reasons when a required operation cannot execute.

## 10. Test coverage update

- BrightBot: deterministic completion parser and fleet summary regression tests;
  fake collaborators for MCP preview, denial, tenant scope and operation dispatch.
- Platform Core: targeted adapter dispatch/polling and authorization tests where changed.
- brighthive-e2e: one AC per journey test, ground-truth fixtures, explicit writes and
  cleanup, persisted run polling and output assertions. Required skipped cases prevent
  declaring the entire journey verified even if the surrounding smoke suite is green.
- Validate local changes before staging promotion; record deployed revision on live runs.

## Related

- [Longaeva acceptance scorecard](../../clients/trials/longaeva/scorecard.md)
- [Loop Capital client scope](../../clients/trials/loopcapital/artifacts/2026-07-client-docs-trial-scope-and-demo.md)
- [MCP tool journeys](../features/mcp-user-journeys.md)
- [Honest monitoring surfaces](THEME-honest-surfaces.md)
