"""Slack post for tracker refresh — full state + diff highlights.

Replaces the diff-only message with a richer state snapshot mgmt can read
without opening the tracker file: phase progress, who's done what, and the
diff highlights since the last refresh.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from collections import Counter

from ._ssl import build_ssl_context
from .github_client import GitHubPR
from .jira_client import JiraTicket
from .loader import PocConfig
from .snapshot import TrackerDiff

logger = logging.getLogger(__name__)


def post_to_slack(
    *,
    config: PocConfig,
    diff: TrackerDiff,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
    phase_progress: list[tuple[str, int, int]],
) -> bool:
    """Post the full state + diff. Returns True on success.

    Caller passes pre-computed `phase_progress` so we don't duplicate the
    expectations logic. Each tuple is (phase_title, green_count, total_count).
    """
    if not config.auth.slack_bot_token:
        logger.info("SLACK_BOT_TOKEN not set — skipping Slack post.")
        return False
    if not config.slack_channel_id:
        logger.info("slack.channel_id not configured — skipping Slack post.")
        return False

    text, blocks = _render_message(
        config=config,
        diff=diff,
        tickets=tickets,
        pr_map=pr_map,
        phase_progress=phase_progress,
    )
    payload = {
        "channel": config.slack_channel_id,
        "text": text,
        "blocks": blocks,
    }
    req = urllib.request.Request(
        url="https://slack.com/api/chat.postMessage",
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.auth.slack_bot_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15, context=build_ssl_context()) as resp:
            body = json.loads(resp.read())
    except Exception:  # noqa: BLE001 — don't block tracker on Slack outage
        logger.warning("Slack post failed", exc_info=True)
        return False
    if not body.get("ok"):
        logger.warning("Slack rejected post: %s", body.get("error"))
        return False
    return True


def _render_message(
    *,
    config: PocConfig,
    diff: TrackerDiff,
    tickets: list[JiraTicket],
    pr_map: dict[str, list[GitHubPR]],
    phase_progress: list[tuple[str, int, int]],
) -> tuple[str, list[dict]]:
    """Compose a Slack post with phase progress + scoreboard + diff highlights."""
    total = len(tickets)
    done = sum(1 for t in tickets if t.is_done)
    headline = (
        f"📊 {config.slug.title()} tracker · {done}/{total} done · "
        + _format_diff_headline(diff=diff)
    )

    phase_lines = "\n".join(
        f"• *{title}* — {green}/{total_p}"
        for title, green, total_p in phase_progress
    )
    scoreboard_lines = _format_scoreboard(tickets=tickets, pr_map=pr_map)

    blocks: list[dict] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{headline}*"}},
        {"type": "section", "text": {"type": "mrkdwn",
            "text": "*Phase progress*\n" + (phase_lines or "_no phases configured_")}},
        {"type": "section", "text": {"type": "mrkdwn",
            "text": "*Who's done what*\n" + (scoreboard_lines or "_no tickets in scope_")}},
    ]

    diff_chunks = _format_diff_chunks(diff=diff)
    for chunk in diff_chunks:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": chunk}})

    blocks.append(
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"<{config.tracker_github_url}|Open full tracker>"}
            ],
        }
    )
    return headline, blocks


def _format_diff_headline(*, diff: TrackerDiff) -> str:
    parts: list[str] = []
    if diff.merged_prs:
        parts.append(f"{len(diff.merged_prs)} merged")
    if diff.status_changes:
        parts.append(f"{len(diff.status_changes)} moved")
    if diff.new_tickets:
        parts.append(f"+{len(diff.new_tickets)} tickets")
    if diff.new_prs:
        parts.append(f"+{len(diff.new_prs)} PRs")
    return " · ".join(parts) if parts else "no change"


def _format_diff_chunks(*, diff: TrackerDiff) -> list[str]:
    chunks: list[str] = []
    if diff.merged_prs:
        chunks.append(
            "*Merged since last refresh*\n"
            + "\n".join(f"• `{pr}`" for pr in diff.merged_prs[:8])
        )
    if diff.status_changes:
        chunks.append(
            "*Status changes*\n"
            + "\n".join(
                f"• `{key}` {old} → {new}" for key, old, new in diff.status_changes[:8]
            )
        )
    if diff.new_tickets:
        chunks.append(
            "*New tickets*\n" + "\n".join(f"• `{key}`" for key in diff.new_tickets[:8])
        )
    if diff.new_prs:
        chunks.append(
            "*New PRs*\n" + "\n".join(f"• `{pr}`" for pr in diff.new_prs[:8])
        )
    return chunks


def _format_scoreboard(
    *, tickets: list[JiraTicket], pr_map: dict[str, list[GitHubPR]]
) -> str:
    """Per-assignee one-liner: name · ✅n 🔵n 🟡n."""
    by_assignee: dict[str, Counter[str]] = {}
    for t in tickets:
        owner = t.assignee_name or "_unassigned_"
        bucket = by_assignee.setdefault(owner, Counter())
        if t.is_done:
            bucket["done"] += 1
        elif t.status_category == "In Progress" or any(
            pr.state == "OPEN" for pr in pr_map.get(t.key, [])
        ):
            bucket["in_flight"] += 1
        else:
            bucket["queued"] += 1

    lines = []
    for owner, counts in sorted(
        by_assignee.items(),
        key=lambda kv: (kv[0] == "_unassigned_", -counts_get_done(kv[1]), kv[0]),
    ):
        lines.append(
            f"• *{owner}* — ✅{counts.get('done', 0)} "
            f"🔵{counts.get('in_flight', 0)} "
            f"🟡{counts.get('queued', 0)}"
        )
    return "\n".join(lines)


def counts_get_done(counter: Counter[str]) -> int:
    return counter.get("done", 0)
