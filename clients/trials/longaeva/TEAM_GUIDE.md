---
title: "Longaeva trial — team workflow"
audience: "Marwan, Ahmed, Harbour, Kuri"
last_reviewed: "2026-06-02"
---

# Longaeva trial — team workflow

> One repo, one tracker, one ritual: pick a ticket → branch → PR → merge → tracker
> shows the change. The tracker is the single source of truth. If the tracker
> doesn't show your work, your work doesn't exist for the trial.

## Tracker

[`clients/trials/longaeva/TRACKER.md`](TRACKER.md) — refreshed by
`make longaeva-tracker` and nightly cron. Reads Jira (BH-526 children, BH-503
children, all Snowflake-spec tickets, anything with "Longaeva" or "POC" in the
text) and joins it with GitHub PRs across the 4 repos the trial touches.

## Daily ritual

1. **Morning standup** — pull `master`, open `TRACKER.md`, scan:
   - 🚨 Blockers — anything new since yesterday?
   - 🎯 This Week — am I on the list?
   - 📊 Summary — points done / total
2. **Pick a ticket**:
   - Filter the [BH-526 board](https://brighthiveio.atlassian.net/browse/BH-526) by
     `Assignee = Unassigned` AND `Status = To Do`.
   - Self-assign in Jira and move the ticket to `In Progress`.
3. **Branch + PR** — see naming + linkage rules below.
4. **Merge** — Jira ticket auto-moves via the GitHub→Jira integration when the PR
   merges. The tracker picks it up on the next refresh.
5. **End of day** — if you raised a blocker, add a line to the 🚨 Blockers section
   of `TRACKER.md` (it's preserved across refreshes).

## Picking work

| Bucket | Source |
|---|---|
| Pre-trial Snowflake / OMD / CDK | BH-526 children — `parent = BH-526` |
| Quality rules backbone | BH-503 children — `parent = BH-503` |
| Anything else trial-related | Search Jira for "Longaeva" or "POC" |

If a piece of work *should* be tracked but isn't surfacing, **open a ticket
under BH-526** (use `mcp__jira__jira_create_issue` via Claude or
[Jira directly](https://brighthiveio.atlassian.net/jira/software/c/projects/BH/boards/152)).
Don't do uncovered work.

## Branch naming

```
<short-name>/<BH-XXX>/<short-slug>
```

Examples:

- `marwan/BH-527/snowflake-connection`
- `ahmed/BH-554/workspace-secret-store`
- `harbour/BH-552/webapp-snowflake-audit`

The `BH-XXX` token is what links the branch back to the tracker. Keep it; don't
abbreviate it.

## PR linkage rule

The PR title or body MUST contain the Jira ticket key (`BH-XXX`). The tracker's
GitHub fetcher looks for `\bBH-\d+\b` in:

1. PR title (best — surfaces in lists)
2. PR body (acceptable — search the first 400 chars)
3. Branch name (fallback — already covered by the naming rule)

Multiple ticket keys per PR are fine. The tracker links the PR to every ticket
it mentions.

## When to refresh the tracker

- **Manual**: `make longaeva-tracker` — anyone on the team can run it
  - Posts a one-line diff to #engineering when something changed
  - Add `--no-slack` to skip the post (e.g. while iterating locally)
- **Cron**: nightly at 06:00 ET (10:00 UTC) — see `crontab -l | grep longaeva`
  to verify
- **On PR merge**: the tracker isn't auto-refreshed by GitHub Actions today.
  If you need an immediate refresh after merging, run `make longaeva-tracker`.

## Manual sections

These four sections of `TRACKER.md` are NOT overwritten by the refresh script —
edit them directly and commit:

| Section | When to edit |
|---|---|
| 🚨 **Blockers** | Whenever you hit one. Format: `**🚨 BH-XXX** — description (raised YYYY-MM-DD by @owner)`. Remove the line when resolved. |
| 🎯 **This Week** | Monday morning standup output. Bullet list of ticket commitments by owner. |
| 📝 **Daily Notes** | During the trial only — one heading per trial day (`### Day N — YYYY-MM-DD`), bullet log of what happened. |
| ❓ **Open Questions** | For Grant or for the team. Mark `(Grant)` or `(team)`; date-stamp on resolution. |

## Auth — first-time setup

Requirements:
- **Python 3.11+** (the tracker uses `datetime.fromisoformat` features added in 3.11)
- **`gh` CLI** authenticated via `gh auth login` (the tracker uses keyring auth, not `GITHUB_TOKEN`)

One-time Jira:
1. Generate an API token at <https://id.atlassian.com/manage-profile/security/api-tokens>
2. Add to `~/.zshrc` or `.env` at the **repo root** (the same `.env` other Makefile targets use). Either env-var form works:
   ```sh
   # Long form (preferred for clarity)
   export JIRA_BASE_URL="https://brighthiveio.atlassian.net"
   export JIRA_USER_EMAIL="you@brighthive.io"
   export JIRA_API_TOKEN="paste-token-here"

   # Short form (alias — also accepted)
   export JIRA_BASE="https://brighthiveio.atlassian.net"
   export JIRA_USER="you@brighthive.io"
   export JIRA_TOKEN="paste-token-here"
   ```
3. Verify: `make longaeva-tracker-dry`  (≡ `python3 -m scripts.longaeva_tracker --dry-run`)
   - `--dry-run` already implies no Slack post; `--no-slack` is the explicit flag.

GitHub: re-uses your existing `gh` CLI auth (`gh auth status`). The tracker
strips `GITHUB_TOKEN`/`GH_TOKEN` from env to avoid scope mismatches — your
keyring login is the one that matters.

Slack (optional): the tracker reads `SLACK_BOT_TOKEN` from env first, then
falls back to `~/.claude/slack/tokens.json`. Override the target channel with
`SLACK_CHANNEL_ID=…` (default is `#engineering` / `C0782EYPC2K`). Skip the
post entirely with `--no-slack`. The bot must be a member of the channel —
add via `/invite @brightagent` if needed.

## Cron setup

Nightly refresh at 06:00 ET (10:00 UTC):

```sh
make longaeva-tracker-install-cron      # idempotent — safe to re-run
make longaeva-tracker-uninstall-cron    # remove if needed
```

Or manually with `crontab -e`:

```sh
0 10 * * * cd $(pwd-of-this-repo) && make longaeva-tracker >> /tmp/longaeva-tracker.log 2>&1
```

The tracker logs to `/tmp/longaeva-tracker.log`; tail it after the first run.

## Trouble?

- Tracker fails with `Missing required env vars` → see Auth above.
- Tracker shows tickets you didn't expect → check the JQL line in the log;
  adjust `LONGAEVA_KEYWORD_JQL` in `scripts/longaeva_tracker/config.py`.
- PR not linking → confirm `BH-XXX` is in title / body / branch; rerun.
- Slack post not appearing → `gh auth status` for tokens; bot must be in
  #engineering (already added).
