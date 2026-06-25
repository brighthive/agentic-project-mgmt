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
