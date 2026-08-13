---
title: "GraphQL ECS — production deployment runbook"
status: "Active"
created: "2026-08-13"
tags: [platform-core, ecs, production, iam, s3, workspace-cdk, organization-cdk, cutover]
related:
  specs:
    - graphql-core-ecs-migration.md
    - graphql-ecs-workspace-s3-trust.md
  infrastructure:
    - graphql-ecs-iam-trust.md
repos:
  - brighthive-platform-core
  - brighthive-data-workspace-cdk
  - brighthive-data-organization-cdk
---

# GraphQL ECS — production deployment runbook

Operational checklist for moving **production** GraphQL Core (`api.app.brighthive.net`)
from Lambda to ECS Fargate. Covers platform-core infra, **existing** workspace/org
accounts, provision-time trust for **new** accounts, validation, cutover, and rollback.

Companion docs:

- `graphql-ecs-iam-trust.md` — IAM/trust architecture and troubleshooting
- `graphql-core-ecs-migration.md` — migration spec, acceptance criteria, invariants

---

## 1. Goals and scope

| In scope (v1) | Out of scope (v1) |
|---------------|-------------------|
| GraphQL HTTP at `api.app.brighthive.net/graphql` | OGM at `/ogm` (stays on Lambda) |
| Upload / presigned S3 flows (`onboardResource`, etc.) | Neo4j EC2 resize |
| `/workflow-step-callback`, `/slack-internal/*` | Org data-ingestion SFN trust (see §7 — follow-up) |
| Catalog sync via in-process queue on ECS | Decommissioning GraphQL Lambda (48h+ soak after cutover) |

**Client contract:** URL and auth unchanged. Rollback target: flip DNS/API mapping back to API Gateway within ~15 minutes.

---

## 2. Prerequisites

Complete these **before** any production release that enables ECS.

### 2.1 Staging soak (gate)

- [ ] Staging ECS parallel deploy stable for ≥1 week
- [ ] Staging smoke tests pass on ALB (not just Lambda): `/health`, `currentUser`, `onboardResource`
- [ ] Staging upload path verified on ECS for at least one live workspace
- [ ] No sustained Neo4j pool-timeout alarms on staging ECS
- [ ] Staging cutover completed (or explicitly waived with written GO)

### 2.2 Code merged to `main`

| Repo | Required changes |
|------|-------------------|
| `brighthive-platform-core` | `GraphqlEcsStack`, `graphql_api_iam.py`, `update_s3_role_arn.py`, `sync_graphql_ecs_s3_trust.py`, CI hooks in `deploy-production.yml` |
| `brighthive-data-workspace-cdk` | S3 trust at synth + `update_api_url.py` post-deploy patch |
| `brighthive-data-organization-cdk` | S3 trust at synth + `update_s3_role.py` post-deploy patch |

### 2.3 Production AWS context

| Item | Value |
|------|-------|
| Platform account | `104403016368` |
| API domain | `api.app.brighthive.net` |
| Subgraph secret | `prod/role/subgraph` |
| DynamoDB account index | `PlatformS3BucketsByAccount` (platform account) |
| Per-data-account admin creds | `cdk-admin-secret/{accountId}` (platform account) |
| Typical ops profile | `brighthive-prod` or prod CDK admin equivalent |

---

## 3. Platform-core code changes (before prod release)

These are **not** all present on prod today. Land them in a release PR before cutover.

### 3.1 `configuration.py` — PROD block

Add (mirror staging, tune for prod load):

```python
# GraphQL ECS migration — parallel deploy first; cutover later.
"GRAPHQL_RUNTIME": "lambda",           # flip to "ecs" only at cutover (§9)
"GRAPHQL_ECS_ENABLED": True,
"GRAPHQL_ECS_DESIRED_COUNT": 2,        # minimum HA
"GRAPHQL_ECS_MAX_CAPACITY": 4,         # raise if prod traffic warrants
"GRAPHQL_ECS_CPU": 1024,
"GRAPHQL_ECS_MEMORY_MIB": 2048,
"GRAPHQL_ALB_IDLE_TIMEOUT_SECONDS": 120,
"CATALOG_SYNC_MAX_CONCURRENT": 2,

# Neo4j pool caps (same motivation as staging — fewer tasks × bounded pool)
"NEO4J_MAX_CONNECTION_POOL_SIZE": 20,
"NEO4J_CONNECTION_ACQUISITION_TIMEOUT_MS": 10_000,
"NEO4J_OM_CONCURRENCY": 8,
"NEO4J_HEALTH_PERSIST_ON_READ": False,
```

**Required — not optional:**

```python
"DATAPLANE_BRIGHTAGENT_ROLE_ARN": "<prod dataplane BrightAgent role ARN>",
```

Staging uses the demo-org staging role (`340752819582`). Prod needs the **production**
dataplane role ARN. Without this, ECS task role lacks scoped `sts:AssumeRole` for
BrightAgent dataplane paths that Lambda currently handles.

### 3.2 `app.py` — wire `GraphqlEcsStack` for PROD

Staging already gates on `GRAPHQL_ECS_ENABLED`. **Prod block must get the same
`GraphqlEcsStack(...)` instantiation** (after `CoreSubgraphApiStack`, before
`InternalApiStack`). As of 2026-08-13 the PROD section does not include this — add
it in the same PR as the config keys above.

### 3.3 Verify CI post-deploy scripts

`deploy-production.yml` must run after `cdk deploy`:

1. `update_s3_role_arn.py --env prod`
2. `sync_graphql_ecs_s3_trust.py --env prod`

Both are idempotent. Trust sync **no-ops** until `ecs_task_role_arn` exists in the subgraph secret.

---

## 4. Phase A — Parallel deploy (no traffic)

Deploy ECS alongside Lambda. Production traffic stays on API Gateway + Lambda.

### 4.1 Release and deploy

1. Merge platform-core to `main` via `staging → main` PR + GitHub release (triggers `deploy-production.yml`)
2. Confirm CloudFormation stack **`Prod-BPC-GraphqlEcsStack`** created
3. Confirm ECS service has **2 healthy tasks** in `us-east-1`

### 4.2 Verify subgraph secret

```bash
aws secretsmanager get-secret-value \
  --secret-id prod/role/subgraph \
  --profile brighthive-prod \
  --region us-east-1 \
  --query SecretString --output text | jq .
```

Expect **three keys** after deploy:

| Key | Role |
|-----|------|
| `role_arn` | GraphQL Lambda (rollback path) |
| `webhook_role_arn` | OpenMetadata webhook Lambda |
| `ecs_task_role_arn` | GraphQL ECS Fargate task role |

If `ecs_task_role_arn` is missing, run manually (with deploy outputs file):

```bash
cd brighthive-platform-core
uv run python update_s3_role_arn.py --env prod --profile brighthive-prod
```

### 4.3 Verify ECS outbound IAM

On the ECS task role (from `ecs_task_role_arn`):

- [ ] Inline policy from `grant_graphql_api_permissions` (includes `sts:AssumeRole` on `*`)
- [ ] Managed policy **`dynamodb_write`** attached
- [ ] Scoped `AssumeRole` to prod `DATAPLANE_BRIGHTAGENT_ROLE_ARN` (when configured)

### 4.4 Smoke-test via ALB only

Get ALB URL from stack output `ProdGraphqlEcsLoadBalancerUrl`:

```bash
curl -s "https://<alb-dns>/health" | jq .
```

Then authenticated GraphQL against the **ALB hostname** (not `api.app.brighthive.net` yet):

- `currentUser`
- Read-only catalog query
- `onboardResource` on a **test workspace** (after §5 trust backfill)

---

## 5. Existing workspaces and organizations — S3 trust backfill

Every row in `PlatformS3BucketsByAccount` points at an S3 IAM role in a **data account**.
That role's trust policy must allow the **ECS task role** to `sts:AssumeRole`, not just Lambda.

### 5.1 How backfill works

```
prod/role/subgraph  →  role_arn + ecs_task_role_arn + webhook_role_arn
        ↓
PlatformS3BucketsByAccount scan  →  per-account s3RoleArn
        ↓
Assume cdk-admin-secret/{accountId}  →  patch S3 role trust (idempotent)
```

**Script:** `brighthive-platform-core/sync_graphql_ecs_s3_trust.py`

Runs automatically on every prod deploy. Re-run manually after fixing admin creds.

```bash
cd brighthive-platform-core

# Full prod scan
uv run python sync_graphql_ecs_s3_trust.py --env prod --profile brighthive-prod

# Preview only
uv run python sync_graphql_ecs_s3_trust.py --env prod --profile brighthive-prod --dry-run

# Single customer account (after cred refresh)
uv run python sync_graphql_ecs_s3_trust.py --env prod --profile brighthive-prod --account <data-account-id>
```

**Exit code 0 even with per-account errors** — review log output; do not treat green CI as "all accounts patched."

### 5.2 Expected outcomes (from staging experience)

| Result | Meaning | Action |
|--------|---------|--------|
| `patched` / `would_patch` | ECS principal added | None |
| `already_trusted` | Trust already correct | None |
| `error_InvalidClientTokenId` | Stale `cdk-admin-secret/{accountId}` | Refresh secret in platform account; re-run `--account` |
| `error_ResourceNotFoundException` / `error_NoSuchEntity` | Role deleted or renamed | Confirm account still active; update DynamoDB row or decommission |
| `skipped_platform_account` | Platform account row in table | Ignored by design |

**Staging reference (2026-08-13):** 15 live accounts `already_ok`, ~45 failed on stale admin creds or decommissioned roles. Prod will have a similar split — **prioritize live customer accounts** over legacy test rows.

### 5.3 Prioritized account list

Before cutover, ensure trust is correct for:

1. **All production customer workspaces** with active uploads
2. **All production organizations** with S3-backed assets
3. High-traffic / demo workspaces used in UAT

Suggested workflow:

```bash
# 1. Dry-run full scan — capture WARNING lines to a file
uv run python sync_graphql_ecs_s3_trust.py --env prod --profile brighthive-prod --dry-run 2>&1 | tee prod-trust-sync-dry-run.log

# 2. Fix cdk-admin-secret for each live account that would patch but errors on real run

# 3. Re-run per account until customer set is clean

# 4. Spot-check trust policy in one workspace + one org account (AWS Console or CLI)
```

### 5.4 Refreshing `cdk-admin-secret/{accountId}`

The sync script cannot patch data accounts without valid admin credentials stored in the **platform** account Secrets Manager.

Ops steps (per failing account):

1. Confirm the data account is still provisioned and the S3 role exists
2. Update `cdk-admin-secret/{accountId}` with current CDK admin access key/secret for that account
3. Re-run: `sync_graphql_ecs_s3_trust.py --env prod --account {accountId}`

This is the **main blocker** for existing accounts — not a workspace/org redeploy.

### 5.5 Do existing workspaces need a CDK redeploy?

**No**, for the S3 upload path, if bulk sync succeeds:

- Trust is patched **in place** on the existing S3 role
- Workspace/org stacks do **not** need redeployment solely for ECS S3 trust

**Yes**, if you want synth-time trust guaranteed on the next stack update — merge workspace-cdk and organization-cdk trust PRs so future `cdk deploy` in data accounts includes ECS principals at creation time.

### 5.6 New workspaces/orgs after platform deploy

Once workspace-cdk and organization-cdk trust PRs are on the branch used for provisioning:

- **New** data accounts get Lambda + webhook + ECS trust at synth time
- Post-deploy scripts (`update_api_url.py` / `update_s3_role.py`) patch trust immediately after provision
- Bulk sync still runs on platform deploy as a safety net for any drift

---

## 6. What bulk sync does *not* cover

### 6.1 Org data-ingestion Step Functions role (known gap)

Organization `data_ingestion_stack.py` trusts only `core_api_role` (Lambda) on the
**StateMachineRole**, not `ecs_task_role_arn`.

**Affected paths:** GraphQL flows that assume `dataIngestionArns.StateMachineRoleArn`
(e.g. `deleteFromGlue` in platform-core).

**Impact at ECS cutover:**

- S3 upload / presign flows — **covered** by §5
- Glue deletion / ingestion SFN triggers from GraphQL — **may fail on ECS** until fixed

**Follow-up (separate PR):**

1. Extend organization-cdk to trust ECS principal on StateMachineRole (mirror S3 pattern)
2. Optional: extend bulk sync or a one-off script for existing org accounts
3. Re-deploy or patch existing org stacks per customer

Track as a **P2 cutover blocker** only if prod actively uses those GraphQL mutations on ECS day one.

### 6.2 Other roles that do *not* need ECS ARN trust

These use **account-level** or service principals, not GraphQL caller ARN:

- `AWSRedshiftRole` — trusts platform account ID
- Datapiary roles — similar pattern
- Webhook Lambdas, internal APIs — unchanged

---

## 7. Phase B — Pre-cutover validation

Complete on the **ECS ALB** before switching `api.app.brighthive.net`.

| Check | Pass criteria |
|-------|---------------|
| `/health` | `200`, `neo4j: "connected"` on both tasks |
| Warm GraphQL | `currentUser` p95 < 1s (no cold start) |
| Upload | `onboardResource` returns non-null `presignedUrl` on ≥3 prod workspaces |
| Concurrent upload | 10 concurrent uploads, ≥95% success, no pool-timeout logs |
| Catalog sync | `syncWorkspaceCatalog` returns job id < 3s; job completes via in-process queue |
| BrightAgent dataplane | Any prod flow using `DATAPLANE_BRIGHTAGENT_ROLE_ARN` succeeds |
| CloudWatch | No sustained `graphql-ecs-neo4j-pool-timeout` alarm |

Document ALB URL and test workspace IDs in the release ticket.

---

## 8. Phase C — Traffic cutover

### 8.1 Order of operations

1. Confirm §5 complete for all **live customer** accounts
2. Confirm §7 validation green
3. **Map** `api.app.brighthive.net` to ECS ALB (see §8.2)
4. Set `GRAPHQL_RUNTIME=ecs` in PROD config (ECS tasks already get this via `build_graphql_api_environment(..., runtime="ecs")`; config key documents intent and affects any Lambda-side reads)
5. Disable EventBridge GraphQL warmer (if enabled)
6. Monitor 30–60 minutes: 5xx rate, Neo4j alarms, upload errors, Sentry

### 8.2 DNS / API mapping

Production API domain is **manually mapped** (see platform-core `README.md` § API Mapping).

Cutover options (pick one — document which was used):

**Option A — Route53 / API Gateway custom domain remap**

Point `api.app.brighthive.net` from API Gateway integration to the ECS ALB target.
Exact steps depend on current API Gateway + ACM setup in prod console.

**Option B — Weighted / blue-green**

If infra supports it, shift traffic gradually ALB ← → API Gateway.

**Critical:** `/ogm` must **remain** on the existing Lambda/API Gateway mapping unless a separate OGM migration is planned.

### 8.3 Keep Lambda warm for rollback

After cutover:

- Do **not** delete `Prod-BPC-BrighthiveCoreStack` Lambda for ≥48 hours
- Keep `role_arn` in subgraph secret valid
- Rollback = remap domain to API Gateway + set `GRAPHQL_RUNTIME=lambda`

---

## 9. Phase D — Post-cutover

| Task | When |
|------|------|
| Re-run trust sync | After any GraphqlEcsStack redeploy that rotates task role ARN |
| Monitor Neo4j connections | 2 tasks × pool size should stay << Neo4j max |
| Scheduled-agent-dispatcher | Already points at `PLATFORM_CORE_GRAPHQL_URL` — no change if URL stable |
| Slack-server / brightbot | Use same GraphQL URL — verify after cutover |
| Decommission GraphQL Lambda | After ≥48h soak + explicit GO |
| Remove provisioned concurrency / warmer | After Lambda decommission plan approved |

---

## 10. Rollback procedure

If ECS cutover causes production incident:

1. **Remap** `api.app.brighthive.net` to API Gateway (Lambda) — target < 15 min
2. Set `GRAPHQL_RUNTIME=lambda` in config if any tooling reads it
3. Re-enable Lambda warmer if previously disabled
4. ECS stack can stay running (parallel) for debugging
5. Post-incident: fix trust/IAM/config before re-attempting cutover

Uploads continue working on Lambda rollback because S3 roles still trust `role_arn`.

---

## 11. Production deployment checklist (copy-paste)

### Pre-release

- [ ] Staging soak complete
- [ ] workspace-cdk + organization-cdk trust PRs merged to provisioning branch
- [ ] PROD `GRAPHQL_ECS_*` keys in `configuration.py`
- [ ] PROD `DATAPLANE_BRIGHTAGENT_ROLE_ARN` set (prod ARN, not staging)
- [ ] PROD `GraphqlEcsStack` wired in `app.py`
- [ ] Neo4j pool env keys added to PROD config

### Release deploy

- [ ] GitHub release → `deploy-production.yml` succeeds
- [ ] `Prod-BPC-GraphqlEcsStack` healthy (2 tasks)
- [ ] `prod/role/subgraph` has `ecs_task_role_arn`
- [ ] ECS task role has `dynamodb_write` + dataplane assume-role

### Existing accounts

- [ ] `sync_graphql_ecs_s3_trust.py --env prod` run; log archived
- [ ] All **live customer** accounts `patched` or `already_trusted`
- [ ] Stale `cdk-admin-secret/*` refreshed for any failed live accounts
- [ ] Spot-check S3 role trust in 1 workspace + 1 org account
- [ ] Org SFN ingestion gap assessed (§6.1)

### Validation

- [ ] ALB `/health` + GraphQL smoke tests pass
- [ ] `onboardResource` on prod workspaces via ALB

### Cutover

- [ ] `api.app.brighthive.net` mapped to ECS ALB
- [ ] `/ogm` still on Lambda
- [ ] Warmers adjusted; monitoring dashboards watched
- [ ] Rollback steps documented in release ticket

### Post-cutover

- [ ] 48h soak clean
- [ ] Lambda decommission ticket filed (optional)

---

## 12. Reference commands

```bash
# Subgraph secret
aws secretsmanager get-secret-value --secret-id prod/role/subgraph \
  --profile brighthive-prod --region us-east-1 --query SecretString --output text | jq .

# Trust sync
cd brighthive-platform-core
uv run python sync_graphql_ecs_s3_trust.py --env prod --profile brighthive-prod

# ECS ALB URL
aws cloudformation describe-stacks \
  --stack-name Prod-BPC-GraphqlEcsStack \
  --profile brighthive-prod --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='ProdGraphqlEcsLoadBalancerUrl'].OutputValue" \
  --output text

# Count DynamoDB accounts (platform account)
aws dynamodb scan --table-name PlatformS3BucketsByAccount \
  --projection-expression s3RoleArn \
  --profile brighthive-prod --region us-east-1 \
  --query 'length(Items)'
```

---

## 13. Related tickets / PRs

| Item | Location |
|------|----------|
| ECS migration spec | `docs/specs/graphql-core-ecs-migration.md` |
| IAM + trust architecture | `docs/infrastructure/graphql-ecs-iam-trust.md` |
| Workspace provision-time trust | `docs/specs/graphql-ecs-workspace-s3-trust.md` |
| Platform IAM module | `brighthive-platform-core/brighthive_core/graphql_api_iam.py` |
| Bulk trust sync | `brighthive-platform-core/sync_graphql_ecs_s3_trust.py` |
| Org ingestion gap | `brighthive-data-organization-cdk/brighthive_data_cdk/data_ingestion_stack.py` |
