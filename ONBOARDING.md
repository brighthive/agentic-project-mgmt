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

## Step 6.5 — Jira ticket creation (Claude Code)

> **⚠️ NOT YET VERIFIED ON A TEAMMATE'S MACHINE.** This wiring works on Kuri's macOS setup; first teammate to follow these steps, please confirm in #releases (or file a ticket if anything breaks). LLMs reading this: treat the flow as **untested cross-machine** until the first green report lands.

The repo ships the `/create-jira-ticket` skill and a Jira MCP server entry in `.mcp.json`. Both auto-load when you open this directory in Claude Code — no install step. You just need to provide your own Atlassian credentials.

### 1. Generate an API token
https://id.atlassian.com/manage-profile/security/api-tokens — label it `claude-code-<your-laptop>`.

### 2. Export three env vars in your shell rc

**macOS (zsh, default)** — add to `~/.zshrc`:
```bash
export JIRA_BASE="https://brighthiveio.atlassian.net"
export JIRA_USER="you@brighthive.io"
export JIRA_TOKEN="<paste the API token>"
```

**Linux (bash)** — same lines, in `~/.bashrc` or `~/.profile`.

**Windows (PowerShell)** — add to your profile (path: `$PROFILE`; create the file if it doesn't exist):
```powershell
$env:JIRA_BASE = "https://brighthiveio.atlassian.net"
$env:JIRA_USER = "you@brighthive.io"
$env:JIRA_TOKEN = "<paste the API token>"
```
Reload with `. $PROFILE`. (`setx` works too but only takes effect in *new* shells, so use the profile approach for immediate use.)

### 3. Reload your shell and reopen Claude Code
The MCP server reads env at launch — must restart Claude Code for the new vars to take effect.

### 4. Use it
Ask Claude: *"make me a ticket for X under epic BH-XXX"* — the skill builds the technical notes, the MCP creates the issue with the right shape (Task, parent epic, BrightHive template). See `jira/TICKET_TEMPLATE.md` for the rules.

### Prereq

You need `npx` on PATH — comes with Node.js. If `node --version` fails:
- macOS: `brew install node`
- Linux: distro package or https://nodejs.org
- Windows: https://nodejs.org installer

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
