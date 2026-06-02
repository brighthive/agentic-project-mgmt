"""Tracker config — loaded from environment.

Per ~/.claude/rules/brighthive-ops.md "No Hardcoded Type Strings": every
ticket key, JQL fragment, repo slug, and Slack channel is a module-level
constant. Tests import these too.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Final

logger = logging.getLogger(__name__)

# ── Tracker scope (the "all" answer) ─────────────────────────────────

# Parent epic for all Longaeva pre-trial work.
LONGAEVA_EPIC: Final[str] = "BH-526"

# Other Longaeva-relevant epics that drop tickets into the tracker.
ADJACENT_EPICS: Final[tuple[str, ...]] = (
    "BH-503",  # Configurable Quality Agent — quality rules backbone
)

# Snowflake integration spec lives in this repo, not as a Jira epic, but its
# children (BH-527/528/549/550/551/552/553/554) all live under BH-526. Listed
# here so the tracker shows them as the "Snowflake integration" group even if
# Jira reorganizes them later.
SNOWFLAKE_TICKET_KEYS: Final[tuple[str, ...]] = (
    "BH-527", "BH-528", "BH-549", "BH-550",
    "BH-551", "BH-552", "BH-553", "BH-554",
    "BH-531",  # Atlas YAML scaffold
)

# Catch-all JQL — tickets whose summary or description mentions Longaeva /
# POC keywords but that aren't already in BH-526. Keeps stragglers visible.
LONGAEVA_KEYWORD_JQL: Final[str] = (
    'project = BH AND statusCategory != Done AND ('
    'summary ~ "Longaeva" OR description ~ "Longaeva" OR '
    'summary ~ "POC" OR summary ~ "Snowflake POC"'
    ')'
)

# ── GitHub repos crossed by Longaeva work ────────────────────────────

LONGAEVA_REPOS: Final[tuple[str, ...]] = (
    "brighthive/brightbot",
    "brighthive/brighthive-platform-core",
    "brighthive/brighthive-data-organization-cdk",
    "brighthive/agentic-project-mgmt",
)

# ── External SoT URLs (cross-repo type strings) ──────────────────────

JIRA_BROWSE_BASE: Final[str] = "https://brighthiveio.atlassian.net/browse"
TRACKER_GITHUB_URL: Final[str] = (
    "https://github.com/brighthive/agentic-project-mgmt/blob/master/"
    "clients/trials/longaeva/TRACKER.md"
)

# ── Slack ────────────────────────────────────────────────────────────

# Default — env-overridable via SLACK_CHANNEL_ID so tests don't post to
# #engineering by accident.
SLACK_CHANNEL_ENGINEERING_ID: Final[str] = "C0782EYPC2K"

# ── Render bounds ───────────────────────────────────────────────────

RECENT_ACTIVITY_DAYS: Final[int] = 14
RECENT_ACTIVITY_MAX_ROWS: Final[int] = 20
SUMMARY_CLIP_CHARS: Final[int] = 70

# ── Output ──────────────────────────────────────────────────────────

TRACKER_RELATIVE_PATH: Final[str] = "clients/trials/longaeva/TRACKER.md"
SNAPSHOT_RELATIVE_PATH: Final[str] = "clients/trials/longaeva/.tracker-snapshot.json"

# Markers used to preserve manual sections across refreshes.
MANUAL_SECTION_MARKER_BEGIN: Final[str] = "<!-- TRACKER:MANUAL:BEGIN {name} -->"
MANUAL_SECTION_MARKER_END: Final[str] = "<!-- TRACKER:MANUAL:END {name} -->"
MANUAL_SECTION_NAMES: Final[tuple[str, ...]] = (
    "blockers",
    "this-week",
    "daily-notes",
    "open-questions",
)


@dataclass(frozen=True)
class TrackerConfig:
    """Resolved auth + endpoint config; built once via load_from_env."""

    jira_base_url: str
    jira_user_email: str
    jira_api_token: str
    slack_bot_token: str | None    # optional — silent skip if absent
    slack_channel_id: str          # default SLACK_CHANNEL_ENGINEERING_ID, env-overridable

    @property
    def auth_basic(self) -> tuple[str, str]:
        return (self.jira_user_email, self.jira_api_token)


def load_from_env() -> TrackerConfig:
    """Load + validate config from environment. Raises ValueError if missing.

    Accepts either the long form (JIRA_BASE_URL / JIRA_USER_EMAIL /
    JIRA_API_TOKEN) or the short form already used elsewhere on this machine
    (JIRA_BASE / JIRA_USER / JIRA_TOKEN). Long form wins when both are set.
    """
    base_url_form = (
        "JIRA_BASE_URL" if "JIRA_BASE_URL" in os.environ
        else "JIRA_BASE" if "JIRA_BASE" in os.environ
        else "default"
    )
    base_url = (
        os.environ.get("JIRA_BASE_URL")
        or os.environ.get("JIRA_BASE")
        or "https://brighthiveio.atlassian.net"
    ).rstrip("/")
    user_form = "JIRA_USER_EMAIL" if "JIRA_USER_EMAIL" in os.environ else "JIRA_USER"
    user_email = os.environ.get("JIRA_USER_EMAIL") or os.environ.get("JIRA_USER")
    api_token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN")
    logger.info(
        "Resolved Jira config: base=%s (from %s), user via %s",
        base_url, base_url_form, user_form,
    )

    missing = [
        name
        for name, val in (
            ("JIRA_USER_EMAIL or JIRA_USER", user_email),
            ("JIRA_API_TOKEN or JIRA_TOKEN", api_token),
        )
        if not val
    ]
    if missing:
        raise ValueError(
            f"Missing required env vars for Jira: {', '.join(missing)}. "
            "Add them to .env (see .env.example) or your shell."
        )

    # Slack token: either env var or fall back to ~/.claude/slack/tokens.json
    # which the rest of the repo's Slack tooling already uses.
    slack_token = os.environ.get("SLACK_BOT_TOKEN") or _load_slack_bot_token_from_file()

    return TrackerConfig(
        jira_base_url=base_url,
        jira_user_email=user_email,
        jira_api_token=api_token,
        slack_bot_token=slack_token,
        slack_channel_id=os.environ.get("SLACK_CHANNEL_ID", SLACK_CHANNEL_ENGINEERING_ID),
    )


def _load_slack_bot_token_from_file() -> str | None:
    """Best-effort read of ~/.claude/slack/tokens.json."""
    import json
    from pathlib import Path

    path = Path.home() / ".claude" / "slack" / "tokens.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text()).get("bot_token") or None
    except (OSError, json.JSONDecodeError):
        return None
