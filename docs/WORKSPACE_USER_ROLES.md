# Workspace User Roles — Operator Runbook

Promoting / demoting a user on a BrightHive workspace (ADMIN / COLLABORATOR / VIEWER / CONTRIBUTOR). Written after `2026-06-23` when figuring this out from scratch cost ~30 min.

## TL;DR (staging — copy / adapt for prod)

```bash
# 1. Fetch a SystemAdmin JWT (no need for human BH login)
RAW=$(aws secretsmanager get-secret-value \
  --profile brighthive-staging --region us-east-1 \
  --secret-id staging/staging-platform-cognito/credentials \
  --query SecretString --output text)
U=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['SYSTEM_ADMIN_USERNAME'])" "$RAW")
P=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['SYSTEM_ADMIN_PASSWORD'])" "$RAW")

TOK=$(curl -s -X POST https://api.staging.brighthive.net/ \
  -H 'Content-Type: application/json' \
  -d "{\"operationName\":\"login\",\"variables\":{\"input\":{\"username\":\"$U\",\"password\":\"$P\"}},\"query\":\"mutation login(\$input:LoginInput!){login(input:\$input){idToken success}}\"}" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['login']['idToken'])")

# 2. Find workspace UUID — see "Where workspaces live" below

# 3. List members + current roles
WS='<workspace-uuid>'
curl -s -X POST https://api.staging.brighthive.net/ \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOK" \
  -d "{\"query\":\"query(\$i:WorkspaceInput!){workspace(input:\$i){name members{id emailAddress workspaceRole}}}\",\"variables\":{\"i\":{\"workspaceId\":\"$WS\"}}}" \
  | python3 -m json.tool

# 4. Promote (newRole: ADMIN | COLLABORATOR | VIEWER | CONTRIBUTOR)
USER_ID='<cognito-sub-or-neo4j-user-id-they-are-the-same>'
PAYLOAD=$(python3 -c "
import json
print(json.dumps({
  'query':'mutation(\$i:UpdateRoleInput!){updateRole(input:\$i)}',
  'variables':{'i':{'userId':'$USER_ID','workspaceId':'$WS','newRole':'ADMIN'}}
}))")
curl -s -X POST https://api.staging.brighthive.net/ \
  -H 'Content-Type: application/json' -H "Authorization: Bearer $TOK" \
  -d "$PAYLOAD"
# expects: {"data":{"updateRole":true}}
```

For **prod**: profile `brighthive-production`, secret name `production/production-platform-cognito/credentials` (verify before running — never assume the prod secret name matches staging without checking), endpoint `https://api.brighthive.net/`. Prod role changes touch live client data — require explicit per-mutation user confirmation, never batch.

## Where workspaces live (search order)

1. **`../platform-saas-ai-context/docs/infrastructure/ENVIRONMENTS.md`** — named sandboxes (OneTen Workspace, Brighthive Demo Environment, etc.) with their UUIDs in one table. **Look here first.**
2. **`clients/trials/<slug>/overview.md`** — `workspace_id` field for any active client trial.
3. **GraphQL** — `currentUser { organization { workspaces { id name } } }` with a SystemAdmin token returns the lot.
4. **DynamoDB `AdminConfig`** — *last resort*. Only contains CDK-provisioned workspaces with dedicated AWS accounts (52 of 131 on staging). Sandbox / shared-infra workspaces are absent. Scanning here first is the classic time-waster.

## GraphQL pitfalls

- The `workspace()` query takes `WorkspaceInput!` with field **`workspaceId`** — not `id`. The error message ("Field `id` is not defined by type `WorkspaceInput`") is your hint.
- `updateRole` returns `Boolean!`. Caller must be `WORKSPACE_ADMIN` on the target workspace **or** a SystemAdmin (the `dev.test+system.admin.1@brighthive.io` account is SystemAdmin).
- Platform-core `user.id` == Cognito `sub`. No translation needed once you've grepped Cognito.

## Bash pitfalls

- **`UID` is a zsh read-only variable.** Assigning `UID=...` triggers `bad math expression: operator expected`. Use `USER_ID` or anything else.
- Embedding UUIDs (start with a digit) directly in `-d "...$VAR..."` payloads also tickles zsh's math parser. Build the JSON via `python3 -c "import json; print(json.dumps(...))"` and pass the rendered string.

## Finding users in Cognito

```bash
aws cognito-idp list-users \
  --user-pool-id us-east-1_EAYUbZPFk \
  --profile brighthive-staging --region us-east-1 \
  --filter 'given_name ^= "Ignacio"'
```

`Username` in Cognito = `user.id` in platform-core (Neo4j). Searches by `given_name` often return multiple matches (test users, deleted users, name collisions) — always present candidates to the operator before mutating.
