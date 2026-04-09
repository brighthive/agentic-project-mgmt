# Azure Synapse Ingestion — DevOps Handoff

> Last updated: 2026-04-09 | Owner: @drchinca → @sherbiny-bh

## TL;DR

Synapse ingestion pipeline is **deployed to STAGE** (`873769991712`). It mirrors the Snowflake ingestion pattern: Step Functions orchestrates Glue → S3 → Synapse via a data loader Lambda. A warehouse router Lambda detects which warehouse type a workspace uses.

**Not yet in PROD.** Needs security review + E2E testing with real data before production rollout.

---

## Architecture

```
Airbyte → S3 (Parquet) → Glue Crawler → Glue Catalog
                                            ↓
                                   DataIngestionPipeline
                                            ↓
                                   WarehouseRouterLambda
                                     ↓           ↓           ↓
                                 REDSHIFT    SNOWFLAKE    AZURE_SYNAPSE
                                     ↓           ↓           ↓
                              RedshiftSfn   SnowflakeSfn  SynapseIngestionSfn
                                                                ↓
                                                    SynapseDataLoaderLambda
                                                                ↓
                                                    COPY INTO [schema].[table]
                                                    FROM 's3://...' (Parquet)
                                                                ↓
                                                    Azure Synapse Analytics
```

---

## Deployed Components (STAGE)

### CDK Stack: `SynapseIngestionStack`

**Repo**: `brighthive-data-organization-cdk`
**File**: `brighthive_data_cdk/synapse_ingestion.py`

| Resource | Type | Details |
|----------|------|---------|
| SynapseIngestionStateMachine | Step Functions | Orchestrates the full load pipeline |
| SynapseDataLoaderLambda | Lambda (Python 3.11) | 512MB, 10min timeout, pymssql 2.2.11 |
| SynapseIngestionRole | IAM Role | STS, Glue, SecretsManager, Lambda permissions |
| SynapseDataLoaderRole | IAM Role | Basic Lambda execution |

**Stack Output**: `SynapseIngestionSfnArn` (state machine ARN)

### Warehouse Router Lambda

**File**: `warehouse_router_lambda/main.py`

Reads `workspace_secret_store/{uuid}` → checks `warehouses.*.type` → returns `AZURE_SYNAPSE`, `SNOWFLAKE`, or `REDSHIFT` (default).

---

## Step Functions Flow

```
1. GlueGetTable          → Fetch table metadata + S3 location
2. ParallelDataRetrieval → [DynamoDB org lookup] + [SecretsManager workspace config]
3. GetOrgAdminSecret     → Fetch org AWS credentials (for S3 access)
4. CombineForLoader      → Merge all data into Lambda payload
5. InvokeSynapseDataLoader → Execute COPY INTO on Synapse
```

**Input**:
```json
{
  "workspace_uuid": "4d7ffd13-...",
  "organization_uuid": "6e8a3107-...",
  "table_name": "nusa_transactions"
}
```

---

## Synapse Data Loader Lambda

**File**: `synapse_data_loader_lambda/main.py`

What it does:
1. Parses Synapse config from workspace secret store
2. Maps Glue column types → T-SQL types
3. Connects via pymssql (TDS 7.4, TLS 1.2+)
4. `CREATE SCHEMA IF NOT EXISTS`
5. `CREATE TABLE IF NOT EXISTS` (from Glue schema)
6. `TRUNCATE TABLE` (idempotent — retries don't duplicate)
7. `COPY INTO [schema].[table] FROM 's3://...' WITH (FILE_TYPE = 'PARQUET')`
8. Returns `{"success": true, "table": "bh.nusa_transactions", "rows_loaded": 100}`

**Security**:
- SQL identifier sanitization (regex `^[A-Za-z_][A-Za-z0-9_]*$`)
- Credentials redacted in logs
- S3 creds embedded in COPY INTO (required by Synapse syntax — no parameterized alternative)

---

## Secrets & Credentials

| Secret | Location | Contains |
|--------|----------|----------|
| `workspace_secret_store/{ws_uuid}` | Platform account SM | `warehouses.*.{type, host, port, database, schema, username, password}` |
| `cdk-admin-secret/{org_account_id}` | Platform account SM | `{accessKeyId, secretAccessKey}` for S3 access |
| `staging/cdk-admin-user/credentials` | Platform account SM | Platform IAM creds for DynamoDB lookups |

### Staging Test Workspace (OneTen)

| Property | Value |
|----------|-------|
| Workspace UUID | `4d7ffd13-73d0-4f14-8f0e-63bfddceca7c` |
| Org UUID | `6e8a3107-ccf2-4022-aaad-031663ae32fa` |
| Workspace Account | `930996402201` |
| Org Account | `635116939665` |
| Synapse Host | `bh-synapse-workspace.sql.azuresynapse.net` |
| Synapse Database | `brighthivepool` |
| Synapse Schema | `bh` |
| Synapse Admin | `bhadmin` (password in vault) |

---

## Network Connectivity

**Current**: Public endpoints with TLS 1.2+

```
AWS Lambda (us-east-1) → NAT Gateway EIP → Public Internet → Azure Synapse (westus2:1433)
```

**Synapse firewall**: Currently open (0.0.0.0/0) — **dev only, must restrict before prod**.

**Production requirements**:
1. Assign static Elastic IPs to NAT Gateways in Lambda VPC
2. Add EIPs to Synapse firewall allowlist
3. Document EIPs per environment
4. Consider VPN for sensitive customers (Q3 2026)

---

## IAM Permissions

### SynapseIngestionRole (Step Functions)

```
sts:AssumeRole        → arn:aws:iam::{env_account}:role/{env}-datapiary-apis-caller
glue:GetTable         → arn:aws:glue:*:{platform_account}:table/glue-database-organization/*
glue:GetDatabase      → arn:aws:glue:*:{platform_account}:database/glue-database-organization
secretsmanager:Get    → workspace_secret_store/*, cdk-admin-secret/*
lambda:Invoke         → SynapseDataLoaderLambda
```

### Cross-Account Role (`{env}-datapiary-apis-caller`)

Must exist in org account with:
```
dynamodb:GetItem      → PlatformAccountsTable
secretsmanager:Get    → workspace_secret_store/*, cdk-admin-secret/*
```

---

## Testing

### Unit Tests (33 passing)

```bash
cd brighthive-data-organization-cdk
pytest tests/test_synapse_lambdas.py -v
```

Covers: identifier sanitization, type mapping, config parsing, event validation, connection failure, successful load, warehouse routing.

### Local Mock Synapse

```bash
cd ~/iccha/brighthive/mock-azure
docker compose up -d
# SQL Server 2022 at localhost:1433
# Database: brighthive_warehouse, Schema: bh
# Creds: bh_admin / see mock-azure/.env
```

### E2E Checklist

- [ ] Trigger warehouse router → confirms `AZURE_SYNAPSE` detection
- [ ] Trigger Synapse ingestion state machine with test Glue table
- [ ] Verify table created in Synapse `[bh].[table_name]`
- [ ] Verify row count matches S3 Parquet file
- [ ] Query table via Synapse Studio or BrightAgent
- [ ] Test with missing credentials → graceful error
- [ ] Test with suspended Synapse pool → connection timeout handled

---

## Deploying to a New Environment

```bash
# 1. Get platform creds
PLAT_KEY=$(aws secretsmanager get-secret-value \
  --secret-id "staging/cdk-admin-user/credentials" \
  --profile brighthive-staging --region us-east-1 \
  --query SecretString --output text | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['AWS_ACCESS_KEY_ID'])")

# 2. Get org account creds
ORG_KEY=$(aws secretsmanager get-secret-value \
  --secret-id "cdk-admin-secret/635116939665" \
  --profile brighthive-staging --region us-east-1 \
  --query SecretString --output text | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['accessKeyID'])")

# 3. Configure org account profile
aws configure set aws_access_key_id "$ORG_KEY" --profile 635116939665-profile
aws configure set aws_secret_access_key "$ORG_SECRET" --profile 635116939665-profile
aws configure set region us-east-1 --profile 635116939665-profile

# 4. Deploy
cd brighthive-data-organization-cdk
cdk deploy --all --profile 635116939665-profile --require-approval never \
  --context environment=STAGE \
  --context organization_uuid=81896846-2761-40e9-912b-bb84540e6412 \
  --context aws_env_access_key_id=$PLAT_KEY \
  --context aws_env_secret_access_key=$PLAT_SECRET
```

**Note**: `--profile` must point to the **org account** (target), not the platform account. Platform creds go via `--context` for DynamoDB lookups.

---

## Monitoring

| Metric | Alarm Threshold |
|--------|----------------|
| Step Function failure rate | > 10% in 1 hour |
| Lambda duration | > 5 minutes (approaching 10min timeout) |
| Synapse connection refused | Any occurrence (firewall or auth issue) |
| Missing warehouse secret | Any occurrence (misconfiguration) |

**CloudWatch Log Groups**:
- `/aws/stepfunctions/SynapseIngestionStateMachine`
- `/aws/lambda/SynapseDataLoaderLambda`

**Filter for errors**: `"success": false`

---

## Known Limitations

| Limitation | Impact | Timeline |
|-----------|--------|----------|
| Public endpoints only | No VPN/private link | Phase 2 (Q3 2026) |
| SQL auth only | No Azure AD/Entra ID | Phase 3 (Q4 2026) |
| Truncate-then-load | Loses concurrent writes | Acceptable for staging |
| S3 creds in COPY INTO SQL | Visible in Synapse query logs | Use STS short-lived tokens (Phase 2) |
| NAT GW IP whitelist | Fragile if IPs change | Document and automate |

---

## Related Jira Tickets

| Ticket | Summary | Status |
|--------|---------|--------|
| BH-312 | Org CDK: Synapse ingestion Step Functions | Done (STAGE) |
| BH-314 | Org CDK: Glue → Synapse table sync pipeline | Done (STAGE) |
| BH-317 | Platform Core: Synapse in DataIngestionStack | Done (STAGE) |
| BH-316 | Document AWS → Azure network connectivity | Draft |
| BH-318 | E2E test: Full ingestion pipeline → Synapse | Not started |
| BH-313 | Org CDK: SQL auth Lambda | Not started |

---

## Files Reference

| File | Repo | Purpose |
|------|------|---------|
| `brighthive_data_cdk/synapse_ingestion.py` | org-cdk | CDK stack definition |
| `synapse_data_loader_lambda/main.py` | org-cdk | Data loader Lambda |
| `warehouse_router_lambda/main.py` | org-cdk | Warehouse type detection |
| `tests/test_synapse_lambdas.py` | org-cdk | Unit tests (33 passing) |
| `config.yaml` | org-cdk | Environment config |
| `docs/infrastructure/AZURE_INFRASTRUCTURE.md` | platform-saas-ai-context | Azure resource inventory |
| `docs/infrastructure/ENVIRONMENTS.md` | platform-saas-ai-context | Full environment matrix |
| `docs/specs/azure-synapse-full-integration.md` | agentic-project-mgmt | Feature spec |
