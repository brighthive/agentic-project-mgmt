"""Slack post — diff-aware so refreshes that change nothing stay quiet."""

from __future__ import annotations

import json
import logging
import urllib.request

from ._ssl import build_ssl_context
from .config import TrackerConfig
from .snapshot import TrackerDiff

logger = logging.getLogger(__name__)


def post_to_slack_if_changed(
    *,
    diff: TrackerDiff,
    config: TrackerConfig,
    tracker_url: str,
) -> bool:
    """Returns True if a message was posted, False if skipped (no diff or no token)."""
    if diff.is_empty:
        logger.info("Tracker diff is empty — skipping Slack post.")
        return False
    if not config.slack_bot_token:
        logger.info("SLACK_BOT_TOKEN not set — skipping Slack post.")
        return False

    text, blocks = _render_message(diff=diff, tracker_url=tracker_url)
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
            "Authorization": f"Bearer {config.slack_bot_token}",
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


def _render_message(*, diff: TrackerDiff, tracker_url: str) -> tuple[str, list[dict]]:
    headline_parts: list[str] = []
    if diff.merged_prs:
        headline_parts.append(f"{len(diff.merged_prs)} PR(s) merged")
    if diff.new_prs:
        headline_parts.append(f"{len(diff.new_prs)} new PR(s)")
    if diff.status_changes:
        headline_parts.append(f"{len(diff.status_changes)} ticket(s) moved")
    if diff.new_tickets:
        headline_parts.append(f"{len(diff.new_tickets)} new ticket(s)")
    headline = "Longaeva tracker — " + (" · ".join(headline_parts) or "refreshed")

    fields: list[str] = []
    if diff.merged_prs:
        fields.append("*Merged*\n" + "\n".join(f"• `{pr}`" for pr in diff.merged_prs[:8]))
    if diff.status_changes:
        fields.append(
            "*Status changes*\n"
            + "\n".join(
                f"• `{key}` {old} → {new}" for key, old, new in diff.status_changes[:8]
            )
        )
    if diff.new_tickets:
        fields.append(
            "*New tickets*\n" + "\n".join(f"• `{key}`" for key in diff.new_tickets[:8])
        )
    if diff.new_prs:
        fields.append("*New PRs*\n" + "\n".join(f"• `{pr}`" for pr in diff.new_prs[:8]))

    blocks: list[dict] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*{headline}*"}},
    ]
    for chunk in fields:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": chunk}})
    blocks.append(
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"<{tracker_url}|Open tracker>"}
            ],
        }
    )
    return headline, blocks
