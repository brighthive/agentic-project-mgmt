---
title: "On-prem runner enrolment — the runner's identity comes from the customer's own"
epic: "BH-1421"
author: "drchinca"
status: "Draft"
created: "2026-08-14"
last-reviewed: "2026-08-14"
generates: "tickets"
tags: [on-prem, identity, secrets, mcp, loopcapital, security]
related:
  specs:
    - "on-prem-engineering-runner.md"
    - "brightagent-local-plugin.md"
    - "onprem-outbound-job-queue.md"
  adr:
    - "0002-engineering-runs-on-the-customers-filesystem.md"
    - "0004-outbound-polling-queue-for-onprem-engineering-work.md"
---

# On-prem runner enrolment

## 1. Context

Installing the runner today means hand-writing a file of secrets on the customer's host:
warehouse host, database, login, password, a second password their own `profiles.yml`
interpolates, and a control-plane key. Every one is copied by a human from somewhere it
already exists, which is both busywork and a second place for it to drift.

The obvious fix — read them from AWS Secrets Manager — is the wrong one, and the codebase
already says so in two places: *"a customer's on-prem host must never hold AWS
credentials"* (`pyproject.toml`), and *"giving a customer's machine a path into our account
to read a secret is a worse trade than the env vars it replaces"* (`credentials.py`).

The right identity is already in the room. Frank authenticates to the hosted BrightAgent
MCP through Cognito federated to **Loop Capital's own IdP**, and the pre-token-generation
Lambda stamps `custom:workspace_id` onto the JWT before it is issued. The hosted server
binds workspace from that principal and refuses workspace-scoped tools when it is absent
(`brightbot/brightbot/mcp/auth.py:6,252`). "Frank is Frank, and Frank means Loop Capital"
is therefore already true and already enforced — it simply has never been used to
provision the runner.

```mermaid
sequenceDiagram
  participant Frank as Frank's harness
  participant MCP as Hosted BrightAgent MCP
  participant Runner as On-prem runner
  participant CP as platform-core

  Frank->>MCP: enrol_onprem_runner()   [JWT: workspace bound by IdP]
  MCP-->>Frank: enrolment CODE (short-lived, single-use) — not a credential
  Frank->>Runner: brightagent-onprem --enrol <code>
  Runner->>CP: redeem(code)            [direct, out of band]
  CP-->>Runner: runner token, scoped to ONE workspace
  Note over Runner: token written mode-600; no AWS credential anywhere
  Runner->>CP: fetch warehouse connection  [its own token]
```

### What this replaces

The customer's env file drops from a list of secrets to four values, one of which is
secret. Warehouse credentials stop existing at rest on their disk entirely — the runner
needs them in memory to open a connection either way, so fetching them removes the
resting copy without adding exposure.

### The problem it must not create

`isValidServiceKey` compares against a single global `SCHEDULER_SERVICE_API_KEY`. That key
is adequate for posting run reports, and completely inadequate for fetching credentials: a
global key that can read any workspace's warehouse connection turns one compromised
customer host into a cross-tenant incident. [ADR-0004](../adr/0004-outbound-polling-queue-for-onprem-engineering-work.md)
already flagged the tenancy model as *"prototype-only … deliberately deferred"*. This is
where that debt comes due, and it must be paid before, not after.

### Why a code and not a token

An MCP tool's return value lands in the model's context, and from there in transcripts and
logs. A tool that returns a long-lived credential has published it. The enrolment code is
short-lived, single-use, and worth nothing without the redemption call the runner makes
directly — so the real credential never enters the conversation.

## 2. Interface Contract (MDE)

```
# Hosted MCP tool — workspace comes from the JWT, never from an argument
enrol_onprem_runner(project_id: str, label: str)
  -> { enrolment_code: str, expires_at: str, control_plane_endpoint: str,
       workspace_id: str, project_id: str }
   | { status: "refused", reason: str }

# platform-core, unauthenticated except by the code itself (single use)
redeemOnPremRunnerEnrolment(input: { enrolmentCode: ID! })
  -> { runnerToken: String!, workspaceId: ID!, projectId: ID!, expiresAt: String }

# platform-core, authenticated by the runner token — scope is bound to the TOKEN
onPremRunnerConfig
  -> { warehouse: { host, port, database, username, password },
       dbtEnv: [{ name, value }] }

# Runner adapter (third implementation of the existing CredentialSource port)
BRIGHTAGENT_ONPREM_CREDENTIALS_SOURCE = environment | workspace_secret | control_plane
```

The customer's file after enrolment:

```bash
export BRIGHTAGENT_ONPREM_CONTROL_PLANE_ENDPOINT=...
export BRIGHTAGENT_ONPREM_RUNNER_TOKEN=...        # the only secret
export BRIGHTAGENT_ONPREM_DBT_PROJECT_DIR=...
export BRIGHTAGENT_ONPREM_SOURCE_ROOTS=...
```

## 3. Invariants (DbC)

| # | Invariant |
|---|---|
| INV-1 | `THE System SHALL NOT require AWS credentials on a customer-operated host.` The `control_plane` adapter reaches only the control plane, over the same outbound HTTPS report delivery already uses. |
| INV-2 | `A runner token SHALL authorise exactly one workspace`, fixed at issue time from the enrolling JWT. Workspace is never an argument the runner supplies. |
| INV-3 | `WHEN a tool returns enrolment material, THE System SHALL return a single-use code and never a credential` — tool results are model-visible. |
| INV-4 | `An enrolment code SHALL be single-use and short-lived`; redeeming twice fails rather than issuing a second token. |
| INV-5 | `IF the control plane is unreachable at boot, THEN THE System SHALL fail loudly` — never silently fall back to another credential source. A runner using different credentials than the operator asked for is worse than one that will not start. |
| INV-6 | `THE System SHALL NOT return a credential the enrolling user could not already read` — enrolment grants no privilege the human lacked. |

## 4. Acceptance Criteria (BDD)

```gherkin
Feature: A runner gets its identity from the customer's own

  Scenario: Enrolment binds the workspace from the token, not the request
    Given Frank is authenticated to the hosted MCP with a Loop Capital JWT
    When he calls enrol_onprem_runner for his project
    Then the returned enrolment is scoped to Loop Capital's workspace
    And passing a different workspace_id changes nothing about that scope

  Scenario: The credential never enters the conversation
    When enrol_onprem_runner returns
    Then the payload contains a single-use code and no runner token

  Scenario: A code cannot be redeemed twice
    Given an enrolment code already redeemed once
    When the runner redeems it again
    Then the request is refused and no second token is issued

  Scenario: A runner token reaches exactly one workspace
    Given a runner token issued for Loop Capital
    When it requests configuration for another workspace
    Then the request is refused

  Scenario: No AWS credentials on the customer's host
    Given a runner enrolled with the control_plane source
    When it resolves warehouse credentials
    Then it calls only the control plane, and the host holds no AWS credential

  Scenario: An unreachable control plane fails loudly
    Given the control plane is unreachable
    When the runner starts with the control_plane source
    Then it exits non-zero naming the cause, and does not fall back
```

## 5. Out of Scope

- **Rotating or revoking runner tokens through the UI** — the model must allow it, but the surface is separate work.
- **A customer's own secret manager (Vault, Azure Key Vault)** — the port already anticipates it as a further adapter; not this spec.
- **`workspace_secret` adapter changes.** It stays exactly as it is: Brighthive-operated hosts only.
- **`BRIGHTAGENT_ENGINEER_PASSWORD` and its kin.** These are the customer's own `profiles.yml` variables. Whatever supplies them, dbt resolves them from the process environment, so the wrapper must export them; only their *source* is in scope here.

## 6. Dependencies

| Dependency | Status |
|---|---|
| Per-workspace runner token model, replacing the global `SCHEDULER_SERVICE_API_KEY` for this path | **Blocking** — nothing else may land first |
| `CredentialSource` port (BH-1422) | Ships — this is adapter #3 |
| `control_plane_client.execute_graphql(endpoint, service_key, …)` | Ships — already the right shape |
| `secretWarehousesById(store).get(warehouseId)` in platform-core | Ships — the server-side lookup already exists |
| Cognito → `custom:workspace_id` federation | Ships — verified in `mcp/auth.py` |

## 7. Correctness Properties

### Property 1: A runner cannot outreach the human who enrolled it

*For any* runner token, the set of workspaces it can read configuration for is a subset of
those the enrolling JWT could act for — a single workspace.

**Validates: §3 INV-2 and INV-6, §4 Scenario "A runner token reaches exactly one workspace"**

### Property 2: No credential is observable from a transcript

*For any* enrolment, no value returned to the model is sufficient to obtain warehouse
credentials without a further direct call from the runner.

**Validates: §3 INV-3 and INV-4, §4 Scenario "The credential never enters the conversation"**

### Property 3: Blast radius is one tenant

*For any* compromised customer host, the credentials reachable with what that host holds
belong to that host's workspace alone.

**Validates: §3 INV-2, §4 Scenario "Enrolment binds the workspace from the token"**

## 9. Observability Contract

- **Log events**: `onprem_enrolment.code_issued`, `onprem_enrolment.redeemed`,
  `onprem_enrolment.replay_refused`, `onprem_runner_config.served`,
  `onprem_runner_config.workspace_mismatch_refused`
- **Attributes**: `workspace.id`, `project.id`, `runner.label` — never the token or code
- **Metrics**: none

Replay refusals and workspace mismatches are the two events worth alerting on: both mean
either a bug or an attempt.

## 10. Test Coverage Update

| Repo | Suite | What to add |
|---|---|---|
| `brighthive-platform-core` | `tests/integration/` | Real-behavior against live Neo4j: a code redeems once and fails the second time; a token issued for workspace A is refused config for workspace B; the issued scope follows the enrolling principal and ignores a supplied `workspaceId`. |
| `brightagent-engineering-runner` | `tests/` | `ControlPlaneCredentials` resolves against a real control-plane response; an unreachable endpoint exits non-zero and does **not** fall back; the adapter is selected by configuration alone. |
| `brighthive-e2e` | `e2e/` | One feature test: enrol through the hosted MCP, redeem, then run dbt with no warehouse credentials present in the environment. |

**Real-behavior requirement**: the cross-workspace refusal must be exercised against a real
issued token, not a mocked principal. It is the property the whole design turns on.

## Ticket Breakdown

| Ticket | Summary | Points | Epic |
|---|---|---|---|
| — | Per-workspace runner token model, replacing the global service key on this path | 5 | BH-1421 |
| — | `enrol_onprem_runner` MCP tool returning a single-use code | 3 | BH-1421 |
| — | `redeemOnPremRunnerEnrolment` + `onPremRunnerConfig` in platform-core | 3 | BH-1421 |
| — | `ControlPlaneCredentials` adapter + `--enrol` in the runner | 3 | BH-1421 |
| — | e2e: enrol, redeem, run dbt with no warehouse credentials in the environment | 2 | BH-1421 |

## Related

- `on-prem-engineering-runner.md` — the runner this enrols
- `brightagent-local-plugin.md` — the package it installs as
- [ADR-0004](../adr/0004-outbound-polling-queue-for-onprem-engineering-work.md) — the tenancy debt this pays
