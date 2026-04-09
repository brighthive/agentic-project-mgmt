---
title: "dbt Cloud Transformation Integration"
epic: "BH-172"
status: "Beta"
shipped_sprint: 8
shipped_date: "2026-04-08"
services: ["platform-core", "webapp", "brighthive-data-workspace-cdk", "brighthive-dbt"]
tags: ["dbt", "transformation", "data-products", "redshift", "github"]
related:
  specs: []
  pocs: []
notion_page: ""
---

# dbt Cloud Transformation Integration

## What It Does

BrightHive's dbt Cloud integration lets workspace admins connect their transformation pipeline to dbt Cloud and run data transformations directly from the Project Data Flow view. Users configure a dbt Cloud connection once per workspace, link GitHub repos containing dbt models, select jobs, and hit "Run" — the platform triggers the dbt Cloud job, polls for completion, and automatically registers the output tables as data products in the workflow DAG. No context-switching between dbt Cloud, GitHub, and BrightHive.

## How It Works

```
Workspace Admin (one-time setup)
  │
  ├─ 1. Configure TransformationService
  │     Store dbt Cloud credentials (accountId, API key, endpoint)
  │     Store GitHub PAT in AWS Secrets Manager
  │     Link GitHub repos from brighthive-dbt org
  │     Test connection (validates dbt Cloud + GitHub access)
  │
  └─ 2. Create Transformation per project
        Select dbt Cloud job from dropdown (fetched via API)
        Link to project in workflow DAG

User (ongoing)
  │
  ├─ 3. Click "Run" on Project Data Flow page
  │     Triggers dbt Cloud job via API
  │     Webapp polls status every 5 seconds
  │
  ├─ 4. Job completes (SUCCESS)
  │     Platform fetches run_results.json from dbt Cloud artifacts
  │     Auto-registers each successful model as a DataAsset
  │     Creates FinalDataProductGroup linked to Transformation
  │
  └─ 5. Data products appear in Output Data Assets
        Visible in workflow DAG with lineage
        Available for destinations, governance, and querying
```

### Architecture

```
┌──────────────┐     GraphQL      ┌──────────────────┐     REST API     ┌─────────────┐
│   Webapp      │ ───────────────> │  Platform Core    │ ──────────────> │  dbt Cloud   │
│  (React)      │ <─── polling ─── │  (Apollo/Neo4j)   │ <── artifacts ─ │  (Account    │
│               │                  │                   │                 │   26133)     │
└──────────────┘                  └──────────────────┘                 └─────────────┘
                                         │                                    │
                                    Neo4j Graph                          GitHub App
                                  ┌──────────────┐                   ┌─────────────┐
                                  │ Transformation│                   │ brighthive-  │
                                  │ Service       │                   │ dbt org      │
                                  │   └─ Transf.  │                   │  └─ repos    │
                                  │       └─ Data │                   │              │
                                  │         Assets│                   └─────────────┘
                                  └──────────────┘
                                         │
                                    Redshift Serverless
                                  ┌──────────────────┐
                                  │ workspace-database │
                                  │  ├─ database_{org} │ ← External schema (Glue, read-only)
                                  │  └─ dbt_{ws}_{proj}│ ← dbt output (writable)
                                  └──────────────────┘
```

### Data Model (Neo4j)

```
Workspace
  └─ TransformationService (1 per workspace)
     ├─ accountId, apiKey, apiEndpoint (dbt Cloud)
     ├─ gitHubAuthSecretArn (Secrets Manager)
     └─ GitHubRepoNodes[] (repoUrl, branch)

Project
  └─ Transformation (1+ per project)
     ├─ jobId (dbt Cloud job definition ID)
     ├─ transformationMethod: DBT_CLOUD
     └─ sourceUrl (GitHub repo link)

  └─ FinalDataProductGroup (auto-created per transformation)
     └─ DataAssetNodes[] (one per dbt model output)
```

## How to Use It

### For Users (UX Guide)

**One-time: Configure Transformation Service**

1. Go to workspace **Settings** > **Services** > **Add Transformation Service**
2. Select provider: **dbt Cloud**
3. Enter dbt Cloud **Account ID** (from dbt Cloud URL: `cloud.getdbt.com/deploy/{accountId}/...`)
4. Enter **API Key** (dbt Cloud Personal Access Token)
5. Enter **API Endpoint**: `https://di763.us1.dbt.com/api/v3/` (or your dbt Cloud host)
6. Click **Test Connection** — should show green checkmark for dbt Cloud
7. Navigate to **GitHub** tab > enter **Personal Access Token** with `repo` scope
8. Navigate to **Repositories** tab > **Add Repository** — paste repo URL from `brighthive-dbt` org
9. **Save**

**Per-project: Create Transformation**

1. Open the **Project Data Flow** page
2. Click **+ Add Transformation**
3. Fill in:
   - **Name**: e.g., "NUSA CPG Transformation"
   - **Description**: What the transformation does
   - **Source URL**: GitHub repo URL
   - **Job**: Select from dropdown (auto-populated from dbt Cloud)
4. **Save** — transformation appears in the workflow DAG

**Run Transformation**

1. Click the **Run** button (top-right of Project Data Flow)
2. Watch the status indicator: "Queued" → "Running" → "Success"
3. Run results popup shows each model with status and relation name
4. Output Data Assets section auto-populates with registered data products

### For Developers (Tech Guide)

**Key GraphQL Operations:**

```graphql
# Create transformation service (workspace-level)
mutation {
  createTransformationService(input: {
    workspaceId: "..."
    name: "DemoEnv dbt Cloud"
    provider: DBT_CLOUD
    accountId: "26133"
    apiKey: "dbtu_..."
    apiEndpoint: "https://di763.us1.dbt.com/api/v3/"
  }) { transformationServiceId }
}

# Create transformation (project-level)
mutation {
  createTransformation(input: {
    workspaceId: "...", projectId: "..."
    name: "NUSA CPG Transformation"
    transformationMethod: DBT_CLOUD
    jobId: "70471823582405"
    transformationServiceId: "..."
    sourceUrl: "https://github.com/brighthive-dbt/demoenv-cpg-transform"
  }) { transformationId }
}

# Trigger all transformations in project
mutation {
  runTransformationsInProject(input: {
    workspaceId: "...", projectId: "..."
  }) { jobId runId transformationName error }
}

# Poll run status (webapp calls this every 5s)
mutation {
  getTransformationRunStatus(input: {
    workspaceId: "...", runId: "..."
  }) { status statusHumanized results { index status relationName } dataProductsRegistered }
}
```

**Key Files:**

| File | Purpose |
|------|---------|
| `platform-core/src/graphql/service/dbt/dbt-api.ts` | dbt Cloud API v2 wrapper |
| `platform-core/src/graphql/models/transformation-service.ts` | Service CRUD, GitHub auth, connection testing |
| `platform-core/src/graphql/models/transformation.ts` | Transformation CRUD, job status resolution |
| `platform-core/src/graphql/models/project.ts` | runTransformationsInProject, getTransformationRunStatus, registerDbtOutputDataAssets |
| `platform-core/lambdas/dbt_validation/main.py` | Parse manifest.json, get Redshift schema ID |
| `webapp/src/Sheets/Transformation/CreateTransformation.tsx` | Transformation creation form |
| `webapp/src/ProjectWorkflow/ProjectWorkflowPage.tsx` | Run button + polling UI |
| `workspace-cdk/redshift_schemas_lambda/main.py` | External schema creation (cross-account Glue) |

**dbt Cloud API endpoints used:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/accounts/{id}/jobs/` | List jobs (dropdown) |
| POST | `/accounts/{id}/jobs/{jid}/run/` | Trigger run |
| GET | `/accounts/{id}/runs/{rid}/` | Poll status |
| GET | `/accounts/{id}/runs/{rid}/artifacts/run_results.json` | Get model results |
| GET | `/accounts/{id}/runs/{rid}/artifacts/manifest.json` | Get schema info |

## Sub-Features

### Job Dropdown Selection (BH-319)

Replaces manual Job ID text entry with a dropdown populated by querying dbt Cloud's job list API. Users see job names, not IDs. Manual entry toggle available as fallback.

### Workflow Job Status Display (BH-320)

The workflow DAG's transformation node shows the latest dbt Cloud run status — start time, duration, success/failure. Resolved by reading `jobId` from TransformationNode and calling `getLatestRun()` with per-service credentials.

### Auto-Register Data Products (BH-322)

When a dbt Cloud job succeeds, the platform automatically parses `run_results.json`, creates a `FinalDataProductGroup` per transformation, and registers each successful model output as a `DataAsset` in Neo4j with full lineage. Idempotent — safe to re-run.

### Duplicate Prevention (BH-323)

`createTransformation` validates uniqueness of `(projectId + jobId)` — prevents duplicate transformations pointing to the same dbt Cloud job.

### GitHub Repo Registry (BH-330)

TransformationService stores GitHub authentication (PAT via Secrets Manager) and linked repositories. Single auth token per service, multiple repos. Connection testing validates both dbt Cloud and GitHub access in parallel.

### GitHub Settings UI (BH-331)

Webapp drawer with tabs: Service Config, GitHub Connection (PAT entry), Repositories (add/remove repos). Test connection button validates everything before save.

### Cross-Account Glue Access Fix (BH-341)

External schemas for organization accounts must include `CATALOG_ID '{org_account_id}'` to route Redshift Spectrum to the correct Glue catalog. Without it, all cross-account queries fail with `EntityNotFoundException`. Fix in `workspace-cdk/redshift_schemas_lambda/main.py`.

## Limitations & Roadmap

| Limitation | Impact | Planned Fix | Ticket |
|-----------|--------|-------------|--------|
| No auto-provisioning of dbt Cloud projects/repos | Manual setup per workspace+project | Auto-provision pipeline from webapp | BH-332 (Epic) |
| No `deleteTransformation` mutation in public API | Can't remove transformations from UI | Add mutation to schema | Backlog |
| Cross-account Glue fix not deployed to all workspaces | Existing workspaces still broken | Migration script ready (PR #2) | BH-341 |
| TransformationService name may contain client names | "dbtcloudcooperators" visible on demo | Rename + enforce naming conventions | Backlog |
| Only Redshift cross-account wiring automated | Snowflake/Synapse BYOW = manual | Abstract per-provider pattern | BH-342 |
| No webhook-based job completion notification | Polling every 5s until complete | dbt Cloud webhooks | Future |
| dbt Cloud API key stored in Neo4j (not Secrets Manager) | Rotation requires node update | Move to Secrets Manager | BH-337 |

## Changelog

- **Sprint 8** (2026-04-08): Infrastructure fixes — CATALOG_ID bug fix (BH-341), repo cleanup, Nestle deletion, dbt Cloud credentials schema fix. Feature branches ready: BH-330 (core) + BH-331 (webapp)
- **Sprint 7** (2026-03-24): Core dbt integration — BH-319 job dropdown, BH-320 job status fix, BH-321 expose accountId, BH-322 auto-register, BH-323 duplicate prevention, BH-330 GitHub registry
- **Sprint 6** (2026-03-10): Initial Transformation CRUD — createTransformation, workflow DAG display, basic Run button

## Related

- **Architecture Doc**: `platform-saas-ai-context/docs/architecture/DBT_TRANSFORMATION_ARCHITECTURE.md`
- **Auto-Provisioning Plan**: `/Users/bado/.claude/plans/serene-finding-wirth.md`
- **Jira Epic**: [BH-172](https://brighthiveio.atlassian.net/browse/BH-172) (Features)
- **Jira Bugs**: [BH-341](https://brighthiveio.atlassian.net/browse/BH-341) (CATALOG_ID fix)
- **Jira Auto-Provision**: [BH-332](https://brighthiveio.atlassian.net/browse/BH-332) (next phase)
- **GitHub Org**: [brighthive-dbt](https://github.com/brighthive-dbt)
- **dbt Cloud**: Account 26133, host `di763.us1.dbt.com`
