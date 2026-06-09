---
title: Longaeva Trial Day 1 — Operator Runbook
last-reviewed: 2026-06-08
trial-day-1: 2026-06-15
owner: drchinca
audience: whoever drives the live demo (Kuri / Marwan / Ahmed / Harbour)
---

# Longaeva Trial Day 1 — Operator Runbook

> Read this top-to-bottom 24 hours before the demo. Run the **Pre-flight** section the morning of. The **Live demo script** is the 4-mutation sequence that closes GC-6 (Semantic View → GitHub PR). If anything in pre-flight is red, **stop** and route to the §"If something breaks" section before going live.

## TL;DR — what we're demoing

Customer drops a YAML semantic view in the BrightHive UI. We:
1. Validate the YAML against their live Snowflake account
2. Save the YAML on the DataAsset
3. Open a real GitHub PR against `github.com/brighthive/longaeva-semantic-views`
4. Optionally auto-merge

Total live-demo time: **~90 seconds** end-to-end. Everything else is talking points.

## What ships in develop today

| Component | PR | Status | What it does |
|---|---|---|---|
| Auth role hierarchy | pc#797 | ✅ merged | Workspace admin satisfies any required-role directive |
| WorkspaceGitHubBindingNode + setWorkspaceGitHubBinding | pc#799 | ✅ merged | Per-workspace GitHub repo + PAT routing |
| commitSemanticViewToGitHub orchestrator | pc#800 | ✅ merged | Branch → commit → PR → optional auto-merge |
| Eval harness (20 deterministic tests) | pc#801 | ✅ merged | Locks Properties 1–4 in CI |
| LocalStack in compose | pc#802 | ✅ merged | Local stack actually round-trips Secrets/SSM/S3 |
| Token redaction regex extension | pc#803 | ✅ merged | `ghu_*`, `?access_token=`, `&pat=` no longer leak in logs |
| GHE proxy selection-set drift | bb#520 | ✅ merged | dbt-agent gets typed `errorCode` + `httpStatus` |
| Per-customer repo provisioning | brighthive-scripts#3 | ✅ merged | One command sets up the entire trial customer |
| Local seed (7 unseeded OGM types + 42 nodes) | pc#797 | ✅ merged | Webapp surfaces render |
| Spec | pc#798 | open | Source of truth — sign off §10 if shipping changes |

**No webapp UI work landed this session.** wa#1124 (canvas + YAML editor) is already on develop; the user-facing "Save & Open PR" button (BH-616) is filed but not implemented. Day 1 demo runs against the GraphQL API directly until BH-616 ships.

## Demo Snowflake account

| Field | Value |
|---|---|
| Account | `bfddsko-dua97555` |
| Database | `LONGAEVA_POC` |
| Warehouse | `POC_WH` |
| Role | `LONGAEVA_POC_ROLE` |
| User | `KURICHINCA` |
| Schemas | `BRONZE / SILVER / GOLD / SEMANTIC / REF / MONITORING / GC_SANDBOX` |

(Per session-handoff §"Real-Snowflake function-tier verification".)

## Pre-flight checklist (run morning of Day 1)

Run these in order. **All ✅ = green-light demo. Any ✗ = stop, route to §"If something breaks".**

### 1. Confirm staging is fresh

```bash
cd ~/iccha/brighthive/brighthive-platform-core
gh pr list --base develop --state open --search "drchinca" --json number,title
# Expected: 0 open PRs from this session (all 5 merged: 797, 799, 800, 801, 802, 803)
```

```bash
gh release list --repo brighthive/brighthive-platform-core --limit 3
# Expected: a pre-release tagging staging within the last 24h that includes pc#797..803
```

If the staging release predates the merge train: deploy is stale, ops/SRE owes a redeploy → **stop**.

### 2. Verify the local stack works (smoke)

```bash
make stack-up && make seed-localstack
NAME=kuri make local
```

Expect: `✓ platform-core running at http://localhost:4040/graphql` within ~30s.

```bash
TOKEN=$(bash setup/scripts/generate-local-token.sh admin | sed -n '/^Token/,/^Usage/{/^Token/d;/^$/d;/^Usage/d;p}')
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST -d '{"query":"{ currentUser { id firstName emailAddress } }"}' \
  http://localhost:4040/graphql | jq .
```

Expect:
```json
{"data":{"currentUser":{"id":"a06fd80c-...","firstName":"Sarah","emailAddress":"admin@local.brighthive.io"}}}
```

If that fails: tail `/tmp/bh-platform-core.log`, check Neo4j (`docker logs brighthive-neo4j`), check LocalStack (`docker logs brighthive-localstack`). Most common failure mode: the neo4j container is from a previous run with stale data — run `docker rm -f brighthive-neo4j` and retry.

### 3. Verify the four demo mutations work locally

Run the **Live demo script** below against `http://localhost:4040/graphql` first. If all four return `success: true` against the local stack, staging will work too.

### 4. Confirm the customer repo exists

```bash
gh repo view brighthive/longaeva-semantic-views --json name,visibility,defaultBranchRef \
  --jq '{name, visibility, default: .defaultBranchRef.name}'
# Expected: { "name": "longaeva-semantic-views", "visibility": "PRIVATE", "default": "main" }
```

If absent: run

```bash
WORKSPACE_ID=<staging-uuid> WORKSPACE_SLUG=longaeva JWT=<staging-jwt> \
  ../brighthive-scripts/scripts/provision_semantic_views_repo.sh
```

This creates the repo, seeds README + CODEOWNERS + `.gitignore`, mints a PAT, and registers the binding via `setWorkspaceGitHubBinding`. **Idempotent** — safe to re-run.

### 5. Confirm the binding is registered for the staging customer workspace

```bash
STAGING_TOKEN=...   # Cognito token for the staging customer admin user
curl -s -H "Authorization: Bearer $STAGING_TOKEN" -H "Content-Type: application/json" \
  -X POST \
  -d '{"query":"query G($wsId: ID!) { getWorkspaceGitHubBinding(workspaceId: $wsId) { ownerSlug repoSlug defaultBranch hasStoredPat } }","variables":{"wsId":"<staging-ws-uuid>"}}' \
  https://api.staging.brighthive.net/graphql | jq .
```

Expect: `{"hasStoredPat": true}`. If `false`, re-run the provisioning script with `JWT` pointing at staging.

### 6. Snowflake reachability

```bash
snow connection test -c brighthive
# Expected: "✓ Status report:  KURICHINCA / LONGAEVA_POC_ROLE / POC_WH / LONGAEVA_POC"
```

Per session-handoff: this round-trips today. If it fails on demo morning, it's a credential or network issue; route to Ahmed/Marwan to refresh.

## Live demo script

Variables to substitute before running:
- `JWT` — staging or prod customer admin Cognito token
- `WS_ID` — customer workspace UUID
- `ASSET_ID` — DataAsset UUID for the table you're demoing (recommend a SILVER table the customer recognizes, e.g. `STG_SECURITY_PRICES`)
- `WAREHOUSE_ID` — the WarehouseServiceNode UUID for their Snowflake account

### Step 1 — Author the YAML (UI walkthrough OR direct mutation)

If demoing through the existing YAML editor (wa#1124): open the DataAsset's "Semantic View" tab and paste the YAML. The editor calls `upsertSemanticView` on save.

If demoing through the API (no UI):

```bash
YAML='name: stg_security_prices
version: 1
tables:
  - name: stg_security_prices
    base_table:
      database: LONGAEVA_POC
      schema: SILVER
      table: STG_SECURITY_PRICES
metrics:
  - name: total_instruments
    expr: COUNT(DISTINCT instrument_id)
  - name: avg_close_price
    expr: AVG(close_price_usd)
dimensions:
  - name: trade_date
    expr: trade_date
  - name: asset_class
    expr: asset_class_code'
JSON=$(printf '%s' "$YAML" | jq -Rsa .)

curl -s -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -X POST -d "{
    \"query\": \"mutation U(\$i: UpsertSemanticViewInput!) { upsertSemanticView(input: \$i) { yamlHash } }\",
    \"variables\": {\"i\": {
      \"workspaceId\": \"$WS_ID\",
      \"assetId\": \"$ASSET_ID\",
      \"yaml\": $JSON,
      \"comment\": \"Live demo — Day 1\"
    }}
  }" \
  https://api.staging.brighthive.net/graphql | jq .
```

Expect: `{"yamlHash": "<sha256>"}`.

### Step 2 — Validate against Snowflake

```bash
curl -s -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -X POST -d "{
    \"query\": \"mutation V(\$i: ValidateSemanticViewAgainstSnowflakeInput!) { validateSemanticViewAgainstSnowflake(input: \$i) { valid structuralErrors snowflakeReachable } }\",
    \"variables\": {\"i\": {
      \"workspaceId\": \"$WS_ID\",
      \"assetId\": \"$ASSET_ID\",
      \"yaml\": $JSON,
      \"warehouseId\": \"$WAREHOUSE_ID\",
      \"database\": \"LONGAEVA_POC\",
      \"schema\": \"SILVER\",
      \"viewName\": \"stg_security_prices_v\"
    }}
  }" \
  https://api.staging.brighthive.net/graphql | jq .
```

Expect:
- `snowflakeReachable: true`
- `valid: true`
- `structuralErrors: []`

If `snowflakeReachable: false`: warehouse credentials missing (BH-549 territory) or the role doesn't have grant on `agents.invoke`. **Route to §"If something breaks" item B.**

If `valid: false` with structural errors: the YAML is wrong — fix and retry. The demo recovers gracefully ("see, structural validation caught the missing column reference before we wasted a Snowflake round-trip").

### Step 3 — Open the PR

```bash
curl -s -H "Authorization: Bearer $JWT" -H "Content-Type: application/json" \
  -X POST -d "{
    \"query\": \"mutation C(\$i: CommitSemanticViewToGitHubInput!) { commitSemanticViewToGitHub(input: \$i) { success errorCode prNumber prUrl branchName commitSha filePath yamlHash } }\",
    \"variables\": {\"i\": {
      \"workspaceId\": \"$WS_ID\",
      \"assetId\": \"$ASSET_ID\",
      \"prDescription\": \"Demo PR — semantic view for STG_SECURITY_PRICES\"
    }}
  }" \
  https://api.staging.brighthive.net/graphql | jq .
```

Expect:
```json
{
  "success": true,
  "errorCode": null,
  "prNumber": <N>,
  "prUrl": "https://github.com/brighthive/longaeva-semantic-views/pull/<N>",
  "branchName": "semantic-view/stg_security_prices/<yyyymmddHHMM>",
  "commitSha": "<sha>",
  "filePath": "semantic-views/stg_security_prices.yaml",
  "yamlHash": "<sha256>"
}
```

**Open the prUrl in a browser tab.** That's the demo money shot — a real GitHub PR with the customer's YAML, ready for review.

### Step 4 — (Optional) Auto-merge

If the customer wants to see the merge complete live, set `autoMerge: true`:

```bash
# Same mutation as Step 3, but with autoMerge: true on the input
"autoMerge": true
```

Expected: response also includes `mergeCommitSha: "<sha>"` and `mergeBlocked: false`.

If `mergeBlocked: true`: the repo has required reviews configured. Open the PR URL and merge manually — the demo still works, you just don't get the live-merge wow factor.

## What "fully working" looks like in DataAsset state

After Step 3 succeeds, the DataAsset in Neo4j carries:

```cypher
MATCH (d:DataAssetNode {id: $ASSET_ID})
RETURN d.name,
       d.semanticViewYaml,
       d.semanticViewYamlHash,
       d.semanticViewLastDeployStatus,    // "PR_OPENED" or "MERGED"
       d.semanticViewLastDeployError,     // null
       d.semanticViewDeployedAt,
       d.semanticViewDeployedBy
```

The webapp's `SemanticViewDeploymentBadge` reads these fields directly. After BH-616 ships, the same flow runs from a single button click in the editor.

## If something breaks

### A. The mutation returns `errorCode: "BINDING_NOT_CONFIGURED"`

The workspace doesn't have a `WorkspaceGitHubBindingNode`. Run the provisioning script (Pre-flight #4) and retry.

### B. Snowflake validation returns `snowflakeReachable: false`

Two causes:

1. **No warehouse credentials in Secrets Manager.** Check:
   ```bash
   aws --profile brighthive-staging secretsmanager get-secret-value \
     --secret-id workspace_secret_store/$WS_ID --query SecretString | \
     jq -r . | jq '.snowflake_warehouses'
   ```
   If empty or missing the `$WAREHOUSE_ID` key: run `upsertWarehouseConfig` to register them. The customer should be able to do this from the warehouse settings UI; if not, fall back to the GraphQL mutation directly.

2. **Role lacks `agents.invoke` grant on the Snowflake account.** Per session-handoff GC-9 line: this grant has to be issued on the Longaeva side. Route to Grant.

### C. `commitSemanticViewToGitHub` returns `errorCode: "PAT_NOT_FOUND"` (httpStatus 401)

The PAT in `workspace_secret_store/$WS_ID/services/github/proxy_pat` is missing or invalid. Run the provisioning script with `ROTATE_PAT=1` to mint and register a fresh PAT.

### D. `errorCode: "BRANCH_CREATE_FAILED"` with `httpStatus: 422`

GitHub responds 422 when the branch already exists. The orchestrator's idempotent retry (spec I-6) automatically falls back to a `-retry` suffix; if you see this surface to the response, the retry **also** failed — usually means the repo is in a weird state. Open the repo in the browser and check whether someone has been manually creating branches. As a recovery: pass an explicit `branchName` with a unique suffix in the mutation input.

### E. `errorCode: "PR_CREATE_FAILED"` with `httpStatus: 403`

PAT scope issue — PAT doesn't have `pull_requests:write` on the repo. Re-mint with the correct scopes via the provisioning script.

### F. The editor in the webapp doesn't show a deploy badge

`SemanticViewDeploymentBadge` reads `DataAsset.semanticViewLastDeployStatus`. If that field is null after the demo: either the orchestrator didn't reach step 9 (look at `errorCode`/`httpStatus`), or the webapp is reading a stale Apollo cache. Hard-refresh the browser tab.

### G. A PAT shows up in a log line anywhere

This should be impossible after pc#803 — but if it happens, **the demo stops immediately**, the PAT is rotated via `gh` CLI, the binding is re-registered with the new PAT, and the leak is filed under BH-526. Property 1 of the spec is non-negotiable.

## Talking points for the demo

The customer is watching. These are the things to actually say:

1. **"Snowflake stays the source of truth."** The semantic view YAML is *describing* what's already in Snowflake; we don't move data. The validation step proves it.

2. **"Every change is a Git PR."** No silent updates. The customer's existing review process applies. Auto-merge is opt-in, not on by default.

3. **"PATs never leave Secrets Manager."** Even our own logs don't see them. (You can show the redaction tests if anyone digs in: `tests/unit/scrub-bearer.test.ts` — 20 cases.)

4. **"This loop runs on a laptop with `make stack-up && make local`."** Reproducibility = trust. We can rebuild from scratch in front of them if asked.

5. **"Workspace admins control everything; agents do nothing destructive without consent."** Auth hierarchy means a dbt agent that wants to push needs the binding *and* the right role *and* a real PAT, all wired by the workspace admin.

## Don't say

- "We do Snowflake migrations" — no, we generate semantic views over existing tables.
- "PR auto-merges by default" — only if the operator opts in per call.
- "It works on customer GHE today" — the trial uses our `github.com/brighthive` repo. Customer GHE is a post-trial overlay.
- "All 109 mutations are tested" — only the Longaeva-delta 23 are walked end-to-end (per `MUTATIONS_INVENTORY.md`); the rest stay `[ ]` until BH-526 follow-ups.

## Post-demo checklist

| Item | Owner |
|---|---|
| Capture screen recording of the live PR open | demo driver |
| File any rough edges as Jira tickets under BH-526 | demo driver |
| Update `clients/trials/longaeva/scorecard.md` with GC-6 ✅ if it lands cleanly | drchinca |
| Slack `#internal-longaeva` with the PR URL + outcome | demo driver |
| Send Grant a thank-you note with the PR URL | sales |

## Ownership

- **Demo driver**: Kuri (drchinca) primary, Marwan secondary
- **On-call for breaks during the demo**: Ahmed (infra), Harbour (UI)
- **Customer-facing comms**: Grant
- **Escalation if Snowflake-side breaks**: Grant → Longaeva data-eng

## Glossary

### Demo concepts

- **GC-6** — Golden Case 6 from BH-601: "Semantic view ≥90% coverage." This runbook covers the single-table demo path. Multi-table is GC-6 ⭐ and depends on bb#489 (orphaned, see session-handoff #6).
- **GC-10** — Golden Case 10: "End-to-end Silver→PR." S6 + S7 stages auto-flip green when pc#793 staging deploys; until then they're strict-xfailed.
- **Single-table demo path** — what we're actually selling on Day 1: one DataAsset, one YAML, one Snowflake validation, one PR. Defensible without bb#489.
- **Schema-wide** — multi-table semantic view that auto-infers joins/entities across an entire SILVER schema. **Not** what we're demoing on Day 1; framing this as schema-wide to the customer is a credibility risk.

### Platform pieces

- **PAT** — GitHub personal access token. For the trial, a fine-scoped PAT minted via `gh auth token` and stored in `workspace_secret_store/{ws}/services/github/proxy_pat`. The PAT never leaves Secrets Manager via API or logs (see Property 1).
- **Binding** — `WorkspaceGitHubBindingNode` in Neo4j — routing metadata (host, ownerSlug, repoSlug, defaultBranch, yamlRootPath, prTitleTemplate) pointing the workspace at a specific GitHub repo. One per workspace. Created via `setWorkspaceGitHubBinding` (BH-613).
- **Orchestrator** — `commitSemanticViewToGitHub` mutation (BH-614). The 9-step pipeline that takes the saved YAML and turns it into a real GitHub PR: binding lookup → asset YAML read → branch/path slugify → PAT read → base ref SHA → branch create → file commit → PR open → optional auto-merge.
- **Idempotent retry** — when `createGitHubBranch` returns 422 ("Reference already exists"), the orchestrator retries once with a `-retry` suffix on the branch name. Spec invariant I-6.
- **LocalStack** — AWS service emulator we run in `docker-compose.local.yml`. Covers Secrets Manager, S3, SSM, STS on community tier. Cognito-IDP is Pro-tier only and stays mocked-out.
- **`workspace_secret_store/{workspace_uuid}`** — Secrets Manager prefix; pc writes (binding PAT + warehouse creds), cdk reads (during ingestion stack runs), brightbot reads (during dbt-agent runs).
- **`LONGAEVA_POC`** — the live Snowflake account/database the trial runs against. `bfddsko-dua97555 / KURICHINCA / LONGAEVA_POC_ROLE / POC_WH / LONGAEVA_POC`.
- **`LONGAEVA_AGENT_ROLE`** — the read-only Snowflake role agents should use during the trial (vs. KURICHINCA admin). Per GC-14 sandbox parity. Currently a Day-1 outstanding (humans-only).

### errorCode taxonomy

Every step the orchestrator runs returns a typed `errorCode` on failure. The runbook §"If something breaks" is keyed on these:

- **`BINDING_NOT_CONFIGURED`** — workspace has no `WorkspaceGitHubBindingNode`. Fix: run `provision_semantic_views_repo.sh`.
- **`ASSET_NOT_FOUND`** — DataAsset UUID doesn't resolve in the workspace. Fix: re-confirm the asset ID.
- **`YAML_EMPTY`** — DataAsset has no `semanticViewYaml`. Fix: call `upsertSemanticView` first.
- **`PAT_NOT_FOUND`** (httpStatus 401) — binding exists but no PAT in Secrets Manager. Fix: re-run provisioning with `ROTATE_PAT=1`.
- **`BAD_BRANCH_NAME` / `BAD_FILE_PATH`** — input failed validation regex. Fix: use a clean branch name or trust the default.
- **`BASE_REF_NOT_FOUND`** — `defaultBranch` on the binding doesn't exist on the remote repo. Fix: update binding with the correct branch.
- **`BRANCH_CREATE_FAILED`** (httpStatus 422 means already exists; auto-retry kicks in. Other statuses surface here untouched.)
- **`COMMIT_FAILED`** — typically 422 if the file path is invalid for some reason; check `httpStatus`.
- **`PR_CREATE_FAILED`** (httpStatus 403 typically means PAT lacks `pull_requests:write` scope — re-mint).
- **`mergeBlocked: true`** — PR opened successfully but auto-merge couldn't proceed (required reviews / branch protection). Surface this to the demo audience as a feature, not a bug.

### Spec properties

- **Property 1** — "PAT never leaves Secrets Manager." Test-locked at `tests/unit/scrub-bearer.test.ts` (20 tests) + `tests/unit/semantic-view/commit-orchestrator.test.ts` (PAT-redaction subset).
- **Property 2** — "yamlHash continuity from upsert→commit." `committedYamlHash == DataAsset.semanticViewYamlHash`. Test-locked in the orchestrator suite. The dry-run script also asserts this inline.
- **Property 4** — "Failure surface is observable." Every step returns verbatim `errorCode` + `httpStatus` with a step-name prefix in `error`. Locked by 8 tests in the orchestrator suite.

### Tooling

- **`make verify`** — assumes stack + server running. Generates JWT, ensures binding registered, runs `trial_day_1_dry_run.sh` with cleanup. ~30s.
- **`make verify-pristine`** — cold start. `stack-up` → `seed-localstack` → `seed-neo4j` → `local` → `verify`. Use this on a fresh laptop.
- **`trial_day_1_dry_run.sh`** — the script `make verify` calls. Lives in sibling `brighthive-scripts/scripts/`. Standalone, env-driven, reusable against any environment.
- **`provision_semantic_views_repo.sh`** — one-command per-customer onboarding. Creates the GitHub repo, mints the PAT, registers the binding via `setWorkspaceGitHubBinding`. Idempotent.
- **`SKIP_DEV_SERVER_CHECK=1`** — env var that lets `tests/setup.ts` skip the dev-server gate for pure unit tests. Used by the CI workflow and by humans running unit tests locally without spinning up platform-core.
