---
title: "GraphQL Core — ECS Fargate migration"
status: "In Progress"
created: "2026-08-11"
tags: [platform-core, graphql, ecs, fargate, neo4j, infra]
related:
  specs:
    - staging-graphql-neo4j-capacity.md
    - SPEC-BH-1365-graphql-lambda-provisioned-concurrency.md
---

# GraphQL Core — ECS Fargate migration

> Replace the main GraphQL API Lambda (`core_apollo_server_lambda`) with an
> always-on ECS Fargate service behind an ALB. Resolves Lambda cold starts,
> API Gateway 29s integration timeout, and Neo4j connection-pool multiplication.

## 1. Context

See `staging-graphql-neo4j-capacity.md` for pool-exhaustion root causes. Phase 1
mitigations (pool caps, 503 fail-fast, health writes off) are deployed but
insufficient: up to 40 Lambda containers × 20 connections still oversubscribes
one Neo4j EC2.

**In scope (v1):** HTTP surface at `api.{env}.brighthive.net` — GraphQL,
upload, `/workflow-step-callback`, `/slack-internal/*`.

**Out of scope (v1):** OGM `/ogm` Lambda, Python webhook lambdas, Neo4j EC2 resize.

## 2. Interface contract

### Config keys (`brighthive_core/configuration.py`)

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `GRAPHQL_RUNTIME` | `"lambda"` \| `"ecs"` | `"lambda"` | Traffic target |
| `GRAPHQL_ECS_DESIRED_COUNT` | int | 2 | Fargate tasks |
| `GRAPHQL_ECS_MAX_CAPACITY` | int | 4 | Autoscale ceiling (staging) |
| `GRAPHQL_ALB_IDLE_TIMEOUT_SECONDS` | int | 120 | ALB idle timeout |
| `CATALOG_SYNC_MAX_CONCURRENT` | int | 2 | In-process job cap |

### Runtime env (ECS task)

Same secrets/env as GraphQL Lambda plus:

- `GRAPHQL_RUNTIME=ecs`
- `PORT=8080`

### Health

`GET /health` → `200 { "status": "ok"|"degraded", "neo4j": "connected"|"disconnected" }`

## 3. Invariants

- Client URL `https://api.{env}.brighthive.net/graphql` unchanged after cutover.
- Rollback: flip DNS/custom-domain back to API Gateway within 15 minutes.
- Staging/prod: minimum 2 Fargate tasks for HA.
- Catalog sync jobs run in-process queue on ECS (no Lambda self-invoke).
- OGM API remains on Lambda until a follow-up ticket.

## 4. Acceptance criteria

```gherkin
Feature: GraphQL Core on ECS Fargate

  Scenario: Health check passes on a warm task
    Given the ECS service has 2 healthy tasks
    When GET /health is called on the ALB
    Then the response is 200 with neo4j "connected"

  Scenario: First-load GraphQL is warm
    Given staging cutover to ECS is complete
    When the webapp calls getCurrentUserInfo as the first request
    Then p95 latency is under 1 second

  Scenario: Upload under moderate load
    Given 10 concurrent onboardResource calls on staging
    Then at least 95% succeed within 5 seconds
    And zero "Connection acquisition timed out" log lines during the window

  Scenario: Catalog sync without Lambda invoke
    Given GRAPHQL_RUNTIME is ecs
    When syncWorkspaceCatalog is triggered
    Then the HTTP response returns a job id within 3 seconds
    And the job completes via the in-process queue
```

## 5. Rollout

1. Deploy ECS + ALB parallel to Lambda (no traffic).
2. Validate via ALB DNS smoke tests.
3. Cutover Route53 / custom domain to ALB.
4. Disable EventBridge warmer; keep Lambda 48h for rollback.
5. Decommission GraphQL Lambda after soak.

## 6. Implementation log

| Item | Status |
|------|--------|
| Shared Express app (`create-app.ts`) | Done |
| Production entry + `/health` | Done |
| Dockerfile | Done |
| Catalog sync in-process queue | Done |
| CDK ECS stack | Done (staging parallel deploy) |
| Staging cutover | Pending |
