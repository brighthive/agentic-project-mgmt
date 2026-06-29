# Staging Session Learnings — ecosystem map, creds, hotfix flow, testing

> Working notes distilled from live bug-hunting + hotfix sessions against **staging**.
> Read this BEFORE a staging session so you don't re-derive the environment, re-discover
> where creds live, or repeat the traps below. Update it when reality changes.

## TL;DR (the things that cost the most time to learn)

1. **Two agents can share a repo only via separate clones.** Each agent works in its own
   checkout (`<repo>-loop-session`, `<repo>-session-2`), shares only the GitHub remote.
   NEVER run `git checkout`/`commit` in another agent's clone — branch switches rewrite the
   shared working tree and corrupt the index.
2. **Staging tokens expire fast (~1h for id tokens).** Mint fresh ones with `/tmp/mint_token.py`
   (Cognito USER_PASSWORD_AUTH). Re-mint before any multi-minute batch.
3. **The local IAM user (`brightagent-aws`) is deliberately scoped** — it can't list/read admin
   secrets. For those, use **AWS SSO** profile `brighthive-staging` (AdministratorAccess).
4. **The OGM endpoint wants the raw token WITHOUT `Bearer ` prefix.** Every other API wants
   `Bearer <token>`. This one trap cost an hour ("Unauthorized" on a valid admin token).
5. **`.env`/`.env_staging` secrets drift** — the local `BH_PASSWORD`/`OGM_PASSWORD` are stale
   9-char values. The REAL ones live in AWS Secrets Manager (read via SSO). Don't trust env files
   for admin creds.

## Ecosystem map (which repo owns what)

| Concern | Repo | Notes |
|---|---|---|
| AI agents (LangGraph deep_agent + subagents), MCP server | `brightbot` | FastMCP server IS brightbot; tools run in-process with the graphs |
| GraphQL API + Neo4j OGM (data plane) | `brighthive-platform-core` | Apollo server; OGM (direct Neo4j) at `/ogm`, public API at `/` |
| React frontend | `brighthive-webapp` | catalog Schemas page, Projects UI, governance |
| Scheduler / EventBridge / Step Functions / Lambda | `brighthive-data-organization-cdk` | scheduled-agent dispatcher lambdas live in **platform-core** `lambdas/scheduled_agent_dispatcher/` |
| Sprint/Jira/release + vault CLIs + these docs | `agentic-project-mgmt` | dynamo-vault, aws-secrets-vault, lastpass-vault CLIs |
| Architecture / env / infra runbooks | `platform-saas-ai-context` | the "what/where" reference; ENVIRONMENTS.md, AWS_ACCOUNTS.md |

### Two "schema" concepts — do not conflate (cost real confusion this session)
- **`OMDSchemaTable`** — a real warehouse table's columns, from OpenMetadata, bound to a `DataAsset` (`DataAsset.fields`).
- **`StandaloneSchemaWorkspace`** — user-authored JSON Schema *contracts* on the catalog Schemas page (`Query.schemas` → `TargetSchema`, `SchemaType {INPUT|OUTPUT}`). NOT bound to a table; meant to gate input/output. Today: created but unenforced.

## Credentials & env — where everything actually lives

| Need | Source | How |
|---|---|---|
| Staging **user** token (kuri) | LastPass "BH Staging - Kuri" → Cognito | `/tmp/mint_token.py` (USER_POOL_CLIENT_ID from `brightbot/.env_staging`) |
| Staging **admin/SystemAdmin** token (OGM, member ops) | AWS Secrets Manager `staging/staging-platform-cognito/credentials` (`SYSTEM_ADMIN_USERNAME`/`PASSWORD`) | read via SSO `--profile brighthive-staging`, then Cognito USER_PASSWORD_AUTH |
| AWS admin (read any staging secret, S3, etc.) | **SSO** `brighthive-staging` (AdministratorAccess) | `aws ... --profile brighthive-staging`; `aws configure list-profiles` shows all |
| Scoped programmatic AWS (S3 cross-account assume) | `brightbot/.env_staging` `AWS_ACCESS_KEY_ID/SECRET` = IAM `brightagent-aws` | can assume per-workspace cross-account roles; CANNOT list/read admin secrets |
| Snowflake (Longaeva) | `workspace_secret_store/<ws>` → `snowflake_warehouses.<ws>` | get via SSO Secrets Manager; account BFDDSKO-DUA97555, db LONGAEVA_POC |
| Per-workspace S3 filesystem + cross-account role | `workspace_secret_store/<ws>` → `services.bedrock.{s3_filesystem_name, bedrock_cross_account_role_arn}` | demo ws (1c7cb12e) has it; Longaeva (4d7ffd13) does NOT (BH-773) |

### Key endpoints / values
- Public GraphQL: `https://api.staging.brighthive.net/` — `Authorization: Bearer <token>`. **Introspection DISABLED** (Apollo NODE_ENV=production rejects `__schema`; this is BH-771).
- OGM (direct Neo4j): `https://api.staging.brighthive.net/ogm` — `Authorization: <token>` (**NO** Bearer prefix), needs SystemAdmin token. `QualityRuleNodeWhere` DOES accept `applyOnSchedule`/`applyOnIngestion` (a stale code comment said otherwise).
- MCP: `https://brightagent-mcp.staging.brighthive.net/mcp` — Bearer + `Mcp-Session-Id` + `X-Workspace-Id`; init→notifications/initialized→tools/call.
- Workspaces: Longaeva data = `4d7ffd13-73d0-4f14-8f0e-63bfddceca7c`; demo (governance policies + working S3) = `1c7cb12e-6d1a-4922-98a8-cff4de70f24d`.

## Hotfix workflow — per repo

> Global rules still apply: branch from `develop`/`master`, draft PR, NEVER self-merge, reviewers
> `Marwan-Samih-Brighthive,sherbiny-bh,Nano-233,matthewgee` + assignee `drchinca`.

### `brighthive-platform-core` & `agentic-project-mgmt` — hotfixes that target `main`/`master`
- These repos' protected base is **`master`** (agentic-pm) / `develop`→`staging`→`main` (platform-core).
- Branch from the base you'll PR into. For a genuine hotfix to live: branch from `master`/`main`,
  fix, PR back to that base. Do NOT branch from a stale feature branch.
- agentic-pm is docs/PM — most "fixes" are doc/spec PRs to `master`. Low CI risk.
- platform-core deploys via the git-flow chain (develop→staging→main); a hotfix that must hit
  staging fast is cherry-picked, never a backward merge (see git-workflow rule).

### `brightbot` — hotfixes target `develop`
- Branch from `develop`, fix, draft PR to `develop`. LangGraph Cloud `build_on_push` auto-deploys
  on merge to the deployed branch.
- File-size hook blocks edits to any file >1300 lines. `quality_tools.py` is ~1353 lines —
  **edits there are BLOCKED until it's split** (BH-767/769/778 are all gated behind this split).
- Many tools do local (in-function) imports — patch them at their SOURCE module in tests, not on
  the tool's module.

### Deploy reality
- Staging IS the live env for PoCs (Longaeva). "Live on staging" = live; don't hedge.
- Deploys go via GitHub release tags / merge to the deployed branch, NOT laptop cdk.

## Testing — what works

- **In-process agent runs** (fastest, full state visibility): `deep_agent_graph.ainvoke(BBState(**...))`
  with `session_info = json.dumps({workspace_id, token, user_id})`. Helpers `_initial_bbstate` +
  `_last_assistant_text` in `brightbot/mcp/tools/analyst_ask.py`. Run with
  `uv run --env-file .env_staging python <harness>` from the brightbot clone.
- **Local S3 trap**: in-process runs need a per-workspace S3 filesystem. Longaeva has none → scratch
  writes fail locally even though the warehouse query succeeded. Either use the demo ws (has S3) for
  S3-needing probes, or run financial-data probes via the deployed `analyst_ask` MCP. Always confirm
  an S3-failure finding against DEPLOYED staging before ticketing it as a product bug.
- **Use curl, not urllib**, for MCP/HTTP probes — urllib hits `CERTIFICATE_VERIFY_FAILED` under pyenv.
- **MCP sessions expire** — re-init (initialize → notifications/initialized) per batch.
- **Long agent calls** exceed the 90s sync cap → use `analyst_ask_run_async` + `analyst_ask_poll(run_id)`.
- **Ground-truth numeric answers** against Snowflake directly (creds from workspace_secret_store) before
  judging the agent — don't trust the agent's number as the oracle.

## Recurring anti-pattern found across the platform
**"Declared metadata is created but never made operational."** Governance policies, StandaloneSchemaWorkspace
contracts, the glossary, project targetSchemas, and `applyOnSchedule` flags were all stored + displayed
but never injected into agent reasoning / enforced at execution. When auditing a "feature", always check:
does anything READ it and ACT, or is it write-only metadata? (BH-766/767/768/769/775/779.)

---

## Incident 2026-06-29 — Demo data catalog empty on staging (OM workspace scoping, BH-646)

**Symptom (reported by Sherbiny):** "data catalog and files upload not working on staging."

**Root cause (catalog):** the deployed OM workspace-scoping (`#881`, on `develop`+`staging`) decides
which OM tables a workspace sees by **OM team ownership** — a service belongs to a workspace iff its
`owners[]` contains a team whose `name == workspaceId`, fail-closed (no owned service → empty catalog).
Staging OM holds exactly **one** service, `"Staging Demo Workspace"` (legacy human name, 148 Redshift
tables), owned by team `setup`. No team named after the Demo workspace exists → Demo's catalog scopes
to **zero tables**. Not a code crash — a data-attribution mismatch the fail-closed filter surfaces.

**"File upload" is a separate path — not this bug.** Onboarding (`onboardDataAssetToWorkspace` →
presigned S3 → `updateDataAssetCatalogCache`) never calls `getAllDataAssets`. Investigate uploads
independently (presigned S3 / permissions / DynamoDB account lookup); don't fold it into BH-646.

**The decision:** move scoping off OM teams to the **canonical service name**
(`<workspaceId>_<provider>_ingestion`), which already self-describes ownership and is what the webhook
resolver parses — one nomenclature, one source of truth. See `platform-saas-ai-context` **ADR-011** and
`brighthive-platform-core` PR #948 (`om-tenant-scope.ts` → `om-workspace-scope.ts`). The code change is
**independent** of the staging unbreak below: the legacy-named service resolves to no workspace under
*either* model, so it must be re-registered canonically regardless.

### The ID tangle (why re-registration is NOT a one-liner) — verified live 2026-06-29

Three identifiers must agree for a workspace to see its catalog, and on staging Demo they don't:

| Thing | Value |
|---|---|
| Demo workspace uuid | `1c7cb12e-6d1a-4922-98a8-cff4de70f24d` (Neo4j name: "Brighthive Demo Environment") |
| Staging Neo4j workspaces (only 2) | Demo `1c7cb12e-…` + OneTen `4d7ffd13-…` |
| OM service (the only one) | `"Staging Demo Workspace"` — legacy name, owner team `setup`, connects as Redshift user `admin`, `schemaFilterPattern includes ^database_.*` → pulls 4 schemas (`database_340752819582`=124 real + `dbt_hchinca`/`public`/`dbt_ctan` dev sandboxes) |
| Demo Neo4j `WarehouseServiceNode`s | **4** — incl. `2edd100d-…` "Demo workspace Redshift" (schema `database_340752819582`, the match) + `ca16037f-…` |
| Secret-store key with COMPLETE Redshift creds | `workspace_secret_store/1c7cb12e-…` → `warehouses[1c7cb12e-…]` (the **workspace** uuid, user `redshift_readonly_user`, db `workspace-database`) |
| Secret-store block for `2edd100d-…` | present but **incomplete** (blank `apiEndpoint`/`accountId`) |

`upsertWarehouseServiceConfig(workspaceId, warehouseId)` resolves the connection by `warehouseId`
against BOTH the Neo4j node list (`find(ws => ws.id === warehouseId)`) and the secret-store key. The
Neo4j node id, the secret-store key, and the OM service's live connection are **three different things**
on Demo — a blind re-register either throws (no matching node) or registers an incomplete connection.
**Resolve the intended (Neo4j warehouse-node ↔ secret-store key) pair before re-registering.**

### Remediation runbook (additive, reversible-by-rescan) — NOT yet executed

> Decision (2026-06-29): re-register canonically (not revert, not assign-team). Staging only this round;
> prod handled via the gate below. Held pending resolution of the ID tangle above.

1. **Read-only audit first:** `brighthive-platform-core/scripts/audit-om-service-workspaces.ts` against
   staging OM → confirms one ORPHAN (`Staging Demo Workspace`, 148 tables).
2. **Pick the right warehouse pair:** decide which Neo4j `WarehouseServiceNode` + secret-store key holds
   the correct Demo Redshift connection (likely the `1c7cb12e-…` secret block; confirm the Neo4j node it
   should bind to). Do NOT proceed until this is unambiguous.
3. **Re-register (additive, NOT delete+recreate):** call `upsertWarehouseConfigAsAdmin` (admin) with the
   resolved `warehouseId` → registers `1c7cb12e-…_redshift_ingestion` + triggers AutoPilot. OM 1.8.9 has
   **no non-destructive rename**, so this creates a *second*, canonical service beside the legacy one.
4. **Wait for the AutoPilot scan (~5–15 min)** — verifying before it finishes shows a false-empty catalog.
5. **`syncDataAssets(workspaceId=1c7cb12e-…)`** to backfill DataAssetNodes from the now-in-scope service.
6. **Cleanup LAST (optional):** hard-delete the legacy `"Staging Demo Workspace"` service via OM REST and
   purge orphaned DataAssetNodes (FQN prefix `Staging Demo Workspace.*`). Reversible by rescan.

**Hazard:** re-registration mints NEW OM table UUIDs → existing `DataAssetNode.openMetadataTableId`
links go stale; `syncDataAssets` creates new nodes (name/FQN fallback matchers may relink some).

### Prod-deploy gate (MANDATORY before BH-646 scoping reaches `main`)

`#881` is already on `develop`+`staging` and flows to `main` on the next promotion. Both the team model
AND name-based scoping fail-closed → **any prod service that is legacy-named (or not owned by a
workspace-named team) makes that customer's catalog go empty on deploy.**

1. Run the read-only audit against **prod** OM before the `staging→main` PR:
   ```
   OMD_API_URL=https://openmetadata.app.brighthive.net/api/v1 \
   OMD_TOKEN=<prod ingestion-bot JWT> \
   npx ts-node scripts/audit-om-service-workspaces.ts
   ```
2. **Safe to deploy:** `orphan=0` (every prod service with tables is CANONICAL).
3. **Will break:** any ORPHAN-with-tables → each is a customer whose catalog will empty. Re-register each
   canonically (runbook above) BEFORE the deploy, or hold the PR.

Architecture detail + cloud-resource map: `platform-saas-ai-context/docs/architecture/SNOWFLAKE_OMD_INGESTION.md`
→ "Service ownership signal & ID mapping". Decision: ADR-011 in that repo's `docs/decisions/decisions.md`.
