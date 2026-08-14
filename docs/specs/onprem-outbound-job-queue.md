---
title: "Outbound-only job queue — BrightAgent's cloud agent reaches the on-prem runner"
epic: "BH-1421"
author: "drchinca"
status: "Draft"
created: "2026-08-14"
last-reviewed: "2026-08-14"
generates: "tickets"
tags: [on-prem, transport, queue, mcp, loopcapital, security]
related:
  specs: ["on-prem-engineering-runner.md", "onprem-run-report-receiver.md"]
  adr: ["0004-outbound-polling-queue-for-onprem-engineering-work.md"]
---

# Outbound-only job queue for on-prem engineering work

## 1. Context

Frank's own harness already drives the engineering runner directly over local stdio (BH-1421).
That covers the human-in-the-loop case. It does not let BrightAgent's own cloud agent — the
watchdog, the nightshift, the proactive engineering loop — invoke a tool on the runner: there is no
inbound path, by the customer's own network terms (one static egress IP, 1433 inbound only, no
exceptions). This spec adds the missing direction: the runner polls outbound for work a cloud
agent queued, executes it with the same tool logic the MCP surface already exposes, and posts the
result back — never accepting an inbound connection.

See [ADR-0004](../adr/0004-outbound-polling-queue-for-onprem-engineering-work.md) for why polling,
not a held-open channel or a VPN.

## 2. Interface Contract (MDE)

### platform-core (new mutations/query)

```graphql
input EnqueueOnPremJobInput {
  workspaceId: ID!
  projectId: ID!
  tool: OnPremJobTool!
  argsJson: JSON
}

enum OnPremJobTool {
  LIST_PROJECT_FILES
  READ_PROJECT_FILE
  RUN_MODELS
  BUILD_MODELS
  TEST_MODELS
}

enum OnPremJobStatus {
  PENDING
  CLAIMED
  DONE
  FAILED
}

type OnPremJob {
  id: ID!
  tool: OnPremJobTool!
  argsJson: JSON
  status: OnPremJobStatus!
  resultJson: JSON
  enqueuedAt: String!
  claimedAt: String
  completedAt: String
}

type EnqueueOnPremJobOutput {
  job: OnPremJob!
}

input ClaimNextOnPremJobInput {
  workspaceId: ID!
  projectId: ID!
  leaseSeconds: Int
}

type ClaimNextOnPremJobOutput {
  job: OnPremJob
}

input CompleteOnPremJobInput {
  jobId: ID!
  succeeded: Boolean!
  resultJson: JSON
}

type CompleteOnPremJobOutput {
  ok: Boolean!
}

extend type Mutation {
  enqueueOnPremJob(input: EnqueueOnPremJobInput!): EnqueueOnPremJobOutput!
  claimNextOnPremJob(input: ClaimNextOnPremJobInput!): ClaimNextOnPremJobOutput!
  completeOnPremJob(input: CompleteOnPremJobInput!): CompleteOnPremJobOutput!
}

extend type Query {
  onPremJob(workspaceId: ID!, jobId: ID!): OnPremJob
}
```

`enqueueOnPremJob` is service-key authed for the cloud agent's own calls, matching every other
autonomous write in this codebase (`upsertPipelineLineageAsService`). `claimNextOnPremJob` /
`completeOnPremJob` are service-key authed for the runner's own calls — same shared secret
direction as `recordOnPremRunReport` (BH-1431), since the runner has no user JWT either.

### brightagent-engineering-runner (new)

```
poll_once(*, settings, destination) -> JobOutcome | None
  # claims at most one job, dispatches to the matching tool function, reports the result.

run_worker_loop(*, settings, destination, poll_interval_s, stop_after: int | None = None) -> None
  # calls poll_once on an interval. stop_after is test-only (bounded iteration count).
```

`console_scripts` gains `brightagent-onprem-worker`, a second, independent entry point from the
MCP server binary — this one genuinely is daemon-shaped (ADR-0004's cost: unlike the MCP surface,
it must run whether or not a harness session is open).

## 3. Invariants (DbC)

| # | Invariant |
|---|---|
| INV-1 | `THE System SHALL NOT open an inbound port to receive a job.` The worker only ever originates outbound HTTPS calls. |
| INV-2 | `WHEN a job is claimed, THE System SHALL set claimedAt and a lease expiry, and SHALL NOT let a second claimer take it before the lease expires.` Concurrent claims resolve to exactly one winner. |
| INV-3 | `IF a claimed job's lease has expired without a completeOnPremJob call, THEN THE System SHALL make it claimable again.` A worker that died or lost its link mid-run must not strand the job forever. |
| INV-4 | `THE System SHALL scope every job to exactly one (workspaceId, projectId)`, matching BH-1431's governance check — a runner polling for workspace A can never see or claim workspace B's jobs. |
| INV-5 | Service-key auth only on all three mutations; no `@authorized` directive, no user-session assumption — mirrors `recordOnPremRunReport`. |
| INV-6 | `completeOnPremJob` is idempotent on `jobId`: a retried completion call (ambiguous network failure) does not flip a `DONE` job back to re-completable, and does not error either — it is a no-op success. |

## 4. Acceptance Criteria (BDD)

```gherkin
Feature: The cloud agent reaches the on-prem runner without any inbound rule

  Scenario: A cloud-enqueued job is executed by a polling worker with zero inbound access
    Given a job enqueued for a workspace/project the runner is scoped to
    And the runner's poller is running on a host with no inbound route
    When the poller's next cycle runs
    Then it claims the job, executes the matching tool, and reports the result
    And the job is queryable as DONE with its result

  Scenario: Two pollers cannot claim the same job
    Given one pending job
    When two claim calls race
    Then exactly one succeeds and the other sees no job available

  Scenario: A dead worker's claim is reclaimed after its lease expires
    Given a job claimed by a worker that never completes it
    When the lease interval has passed
    Then the job becomes claimable again
    And a later claim call picks it up

  Scenario: A job for a different workspace is never visible
    Given jobs enqueued for two different workspace/project pairs
    When a worker scoped to workspace A polls
    Then it only ever claims workspace A's jobs

  Scenario: Completing an already-completed job is a safe no-op
    Given a job already marked DONE
    When completeOnPremJob is called again with the same jobId (a retried report after an ambiguous failure)
    Then the call succeeds and the job's result is unchanged
```

## 5. Out of Scope

- **A UI for enqueuing or observing jobs.** This spec is the transport spike (BH-1426's own
  framing: "design spike with a working prototype before committing to the rest"); who calls
  `enqueueOnPremJob` and how a human sees the result is the next layer, not this one.
- **Cancelling an in-flight job.** A queued-but-not-yet-claimed job can be left to expire
  naturally; cancelling a claimed job mid-execution needs a real design (dbt doesn't have a clean
  "stop now" story) and is deliberately not attempted here.
- **Prioritization / multiple concurrent jobs per project.** One job claimed at a time is enough to
  prove the transport; a real scheduler is a separate concern.
- **Encrypting `argsJson`/`resultJson` at rest** beyond what Neo4j's own storage already provides —
  no new encryption layer introduced here.

## 6. Dependencies

- BH-1425/BH-1431 — the outbound-delivery and service-key-receiver patterns this spec reuses.
- The engineering runner's existing tool functions (`project_files`, `dbt_runner`) — the worker
  dispatches to the same functions the MCP surface calls, not a reimplementation.

## 7. Correctness Properties

### Property 1: Exactly one worker ever executes a given job

*For any* job J, at most one `completeOnPremJob(J, ...)` call ever transitions it out of `CLAIMED`
into a terminal state from a *genuine* execution — a retried completion of the same result is a
no-op (INV-6), and a lease-expired reclaim only fires after the prior claimant's lease has lapsed
(INV-3), so two workers never believe they both own J at the same time (INV-2).

**Validates: §3 INV-2, INV-3, INV-6; §4 Scenario "Two pollers cannot claim the same job"**

### Property 2: No inbound reachability is ever required

*For any* deployment of the worker, the only network operations it performs are outbound HTTPS
requests it initiates on its own schedule. No component of this spec listens for, or requires, an
inbound connection.

**Validates: §3 INV-1, §4 Scenario "A cloud-enqueued job is executed by a polling worker with zero inbound access"**

## 8. Eval Criteria

Not applicable — no LLM inference in the queue mechanism itself (a cloud agent may decide *what*
to enqueue using an LLM, but that decision is out of this spec's scope).

## 9. Observability Contract

- **Log events**: `onprem_job.enqueued`, `onprem_job.claimed`, `onprem_job.completed`,
  `onprem_job.reclaimed` — each carrying `workspaceId`, `projectId`, `jobId`, `tool`.
- **Metrics**: none new for the spike; a production build would want claim latency (enqueue →
  claimedAt) as the headline SLI for "how long until the cloud agent's action actually runs."

## 10. Test Coverage Update

### platform-core

- **L2 (real-behavior, live Neo4j)**: enqueue → claim → complete round trip; two concurrent claims
  resolve to exactly one winner; a stale claim (lease artificially expired) is reclaimed; a job for
  a different workspace is never returned to a scoped claimer; a repeated `completeOnPremJob` call
  is a no-op.

### brightagent-engineering-runner

- **L2 (real-behavior)**: `poll_once` against a real local platform-core + Neo4j, executing a real
  `run_models` against the Loop Capital sandbox, with rows verified in the database — not trusting
  the job's own reported result.
- **Prototype demonstration** (documented in ADR-0004, not a CI-gated test): the worker running
  inside a network-isolated container with no inbound route, claiming and executing a job enqueued
  from outside, and a killed-mid-job worker's claim expiring and being reclaimed.
