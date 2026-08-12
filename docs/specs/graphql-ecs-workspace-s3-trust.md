---
title: "GraphQL ECS — workspace S3 trust at provision time"
status: "Done"
created: "2026-08-12"
tags: [platform-core, ecs, workspace-cdk, iam, s3]
related:
  specs:
    - graphql-core-ecs-migration.md
  infrastructure:
    - graphql-ecs-iam-trust.md
---

# GraphQL ECS — workspace S3 trust at provision time

> **Repo:** `brighthive-data-workspace-cdk` and `brighthive-data-organization-cdk`
> (not in platform-core). Platform-core automation covers backfill + post-deploy
> sync; this spec closes the gap for **immediate** trust when a workspace/org is
> first created.

## Problem

`post_deployment_scripts/update_s3_role.py` reads `{env}/role/subgraph` and
patches the data-account S3 role trust with `role_arn` (Lambda) and
`webhook_role_arn`. It does **not** yet trust `ecs_task_role_arn`.

Until platform-core runs `sync_graphql_ecs_s3_trust.py` on the next deploy, new
workspaces are ECS-upload-broken.

## Required change

In both repos:

1. **`s3_stack.py`** — trust `role_arn`, `webhook_role_arn`, and optional `ecs_task_role_arn`
   from `{env}/role/subgraph` at synth time.
2. **Post-deploy script** — patch the data-account S3 role trust with the same ARNs:
   - organization-cdk: `post_deployment_scripts/update_s3_role.py`
   - workspace-cdk: `post_deployment_scripts/update_api_url.py`

Platform-core `sync_graphql_ecs_s3_trust.py` backfills existing accounts on every deploy.

## Acceptance

```gherkin
  Scenario: New workspace trusts ECS at provision time
    Given staging/role/subgraph contains ecs_task_role_arn
    When workspace-cdk finishes provisioning a new data account
    Then the S3 role trust includes Lambda, webhook, and ECS task role ARNs
    And onboardResource succeeds on ECS before any platform-core deploy
```
