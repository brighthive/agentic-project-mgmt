# LangSmith Deployment Snapshots — Protocol

> **Source of truth** for the shape (secret names, env vars, revisions) of every LangSmith / LangGraph Cloud deployment, per environment. Lives at [`langsmith-vault/`](../langsmith-vault/).

## The rule

**Never modify a LangSmith deployment's `secrets`, `env_vars`, or revision config without:**

1. A committed pre-change snapshot in `langsmith-vault/data/{env}/{name}.json` no older than 24h.
2. Explicit per-edit approval from Kuri or Sherbiny (see [`feedback_never_modify_env_vars`](../../.claude/memory/feedback_never_modify_env_vars.md)).
3. A read-modify-write PATCH that preserves the full array (see [`feedback_langsmith_secrets_patch_replaces`](../../.claude/memory/feedback_langsmith_secrets_patch_replaces.md)).
4. A post-change snapshot committed in the same PR. The diff IS the audit trail.

Skipping any of these is the incident, not a shortcut around it.

## Why

`PATCH /v2/deployments/{id}` with a partial `secrets` array **REPLACES** the full array. On 2026-06-18 this dropped 74 secrets on `brightagent-staging` to 1. The fact that we had no committed snapshot is what turned a 5-second mistake into a 1-hour recovery — and left three values unrecovered.

## Cadence

| Trigger | Action |
|---------|--------|
| Before any approved LangSmith mutation | `./cli/snapshot pull --name <deployment>` + commit |
| After any approved LangSmith mutation | `./cli/snapshot pull --name <deployment>` + commit in same PR |
| Nightly (CI) | `./cli/snapshot pull --all` + diff vs HEAD — alert if drift without PR |
| Quarterly | manual review of `data/index.md` — confirm we still own every listed deployment |

## Restoration playbook

If a deployment's secrets are wiped or corrupted:

1. **Read the last good snapshot**: `cat langsmith-vault/data/{env}/{name}.json` — gives you the exact list of secret names that must exist.
2. **Fetch each value** in order of trust:
   - `aws-secrets-vault/cli/secrets fetch <secret-name> --account {STAGE|PROD}` (canonical for shared infra creds)
   - `lastpass-vault/cli/secrets fetch <key>` (personal / vendor API keys)
   - Sibling `.env_*` files — last resort, often stale, mixed with dev creds.
3. **Reconstruct the full `secrets` array** and PATCH in one call. Never send a partial.
4. **Snapshot immediately** after restore and open a postmortem PR.

If a snapshot is older than the mutation that wiped state, treat the unrecoverable keys as a P0 — surface them in #incidents and ask Sherbiny / Kuri to re-issue from vendor.

## Source-of-truth chain

```
shape (key names + revisions)  → langsmith-vault/           ← THIS REPO
values for shared secrets      → aws-secrets-vault/         ← AWS Secrets Manager mirror
values for personal/vendor     → lastpass-vault/            ← LastPass mirror
last-resort cross-check        → ../brightbot/.env_*        ← stale, do not trust
```

Walk top-down. Never invert.

## What gets committed

- ✅ `langsmith-vault/data/{env}/{name}.json` — names, counts, revision IDs, graph aliases
- ✅ `langsmith-vault/data/index.md` — generated cross-env matrix
- ❌ Values — **never** committed. The vault tracks shape, not secrets.
