# LangSmith Deployment Vault

Source of truth for the **shape** (secret names, env vars, revisions) of every LangSmith / LangGraph Cloud deployment we own — per environment.

> Values are NOT committed. This vault tracks **which keys must exist** on each deployment so that we can detect when somebody (human or agent) drops, overwrites, or "re-adds by guessing" the secrets. Values live in AWS Secrets Manager and LastPass.

## Why this exists

On **2026-06-18** the LangSmith deployments API (`PATCH /v2/deployments/{id}`) silently REPLACED the entire `secrets` array on `brightagent-staging` when sent a partial payload. 74 secrets → 1 secret. Recovery took ~1h of cross-referencing AWS Secrets Manager + local `.env` + CloudFormation outputs, and three values (`WEBHOOK_SECRET`, `BRIGHTAGENT_CODE_INTERPRETER_TOOL_ID`, `BACKEND_S3_PREFIX`) could not be fully recovered.

This vault makes that incident a one-time event:

- **Pre-mutation**: snapshot is the diff target. Read it, modify the in-memory copy, PATCH the full reconstructed array.
- **Post-incident**: snapshot tells us exactly what keys to restore.
- **Drift detection**: nightly snapshot vs. last-committed = alarm if the deployment shape changes without a PR.

## Hard rules

1. **Never PATCH `secrets` without first reading the full array.** See [`feedback_langsmith_secrets_patch_replaces`](../../.claude/memory/feedback_langsmith_secrets_patch_replaces.md). PATCH replaces.
2. **Never modify LangSmith deployment env vars without an explicit per-edit approval from Kuri or Sherbiny.** See [`feedback_never_modify_env_vars`](../../.claude/memory/feedback_never_modify_env_vars.md).
3. **Snapshot before and after every approved change.** Commit both snapshots in the same PR — the diff IS the audit trail.
4. **If a snapshot exists and live state diverges, treat live as suspect.** Investigate before "correcting" the snapshot.

## Layout

```
langsmith-vault/
├── README.md              # this file
├── cli/
│   └── snapshot           # CLI: pull deployments + write snapshots
├── data/
│   ├── dev/               # brightagent-dev, brightbot-dev, ...
│   ├── staging/           # brightagent-staging, brightbot-staging, ...
│   ├── prod/              # brightagent-prod, brightbot-prod, ...
│   ├── main/              # any platform-account deployments
│   └── index.md           # generated: cross-env deployment matrix
└── lib/
    └── langsmith_client.py
```

Each snapshot file: `data/{env}/{deployment_name}.json`

```json
{
  "deployment_id": "...",
  "name": "brightagent-staging",
  "env": "staging",
  "snapshot_at": "2026-06-19T12:34:56Z",
  "secret_count": 74,
  "secret_names": ["ANTHROPIC_API_KEY", "AWS_REGION", "..."],
  "env_var_names": [...],
  "latest_revision_id": "...",
  "graph_aliases": {"superduper_agent": "brightagent"}
}
```

**Values are never written to git.** If you need to inspect a value, fetch from AWS Secrets Manager (`aws-secrets-vault/cli/secrets`) or LastPass (`lastpass-vault/cli/secrets`).

## Usage

```bash
cd langsmith-vault

# Snapshot every deployment (requires LANGCHAIN_API_KEY in env)
./cli/snapshot pull --all

# Snapshot one deployment by name
./cli/snapshot pull --name brightagent-staging

# Show diff vs. last-committed snapshot
./cli/snapshot diff --name brightagent-staging

# Regenerate index.md
./cli/snapshot index
```

## Source-of-truth chain

When restoring or comparing, walk the chain in order:

1. **Shape (key names + revisions)** — this vault (`langsmith-vault/data/{env}/*.json`)
2. **Values for secrets** — AWS Secrets Manager (`aws-secrets-vault/`), classified per environment
3. **Values for credentials / personal keys** — LastPass (`lastpass-vault/`)
4. **Last-resort cross-check** — sibling `.env_*` files in `brightbot/` / `brightagent-v2/` (often stale, dev-creds-mixed)

Never invert this order. `.env` files are the LEAST trusted source.
