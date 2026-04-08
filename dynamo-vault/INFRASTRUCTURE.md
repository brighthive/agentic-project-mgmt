# BrightHive AWS Infrastructure & Workspace Registry

**Source**: DynamoDB tables scanned across 4 AWS accounts via `dynamo-vault/` CLI.
**Last Scanned**: 2026-04-08
**Linked To**: [`platform-saas-ai-context/docs/infrastructure/AWS_ACCOUNTS.md`](../platform-saas-ai-context/docs/infrastructure/AWS_ACCOUNTS.md)

---

## Platform AWS Accounts

| Alias | Account ID | Profile | Purpose | DynamoDB Tables | Workspaces |
|-------|------------|---------|---------|-----------------|------------|
| **DEV** | `531731217746` | `brighthive-development` | Development / internal testing | 1 | 0 |
| **STAGE** | `873769991712` | `brighthive-staging` | Staging environment | 8 | 131 (52 provisioned) |
| **PROD** | `104403016368` | `brighthive-production` | Production — all live clients | 9 | 502 (169+ provisioned) |
| **MAIN** | `396527728813` | `brighthive-main` | Platform core / orchestration | 17 | 175 (167 provisioned) |

> "Provisioned" = has a dedicated AWS account number assigned via CDK.

---

## DynamoDB Tables by Account

### STAGE (873769991712)

| Table | Items | PK | Contains |
|-------|-------|----|----------|
| `AdminConfig` | 67 | `UUID` | Workspace name (nested), owner, CDK ARNs, groups |
| `PlatformAccountsTable` | 52 | `UUID` | `EntityName`, AWS account #, `EnvSecretArn`, `accountSecretARN`, `ApiUrls` (client_secret!), IAM roles, type |
| `PlatformS3BucketsByAccount` | 59 | `uuid` | S3 bucket ARNs, entity type, S3 role ARN |
| `LangsmithTokenUsage` | ~1000 | `org_id` / `date_user_id` | Token usage tracking |
| `AgentBasedUsageData` | 0 | `workspace_id` / `date_user_id` | Agent usage metrics |
| `UserCreation` | 34 | `Email` | User onboarding records |
| `TableIdsByDataAssetUuid` | 199 | `dataAssetId` | Data asset to table ID mapping |
| `amplify-dynamodb-table` | 3 | `workspace_project_UUID` | Amplify project configs |

### PROD (104403016368)

| Table | Contains |
|-------|----------|
| `AdminConfig` | Same schema as STAGE |
| `PlatformAccountsTable` | Same schema — **169 provisioned entities** |
| `PlatformS3BucketsByAccount` | S3 bucket ARNs for all PROD entities |
| `IBMServiceInstances` | IBM Watson/wxo catalog integrations |
| `LangsmithTokenUsage` | Production token usage |
| `AgentBasedUsageData` | Production agent metrics |
| `UserCreation` | Production user records |
| `TableIdsByDataAssetUuid` | Production data asset mappings |
| `amplify-dynamodb-table` | Amplify configs |

### MAIN (396527728813)

| Table | Contains |
|-------|----------|
| `AdminConfig` | Workspace admin configs (167 entities) |
| `PlatformAccountsTable` | Platform account mappings |
| `dev-platform-account-s3-bucket-map` | S3 bucket map (1 item — dev only) |
| `BarriersDevApiTable` / `BarriersModelTable` | Barriers model data |
| `Qlarion_SNAP5050Table` | Qlarion integration |
| `demo-brighthive-data-asset-api-*` | Data asset API tables |
| `devtest-*` | Dev/test tables for various services |
| `programs` / `providers` / `table_specs` | Reference data |

### DEV (531731217746)

| Table | Contains |
|-------|----------|
| `ytresearch` | Only table — YouTube research data |

> DEV has no workspace infrastructure tables. All dev workspace testing happens in STAGE.

---

## Client Account Registry

### Production Clients (PROD Account)

#### Education Design Lab (EDL)

| Field | Value |
|-------|-------|
| Entity Type | Organization |
| UUID | `0f7e4a3e-3fed-439c-945f-5e5d0476b923` |
| AWS Account | `127793529216` |
| EnvSecretArn | `cdk-admin-secret/127793529216` (in PROD platform account) |
| AccountSecretARN | `cdk-admin-secret/127793529216` (in client account) |
| S3 Buckets | `brighthive-raw-127793529216`, `brighthive-staged-127793529216`, `brighthive-pii-classifier-results-127793529216` |
| S3 Role | `Brighthive-Data-Organization-S3Stack-s3role2867CC88-ZE5mrBw58fyO` |
| Neo4j Env | Prod |
| Data Ingestion | Step Functions state machine in `127793529216` |

#### Ivy Tech Community College (Indiana)

| Field | Value |
|-------|-------|
| Entity Type | Organization |
| UUID | `83c3d256-c244-465b-8ad3-873e70bdff32` |
| AWS Account | `782228116022` |
| EnvSecretArn | `cdk-admin-secret/782228116022` (in PROD platform account) |
| AccountSecretARN | `cdk-admin-secret/782228116022` (in client account) |
| S3 Buckets | `brighthive-raw-782228116022`, `brighthive-staged-782228116022`, `brighthive-pii-classifier-results-782228116022` |
| S3 Role | `Brighthive-Data-Organization-S3Stack-s3role2867CC88-Gj8cn3WDXMft` |
| Neo4j Env | Prod |
| Data Ingestion | Step Functions state machine in `782228116022` |

#### Virginia Workforce Data Trust

| Field | Value |
|-------|-------|
| Entity Type | Workspace (primary) + Organization (parent) |
| Workspace UUID | `6bf42308-1a5c-40ba-adee-a4a873a03a5b` |
| Workspace AWS Account | `529831121414` |
| Organization UUID | `db0f75e7-adc...` |
| Organization AWS Account | `626193158417` |
| EnvSecretArn | `cdk-admin-secret/529831121414` |
| S3 Buckets | `brighthive-resource-529831121414` |
| S3 Role | `Brighthive-Data-Workspace-S3Stack-s3role2867CC88-YL1YOuOcG9gp` |
| Neo4j Env | Prod |
| API URL | Redshift Schema API via Cognito auth |

**Virginia Sub-Agencies** (each has its own AWS account as an Organization):

| Agency | AWS Account | Type |
|--------|-------------|------|
| SCHEV (State Council of Higher Education) | `851725335446` | Organization |
| DJJ (Dept. of Juvenile Justice) | `845935676605` | Organization |
| DJJ Virginia | `224317127725` | Organization |
| VADOC (VA Dept. of Corrections) | `895588634042` | Organization |
| VCCS (VA Community College System) | `048407405467` | Organization |
| VEC (VA Employment Commission) | `361711873965` | Organization |
| VEDP (VA Economic Development Partnership) | `095191796905` | Organization |
| DWDA (Dept. of Workforce Development & Advancement) | `637423241618` | Organization |
| DOE (Dept. of Education) | `243245591396` | Organization |
| DSS (Dept. of Social Services) | `589696613480` | Organization |
| DVS (Dept. of Veterans Services) | `513369935368` | Organization |
| Governor's Office | `918037262496` | Organization |
| Governor's Office Org | `448372338585` | Organization |
| Northern Virginia CC | `400095111454` | Organization |

---

## All Named Entities — PROD (169 Provisioned)

Key production clients and partners with dedicated AWS accounts:

| Entity | AWS Account | Type |
|--------|-------------|------|
| Accelerate Montana | via PlatformAccountsTable | Organization |
| Alamo Colleges (5 campuses) | 5 separate accounts | Organizations |
| Austin Community College | dedicated account | Organization |
| Borough of Manhattan College | dedicated account | Organization |
| BrightHive (internal orgs) | multiple accounts | Org + Workspace |
| Bunker Hill Community College | dedicated account | Organization |
| CCCS | dedicated account | Organization |
| CCGEF Data Collab | dedicated account | Workspace |
| CDE | dedicated account | Organization |
| CDHE | dedicated account | Organization |
| CDLE (Employment & Training, Unemployment Insurance) | 2 accounts | Organizations |
| Central Lakes College | dedicated account | Organization |
| Cheese Merchants of America | dedicated account | Org + Workspace |
| Chicago Booth | dedicated account | Org + Workspace |
| Colibri Group | dedicated account | Organization |
| College of Eastern Idaho | dedicated account | Organization |
| Colorado Data Trust | dedicated account | Workspace |
| Colorado Workforce Development Council | dedicated account | Organization |
| Community College of Philadelphia | dedicated account | Organization |
| Community College of Rhode Island | dedicated account | Organization |
| CoreSignal | dedicated account | Organization |
| Craft Education | dedicated account | Organization |
| CredLens (multiple envs) | multiple accounts | Org + Workspace |
| Crowder College | dedicated account | Organization |
| CUNY (Central, Kingsborough, LaGuardia, Queensborough) | 4 accounts | Organizations |
| Education Design Lab | `127793529216` | Organization |
| Franklin Cummings | dedicated account | Organization |
| Graduation Alliance | (STAGE only) | Organization |
| Hennepin Technical College | dedicated account | Organization |
| IBM wxo Catalog | dedicated account | Org + Workspace |
| Indiana Tech | dedicated account | Organization |
| Initio Capital | dedicated account | Org + Workspace |
| Intercompany Markets | dedicated account | Org + Workspace |
| Ivy Tech Community College | `782228116022` | Organization |
| JEDx | dedicated account | Organization |
| Julius Education | dedicated account | Organization |
| KJ Industries | dedicated account | Org + Workspace |
| Maricopa Community Colleges | dedicated account | Organization |
| MW Solutions | dedicated account | Org + Workspace |
| Naver | dedicated account | Org + Workspace |
| Northcentral Technical College | dedicated account | Organization |
| Northwestern | dedicated account | Org + Workspace |
| OneTen | dedicated account | Organization |
| PAIRIN | dedicated account | Organization |
| Per Scholas | dedicated account | Organization |
| Pima Community College | dedicated account | Organization |
| Prince George's Community College | dedicated account | Organization |
| Professional Certification Guild | dedicated account | Organization |
| Rainwater Charitable Foundation | dedicated account | Org + Workspace |
| Saint Paul College | dedicated account | Organization |
| Salesflow.io | dedicated account | Org + Workspace |
| Seattle Colleges | dedicated account | Organization |
| Starfleet Academy | dedicated account | Organization |
| State of (AR, ME, NV, OH, SC, TX) | 6 accounts | Organizations |
| SUNY (Dutchess, Orange, Sullivan, Ulster, Westchester) | 5 accounts | Organizations |
| TechEd | dedicated account | Organization |
| Texas (multiple agencies) | multiple accounts | Organizations |
| Uintah Basin Technical | dedicated account | Organization |
| University of Chicago | dedicated account | Org + Workspace |
| Virginia Workforce Data Trust | `529831121414` (WS) / `626193158417` (Org) | Workspace + Org |
| Virginia Sub-Agencies (14 orgs) | 14 separate accounts | Organizations |
| WGU Labs | dedicated account | Organization |
| Western Governors University | dedicated account | Org + Workspace |

---

## Sensitive Fields

Fields in `PlatformAccountsTable` that contain secrets:

| Field | Location | Sensitivity |
|-------|----------|-------------|
| `ApiUrls.*.client_secret` | Cognito app client secret | **HIGH** — masked by default |
| `ApiUrls.*.client_id` | Cognito app client ID | **MEDIUM** — masked by default |
| `ApiUrls.*.token_endpoint` | Cognito token URL | **LOW** — masked by default |
| `EnvSecretArn` | Secrets Manager ARN in platform account | Reference only (not the secret value) |
| `accountSecretARN` | Secrets Manager ARN in client account | Reference only (not the secret value) |

Use `./cli/secrets fetch <name> --show-secrets` to unmask.

---

## CLI Quick Reference

```bash
cd dynamo-vault && source .venv/bin/activate

# List all DynamoDB tables
./cli/secrets list-tables --account PROD

# List all workspaces/orgs
./cli/secrets list --account PROD

# Fetch full config for a workspace (secrets masked)
./cli/secrets fetch EducationDesignLab --account PROD

# Fetch with secrets visible
./cli/secrets fetch VirginiaWorkforceDataTrust --account PROD --show-secrets

# Search by name substring
./cli/secrets search Virginia --account PROD

# Export full index to JSON + markdown
./cli/secrets export --account PROD --output data/prod

# Compare workspace across environments
./cli/secrets diff CarlosCoWorkspace --accounts STAGE,PROD
```

---

## Cross-References

- **System Architecture**: [`platform-saas-ai-context/docs/architecture/ARCHITECTURE.md`](../platform-saas-ai-context/docs/architecture/ARCHITECTURE.md) — How workspaces and organizations are provisioned
- **AWS Account Model**: [`platform-saas-ai-context/docs/infrastructure/AWS_ACCOUNTS.md`](../platform-saas-ai-context/docs/infrastructure/AWS_ACCOUNTS.md) — Account hierarchy and IAM trust model
- **Secrets Manager Vault**: [`aws-secrets-vault/`](../aws-secrets-vault/) — Secrets Manager inventory (complements this DynamoDB inventory)
- **Provisioning CDK**: `brighthive-admin` repo — Step Functions that create these accounts
- **Organization CDK**: `brighthive-data-organization-cdk` — Infra deployed into each org account
- **Workspace CDK**: `brighthive-data-workspace-cdk` — Infra deployed into each workspace account
