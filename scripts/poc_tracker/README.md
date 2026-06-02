# PoC Tracker — framework

Live tracker that joins **Jira + GitHub PRs** into one Markdown doc per client trial. Originally built for the Longaeva POC, now agnostic — point it at any `clients/trials/<slug>/poc.yaml` and it produces a `TRACKER.md` next to it.

## What it does

For each refresh:

1. Reads `clients/trials/<slug>/poc.yaml` for scope + ownership + day-by-day expectations
2. Hits Jira REST for tickets in scope (parent epic, adjacent epics, explicit keys, keyword catch-all)
3. Shells out to `gh pr list` across the configured repos and links PRs to tickets via `BH-XXX` regex
4. Renders `TRACKER.md` with day-by-day matrix, scoreboard, status grid, recent activity
5. Writes a JSON snapshot for diff-vs-last-run
6. Posts a state + diff message to Slack when something changed

Manual sections (🚨 Blockers, 🎯 This Week, 📝 Daily Notes, ❓ Open Questions) are preserved across refreshes via in-page HTML-comment markers.

## Quick start

```bash
# Default — refresh Longaeva
make longaeva-tracker

# Different client
make poc-tracker CLIENT=acme

# Dry run (no file write, no Slack)
make poc-tracker-dry CLIENT=acme

# No Slack post
make poc-tracker-no-slack CLIENT=acme
```

Cron is auto-installed via `make longaeva-tracker-install-cron` (06:00 ET nightly). Edit the cron schedule in the Makefile if you need a different cadence.

## Adding a new client

1. Create `clients/trials/<slug>/poc.yaml` (copy `clients/trials/longaeva/poc.yaml` as a starting point).
2. Fill in:
   - `slug:` matches the directory name
   - `scope.epic:` primary Jira epic key (e.g. `BH-XXX`) — its children become tickets
   - `scope.adjacent_epics:` other epics whose children should land in scope (optional)
   - `scope.ticket_keys:` explicit ticket keys to include even if not under an epic
   - `scope.keyword_jql:` catch-all clause (must include `statusCategory != Done` so done tickets don't double-count)
   - `repos:` GitHub repos crossed by the trial
   - `slack.channel_id:` target Slack channel
   - `ownership:` lane definitions per assignee
   - `phases:` day-by-day expectation matrix (see schema below)
3. Run `make poc-tracker CLIENT=<slug>` — that's it.

The renderer creates the `TRACKER.md` in the same directory on the first refresh; subsequent refreshes overwrite the auto sections and preserve the manual ones.

## `poc.yaml` schema

```yaml
slug: <string>                 # required, must match directory name
trial_dates: <string>          # human-readable; appears in tracker header

scope:                         # what tickets show up
  epic: BH-XXX                 # required
  adjacent_epics: [BH-XXX]     # optional list
  ticket_keys: [BH-XXX]        # optional explicit list
  keyword_jql: |               # optional catch-all clause
    project = BH AND statusCategory != Done AND (
      summary ~ "<term>" OR description ~ "<term>"
    )

repos:                         # GitHub repos for PR linkage
  - owner/repo

slack:
  channel_id: C0782EYPC2K      # Slack channel ID (not name)

ownership:                     # appears as "Lanes" block in scoreboard
  - owner: <full name as in Jira>
    lane: <one-line description>

phases:                        # day-by-day expectation matrix
  - title: <phase title>
    description: <one-paragraph context>
    expectations:
      - day: <free-form day label, e.g. "Day 1" or "Pre-trial">
        outcome: <human-readable goal>
        linked: [BH-XXX, repo#PR]    # optional — auto-checks when all are Done/Merged
```

### How auto-checking works

Each row in the day-by-day matrix is one of three states:

| Symbol | Meaning |
|---|---|
| ✅ | All `linked` items are Done (Jira) or Merged (GitHub) |
| 🔲 | Has `linked` items, none are green yet |
| ⬜ | Manual — no `linked` items, flipped by hand once outcome lands |

Phase headers carry their own progress (e.g. `Pre-trial — Snowflake foundation must be merged (3/9)`).

Linked items can be:
- **Jira ticket keys**: `BH-527` — green when `statusCategory == "Done"`
- **PR shorthand**: `repo-name#42` (no owner prefix) — green when the PR state is `MERGED`

## Architecture

```
scripts/poc_tracker/
├── __main__.py        CLI entry; orchestrates the pipeline
├── loader.py          YAML → PocConfig dataclass, env auth resolution
├── jira_client.py     stdlib urllib REST search, paging, ticket-key validation
├── github_client.py   `gh pr list` shellouts, BH-### regex extraction
├── renderer.py        Markdown composer + manual-section preservation
├── snapshot.py        JSON snapshot diff for Slack notifications
├── slack_notify.py    Diff-aware POST to Slack with phase + scoreboard summary
├── _ssl.py            SSL context cascade (truststore → certifi → distro CA)
└── tests/
    ├── test_loader.py         YAML loader + expectation logic + renderer
    └── test_tracker.py        Round-trip preservation, status diff, etc.
```

**No third-party deps except PyYAML.** The Makefile resolver finds a Python that has it (checks repo venvs, falls back to system) so cron works without an active venv.

## Auth

Required env vars (Long form OR short form accepted):

```bash
# Long form
export JIRA_BASE_URL="https://brighthiveio.atlassian.net"
export JIRA_USER_EMAIL="you@brighthive.io"
export JIRA_API_TOKEN="..."

# Short form (alias)
export JIRA_BASE="https://brighthiveio.atlassian.net"
export JIRA_USER="you@brighthive.io"
export JIRA_TOKEN="..."
```

Generate the API token at <https://id.atlassian.com/manage-profile/security/api-tokens>.

GitHub: re-uses your `gh` CLI keyring auth (`gh auth status`). The tracker strips `GITHUB_TOKEN` / `GH_TOKEN` from the subprocess env so a fine-grained PAT in your shell doesn't shadow the keyring.

Slack (optional): `SLACK_BOT_TOKEN` env, or fallback to `~/.claude/slack/tokens.json`. Skip the post entirely with `--no-slack`. The bot must be a member of the configured channel.

## Extending the framework

Common changes:

| You want to | Where |
|---|---|
| Add a new client | New `clients/trials/<slug>/poc.yaml` |
| Change what shows in the day-by-day for an existing client | Edit `phases:` block in that client's `poc.yaml` |
| Change tracker scope | Edit `scope:` block in `poc.yaml` |
| Add a new auto-rendered section | Add a `_render_*` function in `renderer.py`, call it in `_render_auto_sections` |
| Add a new manual section | Add to `MANUAL_SECTION_NAMES` in `renderer.py`, add a default in `_MANUAL_DEFAULTS`, add to the compose template |
| Change Slack message shape | Edit `_render_message` in `slack_notify.py` |
| Cap or extend recent-activity rows | `RECENT_ACTIVITY_DAYS` / `RECENT_ACTIVITY_MAX_ROWS` in `renderer.py` |
| Support a different ticket-key prefix (e.g. `ACME-XXX`) | Update `_TICKET_KEY_RE` in `jira_client.py` and the `\bBH-\d+\b` regex in `github_client.py` |

Don't change without thinking:

- **Manual section markers** (`<!-- TRACKER:MANUAL:BEGIN/END name -->`) — touching these breaks preservation across refreshes for any existing tracker file
- **Snapshot path** — `clients/trials/<slug>/.tracker-snapshot.json` is gitignored; if you commit it, every cron run produces a noisy diff commit

## Testing

```bash
aws-secrets-vault/.venv/bin/pytest scripts/poc_tracker/tests/ -v
```

22 tests across loader (5), expectation logic (4), renderer (2), and tracker integration (11). Run before any change to `loader.py` / `renderer.py`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Missing required env vars for Jira` | API token not exported | Export `JIRA_USER` + `JIRA_TOKEN` in your shell |
| `gh exited 1: HTTP 401` | `GITHUB_TOKEN` env var has insufficient scope | Tracker now strips it automatically; if it still fails, check `gh auth status` |
| `[SSL: CERTIFICATE_VERIFY_FAILED]` | Python lacks system trust store | Tracker tries truststore → certifi → distro paths; install one with `pip install certifi` if all fail |
| `No PoC config at <path>` | YAML file missing or wrong slug | Create `clients/trials/<slug>/poc.yaml` or fix the `slug:` field |
| Manual section reverted to default | Markers got stripped | Re-add `<!-- TRACKER:MANUAL:BEGIN <name> -->` and `<!-- ... END ... -->` around the body |
| Slack post not appearing | Bot not in channel | `/invite @brightagent` in the channel |
| Cron silent | `/tmp/longaeva-tracker.log` missing or empty | Check crontab entry: `crontab -l \| grep tracker` |

## What this replaces

The first iteration was `scripts/longaeva_tracker/` — Longaeva-only, with expectations hard-coded in Python (`expectations.py`, ~265 lines). The agnostic refactor:

- Moved expectations from Python → YAML (one file per client; the team edits without Python knowledge)
- Renamed module to `poc_tracker`, added `--client <slug>` flag
- Removed module-level constants in favor of `PocConfig` passed through the call graph
- Same auto-rendered sections, same manual-section preservation
- Backwards-compatible Makefile aliases (`make longaeva-tracker` still works)

## Future work

If we keep extending this:

- **Notion mirror** — render `TRACKER.md` to a Notion page on every refresh (blocked on OAuth setup)
- **Per-client Slack channel override** — already supported via `slack.channel_id` in YAML
- **Multiple PoC tracker invocations on one cron** — one cron entry per client, or a `poc-tracker-all` target that loops `clients/trials/*/poc.yaml`
- **Trial-day auto-resolution** — currently `Day 1`/`Day 2`/etc. are free-form; could compute from `trial_start` date in YAML
- **Per-owner Slack DM digest** — instead of a single channel post, send each assignee their own queue
