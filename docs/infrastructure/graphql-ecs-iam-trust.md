---
title: "GraphQL ECS — IAM, roles, and cross-account S3 trust"
status: "Active"
created: "2026-08-12"
tags: [platform-core, ecs, iam, s3, workspace-cdk, organization-cdk, trust]
related:
  specs:
    - graphql-core-ecs-migration.md
    - graphql-ecs-workspace-s3-trust.md
repos:
  - brighthive-platform-core
  - brighthive-data-workspace-cdk
  - brighthive-data-organization-cdk
---

# GraphQL ECS — IAM, roles, and cross-account S3 trust

Handover document for the IAM and trust work required when GraphQL Core runs on
ECS Fargate instead of (or alongside) Lambda. Covers **outbound** permissions
(what the GraphQL caller can do in AWS) and **inbound** trust (who can assume
workspace/org S3 roles in data accounts).

Related specs:

- `docs/specs/graphql-core-ecs-migration.md` — ECS stack, cutover, runtime
- `docs/specs/graphql-ecs-workspace-s3-trust.md` — provision-time trust in CDK repos

---

## 1. Problem

GraphQL mutations such as `onboardResource` presign S3 uploads by:

1. Reading the workspace/org `s3RoleArn` from DynamoDB (`PlatformS3BucketsByAccount`)
2. Calling `sts:AssumeRole` into the **data account** S3 role
3. Generating a presigned URL with the assumed credentials

Data-account S3 roles were provisioned to trust only the **GraphQL Lambda**
execution role (`role_arn` in the subgraph secret). When traffic moves to ECS,
the **ECS task role** must be trusted the same way or uploads fail after Neo4j
writes succeed (`presignedUrl: null`, `success: false`).

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Platform account (dev / staging / prod)                                  │
│                                                                          │
│  Secrets Manager: {env}/role/subgraph                                    │
│    role_arn              → GraphQL Lambda execution role                 │
│    webhook_role_arn      → OpenMetadata webhook Lambda role              │
│    ecs_task_role_arn     → GraphQL ECS Fargate task role (when deployed) │
│                                                                          │
│  GraphQL caller (Lambda or ECS)                                          │
│    outbound: sts:AssumeRole *  (platform IAM)                            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ sts:AssumeRole
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Data account (per workspace or organization)                             │
│                                                                          │
│  S3Stack s3_role — trust policy must include:                            │
│    • role_arn (Lambda)                                                   │
│    • ecs_task_role_arn (ECS)                                             │
│    • webhook_role_arn (webhook pipeline)                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Subgraph secret contract

**Secret id:** `{env}/role/subgraph` in the platform AWS account.

| Key | Source (platform-core deploy) | Purpose |
|-----|-------------------------------|---------|
| `role_arn` | `{Env}-BPC-BrighthiveCoreStack` → `{Env}ApolloServerRoleArn` | GraphQL Lambda |
| `webhook_role_arn` | `{Env}-BPC-InternalApiStack` → `{Env}WebhookRoleArn` | OM webhook Lambda |
| `ecs_task_role_arn` | `{Env}-BPC-GraphqlEcsStack` → `{Env}GraphqlEcsTaskRoleArn` | GraphQL ECS task role (optional until stack deployed) |

**Environment prefix mapping**

| Context | Secret prefix |
|---------|---------------|
| platform-core CLI / CI | `dev`, `staging`, `prod` |
| workspace-cdk / org-cdk CDK context | `dev`, `stage`→`staging`, `prod` |

Written by `brighthive-platform-core/update_s3_role_arn.py` after every
platform-core CDK deploy. Merges with existing keys; does not drop unrelated fields.

---

## 4. Platform-core — outbound IAM (ECS task role)

**Module:** `brighthive_core/graphql_api_iam.py`

### Standard grants (`grant_graphql_api_permissions`)

Attached to the ECS task role (and intended for Lambda parity):

| Area | Actions |
|------|---------|
| DynamoDB (scoped) | R/W on notifications, inbox, subscriptions, brightroutines tables |
| Cognito | Admin user-pool operations on platform pool |
| SES | SendEmail, SendRawEmail |
| Glue schema registry | Full schema/registry CRUD + tagging |
| DynamoDB | Get* on `PlatformS3BucketsByAccount` and `*` |
| S3 | `s3:*` on `*` |
| Step Functions | StartExecution |
| Lambda | InvokeFunction |
| API Gateway | execute-api:Invoke |
| Secrets Manager | Full read/write lifecycle |
| STS | **AssumeRole on `*`** (required to assume data-account S3 roles) |

### Lambda parity extras (`grant_graphql_api_lambda_parity_extras`)

| Extra | Staging | Prod (when enabled) |
|-------|---------|---------------------|
| Managed policy `dynamodb_write` | ✅ | Required at cutover |
| `DATAPLANE_BRIGHTAGENT_ROLE_ARN` scoped AssumeRole | ✅ demo org staging role | ❌ **Must add prod ARN** in `configuration.py` |

**Wiring:** `brighthive_core/graphql_ecs_stack.py` calls both helpers on the Fargate task role.

**Known gap:** Lambda CDK (`core_subgraph_api_stack.py`) still uses inline policies and
does not attach `dynamodb_write` or dataplane assume-role via CDK (may exist manually on live roles).

---

## 5. Platform-core — inbound trust automation

### Publish caller ARNs

**Script:** `update_s3_role_arn.py`

Run after CDK deploy (CI on all envs). Updates `{env}/role/subgraph` with latest
Lambda, webhook, and ECS task role ARNs from CloudFormation outputs (falls back
to `describe-stacks` when a stack had no changes in the deploy run).

### Bulk backfill existing data accounts

**Module:** `brighthive_core/graphql_ecs_s3_trust_sync.py`  
**CLI:** `sync_graphql_ecs_s3_trust.py`

```bash
AWS_REGION=us-east-1 uv run python sync_graphql_ecs_s3_trust.py \
  --env staging --profile brighthive-staging
```

Behavior:

1. Load `role_arn`, `ecs_task_role_arn`, `webhook_role_arn` from subgraph secret
2. **Skip entirely** if `ecs_task_role_arn` is absent (GraphqlEcsStack not deployed)
3. Scan `PlatformS3BucketsByAccount` for all `s3RoleArn` values
4. For each data account, assume `cdk-admin-secret/{accountId}` and patch S3 role trust idempotently
5. Per-account failures (stale admin creds, deleted roles) log warnings; **exit 0** (do not block deploy)

**CI:** All deploy workflows run both scripts:

- `.github/workflows/deploy-dev.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-staging-branch.yml`
- `.github/workflows/deploy-production.yml`

**Tests:** `tests_cdk/test_graphql_ecs_s3_trust_sync.py` (trust merge logic)

---

## 6. Workspace-cdk — provision-time trust

**Repo:** `brighthive-data-workspace-cdk`

| Layer | File | Change |
|-------|------|--------|
| Helpers | `brighthive_data_cdk/subgraph_secret.py` | Extract caller ARNs; `stage`→`staging` |
| CDK | `brighthive_data_cdk/subgraph_principals.py` | Build `CompositePrincipal` |
| Synth | `brighthive_data_cdk/s3_stack.py` | Trust Lambda + webhook + ECS (was Lambda-only) |
| App | `app.py` | Read `staging/role/subgraph` when context is `STAGE` |
| Post-deploy | `post_deployment_scripts/update_api_url.py` | Patch S3 role trust after provision |
| Merge util | `post_deployment_scripts/subgraph_s3_trust.py` | Idempotent AssumeRole statements |
| Tests | `tests/test_subgraph_s3_trust.py` | Unit tests |

Post-deploy accepts `--env dev|stage|prod` (use **`stage`**, not `staging`, for staging).

---

## 7. Organization-cdk — provision-time trust

**Repo:** `brighthive-data-organization-cdk`

Same pattern as workspace-cdk:

| Layer | File |
|-------|------|
| Helpers | `brighthive_data_cdk/subgraph_secret.py` |
| CDK | `brighthive_data_cdk/subgraph_principals.py`, `s3_stack.py` |
| Post-deploy | `post_deployment_scripts/update_s3_role.py` |
| Merge util | `post_deployment_scripts/subgraph_s3_trust.py` |
| Tests | `tests/test_subgraph_s3_trust.py` |

Org `s3_stack.py` loads the subgraph secret at synth time via
`SecretsManagerConnector` with inline `stage`→`staging` mapping.

---

## 8. Per-environment status

| Item | Dev | Staging | Prod |
|------|-----|---------|------|
| Platform account ID | 558215002485 | 873769991712 | 104403016368 |
| `GraphqlEcsStack` in config | ❌ | ✅ `GRAPHQL_ECS_ENABLED` | ❌ |
| `ecs_task_role_arn` in secret | ❌ until deploy | ✅ when stack deployed | ❌ until deploy |
| Bulk trust sync effective | No-op | ✅ after ECS deploy | No-op until ECS |
| CDK provision-time trust | ✅ code | ✅ code | ✅ code |
| API traffic on ECS | ❌ | ❌ (`GRAPHQL_RUNTIME=lambda`) | ❌ |
| `DATAPLANE_BRIGHTAGENT_ROLE_ARN` | ❌ | ✅ staging demo org | ❌ **required at cutover** |

---

## 9. Operational runbook

### Verify subgraph secret

```bash
aws secretsmanager get-secret-value \
  --secret-id staging/role/subgraph \
  --profile brighthive-staging \
  --query SecretString --output text | jq .
```

Expect three keys when GraphqlEcsStack is deployed.

### Run bulk trust sync (staging)

```bash
cd brighthive-platform-core
uv run python sync_graphql_ecs_s3_trust.py --env staging --profile brighthive-staging
```

Use `--dry-run` to preview. Use `--account 930996402201` to limit to one data account.

### Verify data-account S3 role trust

In the workspace/org account, inspect the S3 role trust policy for all three
GraphQL caller ARNs from the subgraph secret.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `presignedUrl: null` on ECS, works on Lambda | S3 role lacks ECS principal | Run bulk sync or redeploy workspace with CDK PR |
| Bulk sync `error_InvalidClientTokenId` | Stale `cdk-admin-secret/{accountId}` | Refresh secret creds in platform account |
| Bulk sync skipped message | No `ecs_task_role_arn` in subgraph secret | Deploy GraphqlEcsStack; run `update_s3_role_arn.py` |
| New workspace upload broken before platform deploy | Expected until CDK PR merged | Merge workspace-cdk trust PR or manual trust patch |

### Staging validation (2026-08-12)

- Bulk sync patched **15** data accounts with ECS principal
- **~45** accounts failed on stale admin creds (non-blocking)
- OneTen (`930996402201`) upload confirmed working on ECS after trust patch

---

## 10. Production cutover checklist

1. Add `GRAPHQL_ECS_ENABLED` and sizing keys to PROD in `configuration.py`
2. Add prod `DATAPLANE_BRIGHTAGENT_ROLE_ARN` (not the staging demo org ARN)
3. Deploy `Prod-BPC-GraphqlEcsStack`
4. Confirm CI writes `ecs_task_role_arn` to `prod/role/subgraph`
5. Merge workspace-cdk + organization-cdk trust PRs
6. Run / verify `sync_graphql_ecs_s3_trust.py --env prod`
7. Smoke-test ECS ALB: `/health`, `currentUser`, `onboardResource`
8. DNS cutover: `api.app.brighthive.net` → ECS ALB
9. Set `GRAPHQL_RUNTIME=ecs` when ready; decommission Lambda warmer last

---

## 11. PR index (implementation)

| Repo | Branch | Scope |
|------|--------|-------|
| `brighthive-platform-core` | `marwan/graphql-ecs-s3-trust-sync` | IAM parity, subgraph secret, bulk sync, CI |
| `brighthive-data-workspace-cdk` | `marwan/graphql-ecs-s3-trust` | S3 trust at synth + post-deploy |
| `brighthive-data-organization-cdk` | `marwan/graphql-ecs-s3-trust` | S3 trust at synth + post-deploy |
| `agentic-project-mgmt` | `marwan/graphql-ecs-iam-trust-docs` | This doc + spec updates |

---

## 12. What was done (summary)

| Work item | Status |
|-----------|--------|
| ECS task role outbound IAM parity with Lambda | ✅ platform-core |
| Publish `ecs_task_role_arn` to subgraph secret | ✅ platform-core |
| Bulk backfill S3 trust for all DynamoDB accounts | ✅ platform-core |
| CI runs trust sync on dev/staging/prod deploy | ✅ platform-core |
| Workspace S3 role trusts ECS at create time | ✅ workspace-cdk (PR) |
| Organization S3 role trusts ECS at create time | ✅ organization-cdk (PR) |
| Workspace post-deploy trust patch | ✅ workspace-cdk (PR) |
| Organization post-deploy trust patch | ✅ organization-cdk (PR) |
| Fix workspace `stage`→`staging` subgraph secret path | ✅ workspace-cdk (PR) |
| Staging live backfill (partial) | ⚠️ ops — re-run after cred refresh |
| Prod ECS stack + cutover | ❌ pending |
