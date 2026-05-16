# BrightHive — New Engineering Leader Onboarding

> **Status (PR #1 / Phase 1 MVP)**: Layer 1 atomic primitives only. The full `make onboard` ceremony and `make localstack`/`make stagingstack` wrappers land in subsequent PRs. This document covers what works today.

This repo is the **agentic project management hub**. It also holds the onboarding bootstrap that pulls all BrightHive secrets to your laptop and materializes per-repo `.env` files so you can run the platform locally.

## What you need before starting

| Item | Where to get it |
|---|---|
| AWS SSO profiles configured | `aws configure sso` for each: `brighthive-main`, `brighthive-staging`, `brighthive-production` (see `~/.aws/config`). Ask your manager for the SSO start URL if you don't have it. |
| LastPass account on the BrightHive vault | `brew install lastpass-cli` (macOS), then `lpass login you@brighthive.io` |
| GitHub access to the `brighthive` org | SSH key added to your GitHub account, org membership confirmed |
| `python3` (3.11+) | `brew install python@3.13` |
| `aws` CLI | `brew install awscli` |
| `gh` CLI (optional, used in later PRs) | `brew install gh` |

## Step 1 — Clone this repo and fill in your `.env`

```bash
git clone git@github.com:brighthive/agentic-project-mgmt.git
cd agentic-project-mgmt

cp .env.example .env
$EDITOR .env   # fill in your AWS profile names, LastPass user, GitHub token
```

## Step 2 — Verify your credentials

```bash
make check-creds
```

You should see green ticks for `brighthive-main`, `brighthive-staging`, `brighthive-production`, and your LastPass session. Any red ✗ tells you exactly what to fix:

```bash
make refresh-aws        # runs `aws sso login --profile X` for each expired session
make refresh-lastpass   # runs `lpass login $LASTPASS_USER` if needed
```

`make check-creds` is **idempotent** — re-running it when everything is already valid completes in <2 seconds with all ticks.

## Step 3 — Pull cached vault secrets

```bash
make pull-secrets
```

This pulls AWS Secrets Manager values (main / staging / production) and the BrightHive LastPass vault into a local `./secrets/` directory (gitignored, never committed). It honors a 24-hour cache — re-running within that window skips with "cache fresh". Override with `FORCE=1`:

```bash
FORCE=1 make pull-secrets
```

## Step 4 — Materialize `brightbot/.env`

```bash
make env-brightbot-local
```

This reads `config/env-templates/brightbot-local.env.tmpl`, resolves every `{{ source.key }}` token against the cached vault data, and writes `../brightbot/.env`. It records a SHA-based audit trail in `.state/env/brightbot-local.meta` so subsequent runs can detect:

- **Nothing changed** → skip silently
- **You edited the file** → print diff and refuse to overwrite (use `FORCE=1` to overwrite)
- **An unmanaged `.env` was already there** → refuse to overwrite (use `ADOPT=1` to take ownership without changing the file, or `FORCE=1` to overwrite)

If the renderer encounters any unresolved `{{ source.key }}` token, it exits non-zero and lists which keys are missing — there is no silent empty substitution.

## Step 5 — Verify brightbot accepts the env

```bash
cd ../brightbot
python scripts/local_bootstrap.py
```

If brightbot starts without missing-env errors, the onboarding bootstrap worked.

## Step 6 — Check your overall state

```bash
make status
```

Shows you the age of every sentinel — AWS sessions, LastPass session, each secrets-cache pull, each materialized `.env`. Tells you at a glance what's stale.

## What's NOT here yet (coming in later PRs)

| Feature | Status | PR |
|---|---|---|
| `make local` / `make staging` / `make start` in each sibling repo (Layer 2) | Not yet | PR #4-5 |
| `make localstack` — bring up all services pointed at local LocalStack (Layer 3) | Not yet | PR #6 |
| `make stagingstack` — bring up all services pointed at Staging (Layer 3) | Not yet | PR #6 |
| `make onboard` — full ceremony for fresh-clone setup (Layer 4) | Not yet | PR #7 |
| Env templates for webapp, platform-core, slack-server | Not yet | PR #2-3 |
| Sibling clone automation (`make clone-siblings`) is in PR #1 — try it now |  ✓ | This PR |

For the design rationale and the full four-layer hierarchy, see [`docs/specs/onboarding-bootstrap.md`](docs/specs/onboarding-bootstrap.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `make check-aws` reports `session expired` | `make refresh-aws` — opens browser for SSO |
| `make pull-aws-secrets` prints "AccessDenied" | Your IAM role doesn't have `secretsmanager:GetSecretValue` on that account; talk to ops |
| `make env-brightbot-local` exits 1 with "unresolved tokens" | A LastPass entry or AWS secret is missing/renamed; either fix the template or fix the vault |
| `make env-brightbot-local` exits 3 with "Unmanaged file present" | Existing `.env` wasn't created by the bootstrap. Run `ADOPT=1 make env-brightbot-local` to take ownership (no overwrite) or `FORCE=1 make env-brightbot-local` to replace it. |
| Renderer complains about a missing template path | Run from the repo root (`cd agentic-project-mgmt`) — paths are relative to it |

## See also

- [`docs/specs/onboarding-bootstrap.md`](docs/specs/onboarding-bootstrap.md) — full four-layer spec
- [`config/siblings.txt`](config/siblings.txt) — sibling repo list (mark optional with trailing `?`)
- [`config/env-templates/`](config/env-templates/) — per-repo per-env templates
