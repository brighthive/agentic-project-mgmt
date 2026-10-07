---
title: "Executable pilot journeys through MCP"
epic: "BH-1255"
author: "drchinca"
status: "In Progress"
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
Confirmed saves stay disabled until `BH_MCP_MUTATION_STORE_READY=true` and a dedicated
`BH_MCP_MUTATION_REDIS_URL` are configured after persistence, non-eviction and recovery
checks. Previews remain available. Mutations disable transport-level POST retries;
a single reservation must never wrap multiple ambiguous downstream attempts.

### Schedule outcome contract

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
The user approved BrightBot #1121 and this spec's PM #199 for merge, and then
requested more implementation before staging verification. New implementation
PRs require their own merge authorization under the workspace contract.

| Slice | PR | Local evidence | Rollout state |
|---|---|---|---|
| Skipped monitoring outcomes | [BrightBot #1121](https://github.com/brighthive/brightbot/pull/1121) | 47 tests | Merge authorized; verification deferred |
| Executable generated expectations | [BrightBot #1122](https://github.com/brighthive/brightbot/pull/1122) | 19 tests; JSON/persistence mapping | Open against staging |
| Shared retry store | [BrightBot #1123](https://github.com/brighthive/brightbot/pull/1123) | 11 tests, including real local Redis concurrency | Open against staging |
| Save one DRAFT rule | [BrightBot #1124](https://github.com/brighthive/brightbot/pull/1124) | 45 tests, including MCP invariants | Stacked on #1123; confirmed writes default off |
| Rule inventory and recent executions | [BrightBot #1125](https://github.com/brighthive/brightbot/pull/1125) | 28 tests, including denied reads and paging | Open against staging |
| Activate/deactivate/deprecate | [BrightBot #1126](https://github.com/brighthive/brightbot/pull/1126) | 48 tests; actual transitions/readback/retry coverage | Stacked on #1124; confirmed writes default off |

Each slice completed architect, senior Python, QA and junior review. Test counts
overlap and must not be added into an aggregate. Inventory pages currently fetch
all matching rules from Core; histories contain at most ten recent executions per
rule, across assets. Cached mutation replies describe their original operation;
inventory reads establish current state. Never reconcile uncertain creations by
fuzzy matching names/parameters or by changing the idempotency key.

Before enabling monitor creation, address execution authorization for scheduled
quality/profiler work (currently service context; owner reauthorization is wired
for execute_workflow only). Schedule creation also automatically creates a Slack
DM subscription independently of explicit sink_config; an INBOX setting alone
does not establish inbox-only delivery. Existing async schedule routes contain
blocking AWS calls; a worker must retain its resources after caller timeout.

Still required: monitor creation/control and delivered alerts; real terminal
pipeline/output evidence and runtime gaps; durable reviewed repair/Slack approval;
observable governance denial; client-specific acceptance evidence. BrightAgent in
the BrightHive Slack workspace is the requested test destination; exact routing
and the human reviewer's Slack identity remain to be resolved before messaging.

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
