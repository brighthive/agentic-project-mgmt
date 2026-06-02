---
name: poc-callouts
description: Read a PoC tracker (clients/trials/<slug>/TRACKER.md + .tracker-snapshot.json), check who didn't update tickets/PRs, and post a thoughtful nudge to #engineering. Calls out specific work, not people. Weekday-only. Use when the user asks to "check on the team", "ping anyone behind", or "post the daily callouts".
allowed-tools: Read, Grep, Glob, Bash
---

# PoC callouts skill

Surface activity gaps on a Longaeva-style PoC tracker and post a Slack nudge to #engineering. **Judgment over thresholds.** A deterministic "stale 3d" script can't tell you Ahmed was pairing on Marwan's PR all morning. You can.

## When to use

The user says something like:
- "Check on the team"
- "Anyone behind on the tracker?"
- "Post the daily callouts"
- "Who hasn't updated their tickets?"

Skip when:
- It's Saturday or Sunday in the user's timezone (no name-and-shame on weekends).
- The tracker is < 12 hours old AND has zero status changes (nothing to react to yet).

## Inputs

For client `<slug>` (default `longaeva`):

1. `clients/trials/<slug>/TRACKER.md` — current generated tracker.
2. `clients/trials/<slug>/.tracker-snapshot.json` — last refresh's snapshot (gitignored; only readable on the cron host).
3. `clients/trials/<slug>/poc.yaml` — ownership map (lane + slack_id per owner).
4. **Optional context** when the user provides it: recent Slack threads in #engineering, PTO status, ongoing pairing.

## Rules

- **Name the work, not the person**, but include the person.
  - ✅ `BH-527 hasn't moved in 3 days — @Marwan, can you push or unblock?`
  - ❌ `Marwan hasn't done anything in 3 days.`
- **Be specific** — every callout names a ticket key or PR number with a real timeframe. Vague "no activity" lands wrong.
- **Group by owner**, one Slack message per refresh, not one per gap.
- **Use Slack mentions** from `poc.yaml` ownership.slack_id; fall back to *bold name* if missing.
- **Never include**:
  - Tickets in Done status
  - Tickets in queued (not in progress + no PR) — those aren't anyone's active responsibility
  - PRs already merged
- **Always include**:
  - Tickets `In Progress` for 5+ days with no linked PR
  - Tickets `In Progress` with no transition in 48h
  - PRs in draft for 48h+ (mark Ready or close)
  - PRs in review with no commit/comment in 48h
- **Tone**: factual, action-oriented. Each line should make it clear what would resolve the gap.

## How to read the tracker

1. Run `make longaeva-tracker-no-slack` first to ensure TRACKER.md is fresh.
2. Read `clients/trials/<slug>/TRACKER.md`. Sections to scan:
   - **🏁 Who's done what** — per-owner counts.
   - **📋 Tickets by status** — filter for In Review and In Progress; check the "Recent activity" section for each ticket's `updated`.
   - **🕒 Recent activity** — anything *not* listed there hasn't moved in 14 days (probably stale).
3. Read `.tracker-snapshot.json` if present — fields `ticket_statuses` and `pr_states` reflect the last cron snapshot.
4. Read `poc.yaml` `ownership` section for slack_ids.
5. **Use judgment** about what to call out. If only 1 ticket is stale, post about that one. If everyone's quiet, post a different message ("Day before holiday — quiet day expected, no nudges.").

## Slack post format

```
🔔 Tracker check-in — <date>
The work that needs attention this morning:

• <@U123> — *BH-527* In Progress 6 days, no PR yet (<link>)
• <@U456> — *brightbot#488* still draft 4 days (<link>) — mark Ready when tests are green
• <@U789> — *BH-541* hasn't moved in 3 days (<link>)

If you're blocked, drop a 🚧 reaction and I'll loop folks in.
```

Send via the Slack bot:

```bash
SLACK_BOT_TOKEN=$(jq -r '.bot_token' ~/.claude/slack/tokens.json)
curl -s -X POST "https://slack.com/api/chat.postMessage" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data '{"channel":"C0782EYPC2K","text":"...","blocks":[...]}'
```

(Channel ID `C0782EYPC2K` = #engineering. Read from `poc.yaml` `slack.channel_id` for non-Longaeva clients.)

## Step-by-step

1. **Check the day**. If Saturday/Sunday, tell the user this skill skips weekends. Stop.
2. **Refresh the tracker** unless the user says "use the existing one":
   ```bash
   make longaeva-tracker-no-slack
   ```
3. **Read the tracker** sections listed above.
4. **Read `poc.yaml`** for slack_ids.
5. **Read context the user provides** (Slack threads, PTO mentions). Treat as authoritative — if the user says "Marwan is on PTO", don't call him out.
6. **Compose the Slack post** following the format above. Pick a tone:
   - If 0 gaps: post a short positive update ("All in flight, no nudges").
   - If 1-3 gaps: focused nudges.
   - If 4+ gaps: pull back. Likely a real blocker upstream — ask the user before posting.
7. **Show the user the draft** before posting. Get explicit approval. Then post.

## Don't

- Do NOT cron this skill. It's manual on purpose — judgment doesn't run on a schedule.
- Do NOT mention people who aren't in `poc.yaml` ownership.
- Do NOT use the deterministic 48h/5d thresholds blindly. They're a *floor*, not a rule.
- Do NOT post if the user hasn't approved the draft.

## Related

- `scripts/poc_tracker/` — the deterministic tracker that generates TRACKER.md
- `scripts/poc_tracker/README.md` — framework guide
- `clients/trials/longaeva/TEAM_GUIDE.md` — team workflow doc
