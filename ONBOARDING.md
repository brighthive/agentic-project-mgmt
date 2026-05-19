# BrightHive — New Engineering Leader Onboarding

> **If you're using Claude Code:** just say **"set me up"** and Claude will walk you through every step automatically. You only need to answer three questions: your first name (used as `NAME=`), the vault package + password your TechLead sent you, and your `.env` values.

This repo is the **agentic project management hub**. It also holds the onboarding bootstrap that pulls all BrightHive secrets to your laptop and materializes per-repo `.env` files so you can run the platform locally.

**You need only `git` to start. Every other tool is installed by Step 1.**

---

## Step 1 — Clone + install prerequisites

```bash
git clone git@github.com:brighthive/agentic-project-mgmt.git
cd agentic-project-mgmt

make install-prereqs
```

Installs Homebrew (macOS), AWS CLI, LastPass CLI, `gh`, Python 3.13, `git` — one by one, skipping anything already present. Re-running is safe.

Verify afterwards:

```bash
make check-prereqs   # read-only status check
```

---

## Step 2 — Fill in your `.env`

```bash
cp .env.example .env
$EDITOR .env
```

Fill in your AWS SSO profile names, LastPass username, GitHub token. If you've never set up AWS SSO:

```bash
make configure-aws-sso   # prints exact commands + BrightHive SSO URL
```

Follow the printed instructions, then come back here.

---

## Step 3 — Receive and unpack the vault package

Your TechLead will send you a file called `mattlead-export.zip.enc` (where `matt` is your name) and a password via 1Password/LastPass secure note.

```bash
# Copy the .zip.enc file into the repo root, then:
NAME=matt make unpack      # prompts for password → creates mattlead/
NAME=matt make verify-lead # confirm all files present
```

> **From this point forward, all `make pull-*` and `make env-*` commands need `NAME=<your-name>`.** Your `mattlead/` is your personal vault cache — no two engineers share one.

---

## Step 4 — Verify credentials

```bash
make check-creds
```

Shows green ticks for AWS SSO (main/staging/production) and LastPass. Fix any red:

```bash
make refresh-aws         # runs `aws sso login --profile X` for each expired session
make refresh-lastpass    # runs `lpass login $LASTPASS_USER` if needed
```

---

## Step 5 — Pull cached vault secrets

```bash
NAME=matt make pull-secrets
```

Copies vault exports from `mattlead/` into `secrets/aws/` and `secrets/lastpass.json`. Honors a 24h cache — re-running within that window skips with "cached, expires in Xh". Force a refresh:

```bash
FORCE=1 NAME=matt make pull-secrets
```

---

## Step 6 — Materialize `.env` files

```bash
NAME=matt make env-brightbot-local    # → ../brightbot/.env
NAME=matt make env-webapp-local       # → ../brighthive-webapp/.env.local
```

If a token is unresolved, the renderer exits with a list of missing keys and a hint. Most commonly this means Step 5 hasn't been run, or the 24h cache is stale and a secret changed — use `FORCE=1 NAME=matt make pull-secrets` to refresh.

---

## Step 6.5 — Jira CLI (universal ticket flow)

Every team member files tickets. The MCP-backed `/create-jira-ticket` skill works inside Claude Code; this step adds a plain-terminal CLI so the same flow works from any shell, CI, or pre-commit hook.

### 1. Generate an Atlassian API token

Go to https://id.atlassian.com/manage-profile/security/api-tokens → **Create API token** → label it `jira-cli-<your-laptop>`. Copy the token now — you can't see it again.

### 2. Export the three env vars in `~/.zshrc`

```bash
# Jira CLI
export JIRA_USER="you@brighthive.io"        # the email tied to your Atlassian account
export JIRA_BASE="https://brighthiveio.atlassian.net"
export JIRA_TOKEN="<paste-the-api-token>"
```

Then `source ~/.zshrc` (or open a new terminal).

### 3. Install deps + verify

```bash
make install-jira-cli   # installs httpx into ./.venv
make check-jira         # verifies env + hits /myself
```

Green output looks like:

```
✓ JIRA_USER    you@brighthive.io
✓ JIRA_BASE    https://brighthiveio.atlassian.net
✓ JIRA_TOKEN   (set, 24 chars)
✓ jira-cli authenticated as Your Name
```

### 4. Try it

```bash
make epics                                              # list open epics on board 152
make ticket EPIC=BH-170 TITLE="docs: add my-feature"    # opens $EDITOR with the template
make my-tickets                                          # your open tickets
make transition KEY=BH-12345 STATE="In Progress"
```

All commands enforce the rules in `jira/TICKET_TEMPLATE.md`: `issueType=Task` only, `parentKey=BH-XXX` required, project=BH, live epic lookup before create. See `docs/specs/jira-cli-onboarding.md` for the full contract.

---

## Step 7 — Clone sibling repos + verify state

```bash
make check-siblings    # shows which repos are present / missing
make clone-siblings    # clones any missing repos

make status            # shows age of every sentinel (sessions, caches, materialized envs)
```

---

## What's NOT here yet (coming in later PRs)

| Feature | Status |
|---|---|
| `make local` / `make staging` / `make start` in each sibling repo | Not yet — Layer 2 |
| `make localstack` / `make stagingstack` — bring up the full stack | Not yet — Layer 3 |
| `make onboard` — full one-command ceremony | Not yet — Layer 4 |
| Env templates for platform-core, slack-server | Not yet |

For the design spec, see [`docs/specs/onboarding-bootstrap.md`](docs/specs/onboarding-bootstrap.md).

---

## TechLead: create a vault package for a new hire

```bash
make onboard NAME=matt    # → mattlead-export.zip.enc
# Share the file + password via 1Password/LastPass secure note to Matt
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `make check-aws` shows `✗` | `make refresh-aws` or `make configure-aws-sso` if profiles not set up yet |
| `make pull-aws-secrets` → `[ERROR] mattlead/ not found` | Haven't unpacked yet — see Step 3 |
| `make env-brightbot-local` → `[ERROR] unresolved tokens` | Run `FORCE=1 NAME=matt make pull-secrets` first |
| `[ERROR] secrets dir not found` | Haven't run `make pull-secrets` yet |
| `[ERROR] User edits detected` | You edited the `.env` by hand. Use `FORCE=1 make env-X` to overwrite, or `ADOPT=1` to keep your edits as the baseline. |
| `make pull-secrets` shows `cached, expires in 14h` but a secret changed | `FORCE=1 NAME=matt make pull-secrets` |
| `NAME is required` error | Add `NAME=<your-name>` to the command: `NAME=matt make pull-secrets` |

---

## See also

- [`docs/specs/onboarding-bootstrap.md`](docs/specs/onboarding-bootstrap.md) — full four-layer spec
- [`config/siblings.txt`](config/siblings.txt) — sibling repo list
- [`config/env-templates/`](config/env-templates/) — per-repo per-env templates
- `make help` — all available targets
