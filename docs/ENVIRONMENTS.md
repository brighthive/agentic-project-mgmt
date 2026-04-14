# BrightHive Environment Matrix

> Last updated: 2026-04-09

Four logical environments map to two platform accounts (PROD, STAGE). Each has a dedicated workspace + organization pair. Shared services (API, Cognito, Neo4j) are per-platform-account; data infrastructure (Redshift, S3, Glue) is per-workspace-account.

---

## Environments

| Environment | Purpose | Owner | Webapp | API | Workspace | Workspace UUID |
|-------------|---------|-------|--------|-----|-----------|----------------|
| **Prod Demo** | Sales demos on production | @Suzanne | [app.brighthive.io](https://app.brighthive.io) | `api.app.brighthive.net` | BrighthiveDemoEnvironment | `cd0c14b7-6a43-4e81-9b59-d3ae46b0d312` |
| **Prod Test** | UAT (current Nestlé) | @Matt | [app.brighthive.io](https://app.brighthive.io) | `api.app.brighthive.net` | ProdTestWorkspace | `1c814cd6-c88f-40f6-8c1c-12b75a73758e` |
| **Staging Demo** | Internal demos, prod mirror | @here | [staging.brighthive.io](https://staging.brighthive.io) | `api.staging.brighthive.net` | Brighthive Demo Environment | `1c7cb12e-6d1a-4922-98a8-cff4de70f24d` |
| **Staging Test** | Dev sandbox — break things here | @Kuri | [staging.brighthive.io](https://staging.brighthive.io) | `api.staging.brighthive.net` | OneTen Workspace | `4d7ffd13-73d0-4f14-8f0e-63bfddceca7c` |

**Promotion path:** Staging Test → Staging Demo → Prod Test → Prod Demo

---

## AWS Account Map

### Workspace Accounts

| Environment | Workspace Account | Org Account | Org Name | Org UUID |
|-------------|-------------------|-------------|----------|----------|
| **Prod Demo** | `985539759307` | `908027373553` | DemoEnv | `5fd24dc8-dd38-4872-8d6c-3ed82e834e14` |
| **Prod Test** | `789941350443` | `128245155604` | ProdTestOrganization | `f16c138a-4d35-41e5-ac2b-191c41127a51` |
| **Staging Demo** | `783764595475` | `340752819582` | DemoEnv | `d8bea253-00a6-4b43-8fb6-2be88e59f7d9` |
| **Staging Test** | `930996402201` | `635116939665` | Starfleet Academy | `6e8a3107-ccf2-4022-aaad-031663ae32fa` |

### Platform Accounts

| Account | Account ID | AWS Profile | Region | Role |
|---------|-----------|-------------|--------|------|
| **PROD** | `104403016368` | `brighthive-production` | `us-east-1` | Production platform services |
| **STAGE** | `873769991712` | `brighthive-staging` | `us-east-1` | Staging platform services |
| **DEV** | `531731217746` | `brighthive-development` | `us-east-1` | Development (CI/CD) |
| **MAIN** | `396527728813` | `brighthive-main` | `us-east-1` | AWS Organizations root, Amplify host |

---

## Shared Platform Services

Shared services run on the platform account and serve **all** workspaces on that account.

### Production Platform (`104403016368`)

| Service | Resource | ARN / Endpoint |
|---------|----------|----------------|
| **GraphQL API** | API Gateway | `api.app.brighthive.net` |
| **Core Lambda** | Subgraph | `arn:aws:lambda:us-east-1:104403016368:function:Prod-BPC-BrighthiveCoreSt-ProdBrighthiveCoreSubgra-kwqSjZjoPcMB` |
| **OGM Lambda** | Neo4j OGM | `arn:aws:lambda:us-east-1:104403016368:function:Prod-BPC-BrighthiveCoreSt-ProdBrighthiveOgmLambdaE-zAHmmg66XKZH` |
| **Cognito** | Platform User Pool | `us-east-1_uEuXw33N8` (`arn:aws:cognito-idp:us-east-1:104403016368:userpool/us-east-1_uEuXw33N8`) |
| **Cognito** | Internal User Pool | `us-east-1_6bp03oRQ9` (`arn:aws:cognito-idp:us-east-1:104403016368:userpool/us-east-1_6bp03oRQ9`) |
| **Neo4j** | EC2 (running) | `i-08fb8d8df3ed0db93` / `54.86.59.241` |
| **Webapp** | Amplify `production` | `arn:aws:amplify:us-east-1:396527728813:apps/d1dk6ngojdo9gg/branches/production` |

### Staging Platform (`873769991712`)

| Service | Resource | ARN / Endpoint |
|---------|----------|----------------|
| **GraphQL API** | API Gateway | `api.staging.brighthive.net` |
| **Core Lambda** | Subgraph | `arn:aws:lambda:us-east-1:873769991712:function:Staging-BPC-BrighthiveCor-StagingBrighthiveCoreSub-og4gv5yxVhDo` |
| **Cognito** | Platform User Pool | `us-east-1_EAYUbZPFk` (`arn:aws:cognito-idp:us-east-1:873769991712:userpool/us-east-1_EAYUbZPFk`) |
| **Cognito** | Internal User Pool | `us-east-1_YCh490eEp` (`arn:aws:cognito-idp:us-east-1:873769991712:userpool/us-east-1_YCh490eEp`) |
| **Neo4j** | EC2 (running) | `i-00a9471a698ae65ee` / `3.84.120.127` |
| **Webapp** | Amplify `staging` | `arn:aws:amplify:us-east-1:396527728813:apps/d1dk6ngojdo9gg/branches/staging` |

---

## DynamoDB Tables (Platform Account)

| Table | PROD (`104403016368`) | STAGING (`873769991712`) |
|-------|----------------------|------------------------|
| **AdminConfig** | `arn:aws:dynamodb:us-east-1:104403016368:table/AdminConfig` | `arn:aws:dynamodb:us-east-1:873769991712:table/AdminConfig` |
| **PlatformAccountsTable** | `arn:aws:dynamodb:us-east-1:104403016368:table/PlatformAccountsTable` | `arn:aws:dynamodb:us-east-1:873769991712:table/PlatformAccountsTable` |
| **PlatformS3BucketsByAccount** | `arn:aws:dynamodb:us-east-1:104403016368:table/PlatformS3BucketsByAccount` | `arn:aws:dynamodb:us-east-1:873769991712:table/PlatformS3BucketsByAccount` |
| **TableIdsByDataAssetUuid** | `arn:aws:dynamodb:us-east-1:104403016368:table/TableIdsByDataAssetUuid` | `arn:aws:dynamodb:us-east-1:873769991712:table/TableIdsByDataAssetUuid` |
| **AgentBasedUsageData** | `arn:aws:dynamodb:us-east-1:104403016368:table/AgentBasedUsageData` | `arn:aws:dynamodb:us-east-1:873769991712:table/AgentBasedUsageData` |
| **LangsmithTokenUsage** | `arn:aws:dynamodb:us-east-1:104403016368:table/LangsmithTokenUsage` | `arn:aws:dynamodb:us-east-1:873769991712:table/LangsmithTokenUsage` |
| **UserCreation** | `arn:aws:dynamodb:us-east-1:104403016368:table/UserCreation` | `arn:aws:dynamodb:us-east-1:873769991712:table/UserCreation` |
| **IBMServiceInstances** | `arn:aws:dynamodb:us-east-1:104403016368:table/IBMServiceInstances` | — |
| **BrightbotIngestionFlows** | — | `arn:aws:dynamodb:us-east-1:873769991712:table/BrightbotIngestionFlows` |

---

## Step Functions (Platform Account)

| State Machine | PROD ARN | STAGING ARN |
|--------------|----------|-------------|
| **Master Automated Setup** | `arn:aws:states:us-east-1:104403016368:stateMachine:PRODMasterAutomatedSetup7A09C6D2-856kwXGPE34l` | `arn:aws:states:us-east-1:873769991712:stateMachine:STAGEMasterAutomatedSetupACE0BF47-o3yURiwDMD8p` |
| **Create Workspace & Org** | `arn:aws:states:us-east-1:104403016368:stateMachine:CreateWorkspaceAndOrganization9FEA5682-H8URU84AI6CF` | `arn:aws:states:us-east-1:873769991712:stateMachine:CreateWorkspaceAndOrganization9FEA5682-Ihr7V37XxIyU` |
| **Add Org to Workspace** | `arn:aws:states:us-east-1:104403016368:stateMachine:AddOrgToWorkspace8B6C2278-sXsebfVati0K` | `arn:aws:states:us-east-1:873769991712:stateMachine:AddOrgToWorkspace8B6C2278-OEmdmcGhH7oL` |
| **Update Data Stacks** | `arn:aws:states:us-east-1:104403016368:stateMachine:UpdateDataStacksF55FFF32-73w1SceKss8z` | `arn:aws:states:us-east-1:873769991712:stateMachine:UpdateDataStacksF55FFF32-u5J8xsQLuLKz` |
| **Update Workspace Org** | `arn:aws:states:us-east-1:104403016368:stateMachine:UpdateWorkspaceOrganization` | `arn:aws:states:us-east-1:873769991712:stateMachine:UpdateWorkspaceOrganization` |
| **Delete Accounts** | `arn:aws:states:us-east-1:104403016368:stateMachine:SfnDeleteAccountsD2D79785-sot3kT9t9rx9` | `arn:aws:states:us-east-1:873769991712:stateMachine:SfnDeleteAccountsD2D79785-kvV4zAoZt5Lg` |
| **dbt Job Status** | `arn:aws:states:us-east-1:104403016368:stateMachine:dbtjobstatusstatemachine5FCE4D03-OJeQzT30yz4B` | `arn:aws:states:us-east-1:873769991712:stateMachine:dbtjobstatusstatemachine5FCE4D03-vIve5PMY2Fb8` |

---

## Redshift Serverless (Per Workspace Account)

| Environment | Account | Workgroup ARN | Endpoint | Port | Base RPU |
|-------------|---------|---------------|----------|------|----------|
| **Prod Demo** | `985539759307` | `arn:aws:redshift-serverless:us-east-1:985539759307:workgroup/4b4f8e08-d675-4950-9a6f-907761b658fe` | `brighthive-redshift-serverless-workgroup.985539759307.us-east-1.redshift-serverless.amazonaws.com` | 5439 | 16 |
| **Prod Test** | `789941350443` | `arn:aws:redshift-serverless:us-east-1:789941350443:workgroup/e8397183-5dc1-46cd-b462-a57ce4cfaf5c` | `brighthive-redshift-serverless-workgroup.789941350443.us-east-1.redshift-serverless.amazonaws.com` | 5439 | 16 |
| **Staging Demo** | `783764595475` | `arn:aws:redshift-serverless:us-east-1:783764595475:workgroup/9001b01c-8345-4a98-847b-aaa4fe17f384` | `brighthive-redshift-serverless-workgroup.783764595475.us-east-1.redshift-serverless.amazonaws.com` | 5439 | 16 |
| **Staging Test** | `930996402201` | `arn:aws:redshift-serverless:us-east-1:930996402201:workgroup/d4e0f336-989e-4ffd-a0c0-f566992b2c0d` | `brighthive-redshift-serverless-workgroup.930996402201.us-east-1.redshift-serverless.amazonaws.com` | 5439 | 16 |

Database: `workspace-database` (all environments)

---

## Workspace Lambda Functions

Each workspace account has identical Lambda functions deployed by workspace-cdk:

| Lambda | Prod Demo (`985539759307`) | Prod Test (`789941350443`) | Staging Demo (`783764595475`) | Staging Test (`930996402201`) |
|--------|---------------------------|---------------------------|------------------------------|------------------------------|
| **Redshift Schema Query** | `...-RedshiftSchemaQueryLambd-XsYw9UHSoJRj` | `...-RedshiftSchemaQueryLambd-OFdwXrWNVZf9` | `...-RedshiftSchemaQueryLambd-wSobRZayp5IO` | `...-RedshiftSchemaQueryLambd-BiVi9Oikbw1Z` |
| **Redshift Schemas** | `...-RedshiftSchemasLambda126-3H0QueNUcv8O` | `...-RedshiftSchemasLambda126-5E7foIl4jlZj` | `...-RedshiftSchemasLambda126-K12JCYGWoyDc` | `...-RedshiftSchemasLambda126-p7ssUhVK5ajU` |
| **Redshift Ingestion** | `...-RedshiftIngestionLambda3-AG5NG6HNyiP0` | `...-RedshiftIngestionLambda3-KUbQzw8HgYPB` | `...-RedshiftIngestionLambda3-0uqUohE3b3VC` | `...-RedshiftIngestionLambda3-DWNDelfnBvGP` |
| **Redshift Credentials** | `...-RedshiftCredentialCreati-xkv96XUI7ORz` | `...-RedshiftCredentialCreati-RYtOq3xyY7Dv` | `...-RedshiftCredentialCreati-mbw8DbFK9PMK` | `...-RedshiftCredentialCreati-iFGTTSSoYjqk` |
| **Redshift OpenMetadata** | `...-RedshiftOpenmetadataLamb-tHWKZU2jFqOo` | `...-RedshiftOpenmetadataLamb-0KgYN0qabIZp` | `...-RedshiftOpenmetadataLamb-Tvu45eZId7qk` | `...-RedshiftOpenmetadataLamb-Qn8H8w17wyDa` |
| **Process Results** | `brighthive-process-results-985539759307` | `brighthive-process-results-789941350443` | `brighthive-process-results-783764595475` | — |

All Lambda ARN prefix: `arn:aws:lambda:us-east-1:{account}:function:`

---

## CDK Admin Secrets (Secrets Manager)

Used to deploy workspace-cdk and organization-cdk to target accounts.

| Environment | Type | Secret ARN |
|-------------|------|------------|
| **Prod Demo** | Workspace | `arn:aws:secretsmanager:us-east-1:104403016368:secret:cdk-admin-secret/985539759307-uKHvlJ` |
| **Prod Demo** | Organization | `arn:aws:secretsmanager:us-east-1:104403016368:secret:cdk-admin-secret/908027373553-ZEleo5` |
| **Prod Test** | Workspace | `arn:aws:secretsmanager:us-east-1:104403016368:secret:cdk-admin-secret/789941350443-IymwAt` |
| **Prod Test** | Organization | `arn:aws:secretsmanager:us-east-1:104403016368:secret:cdk-admin-secret/128245155604-3FGNx2` |
| **Staging Demo** | Workspace | `arn:aws:secretsmanager:us-east-1:873769991712:secret:cdk-admin-secret/783764595475-kXY1gs` |
| **Staging Demo** | Organization | `arn:aws:secretsmanager:us-east-1:873769991712:secret:cdk-admin-secret/340752819582-yYGAtJ` |
| **Staging Test** | Workspace | `arn:aws:secretsmanager:us-east-1:873769991712:secret:cdk-admin-secret/930996402201-jZgfXq` |
| **Staging Test** | Organization | `arn:aws:secretsmanager:us-east-1:873769991712:secret:cdk-admin-secret/635116939665-NkpYkf` |

Platform CDK admin creds (for DynamoDB access during deploys):
- **PROD**: `arn:aws:secretsmanager:us-east-1:104403016368:secret:prod/cdk-admin-user/credentials`
- **STAGE**: `arn:aws:secretsmanager:us-east-1:873769991712:secret:staging/cdk-admin-user/credentials`

---

## Deployment Model

### Auto-Deploy (merge to branch triggers deployment)

| Repo | `production` → PROD | `staging` → STAGE | `develop` → DEV |
|------|---------------------|-------------------|-----------------|
| **brighthive-webapp** | Amplify → `app.brighthive.io` | Amplify → `staging.brighthive.io` | Amplify → `develop.brighthive.io` |
| **brighthive-platform-core** | Lambda (`104403016368`) | Lambda (`873769991712`) | Lambda (`531731217746`) |
| **brightbot** | LangGraph Cloud | LangGraph Cloud | LangGraph Cloud |

### Manual Deploy (per-account CDK)

| Repo | Prod Demo | Prod Test | Staging Demo | Staging Test |
|------|-----------|-----------|-------------|-------------|
| **workspace-cdk** | `985539759307` | `789941350443` | `783764595475` | `930996402201` |
| **organization-cdk** | `908027373553` | `128245155604` | `340752819582` | `635116939665` |

CDK deploy requires:
1. Platform CDK admin creds → `{env}/cdk-admin-user/credentials` (for DynamoDB lookups)
2. Target account CDK admin creds → `cdk-admin-secret/{account-id}` (for CloudFormation)
3. `--profile` must point to the **target account**, not the platform account

---

## Webapp URLs

| URL | Git Branch | Platform |
|-----|------------|----------|
| [app.brighthive.io](https://app.brighthive.io) | `production` | PROD |
| [staging.brighthive.io](https://staging.brighthive.io) | `staging` | STAGE |
| [stagingapp.brighthive.io](https://stagingapp.brighthive.io) | `staging` | STAGE |
| [develop.brighthive.io](https://develop.brighthive.io) | `develop` | DEV |
| [developapp.brighthive.io](https://developapp.brighthive.io) | `develop` | DEV |

Amplify App: `arn:aws:amplify:us-east-1:396527728813:apps/d1dk6ngojdo9gg`

---

## Environment Rules

| Rule | Details |
|------|---------|
| **Prod Demo** | Never deploy untested CDK. Sales-critical. |
| **Prod Test** | Controlled changes only. Active UAT with partners. |
| **Staging Demo** | Mirror of prod. Update intentionally for demo prep. |
| **Staging Test** | Break things here. All new CDK changes go here first. |
