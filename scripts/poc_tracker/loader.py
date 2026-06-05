"""Load a PoC tracker config from clients/trials/<slug>/poc.yaml.

This is the single source of truth — all per-client knobs (scope, ownership,
phases, slack channel) live in YAML, not Python. The tracker is otherwise
client-agnostic.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

CLIENTS_DIR = Path("clients/trials")


@dataclass(frozen=True)
class Expectation:
    """One expected outcome on a trial day."""

    day: str
    outcome: str
    linked: tuple[str, ...] = ()

    def is_green(
        self, *, ticket_statuses: dict[str, str], merged_pr_keys: set[str]
    ) -> bool | None:
        if not self.linked:
            return None
        for item in self.linked:
            if item.startswith("BH-"):
                if ticket_statuses.get(item, "").lower() != "done":
                    return False
            else:
                if item not in merged_pr_keys:
                    return False
        return True

    def is_wip(
        self,
        *,
        ticket_statuses: dict[str, str],
        merged_pr_keys: set[str],
        open_pr_ticket_keys: set[str],
    ) -> bool:
        """True when work is actively moving but not yet done — ticket In Progress/Review, or a linked PR is open."""
        if not self.linked or self.is_green(
            ticket_statuses=ticket_statuses, merged_pr_keys=merged_pr_keys
        ):
            return False
        wip_statuses = {"in progress", "in review", "code review"}
        for item in self.linked:
            if item.startswith("BH-"):
                if ticket_statuses.get(item, "").lower() in wip_statuses:
                    return True
                if item in open_pr_ticket_keys:
                    return True
            elif item not in merged_pr_keys:
                return True
        return False


@dataclass(frozen=True)
class Phase:
    title: str
    description: str
    expectations: tuple[Expectation, ...]


@dataclass(frozen=True)
class Owner:
    owner: str
    lane: str
    slack_id: str | None = None


@dataclass(frozen=True)
class Auth:
    """Resolved auth + endpoints; built once per run."""

    jira_base_url: str
    jira_user_email: str
    jira_api_token: str
    slack_bot_token: str | None

    @property
    def auth_basic(self) -> tuple[str, str]:
        return (self.jira_user_email, self.jira_api_token)


@dataclass(frozen=True)
class PocConfig:
    """Loaded from <repo-root>/clients/trials/<slug>/poc.yaml."""

    slug: str
    trial_dates: str
    epic: str
    adjacent_epics: tuple[str, ...]
    ticket_keys: tuple[str, ...]
    keyword_jql: str
    repos: tuple[str, ...]
    slack_channel_id: str
    ownership: tuple[Owner, ...]
    phases: tuple[Phase, ...]
    auth: Auth

    @property
    def tracker_path(self) -> Path:
        return CLIENTS_DIR / self.slug / "TRACKER.md"

    @property
    def snapshot_path(self) -> Path:
        return CLIENTS_DIR / self.slug / ".tracker-snapshot.json"

    @property
    def tracker_github_url(self) -> str:
        return (
            "https://github.com/brighthive/agentic-project-mgmt/blob/master/"
            f"{self.tracker_path.as_posix()}"
        )


def load_config(*, slug: str, repo_root: Path) -> PocConfig:
    """Load and validate a PoC config by slug from <repo-root>/clients/trials/<slug>/poc.yaml."""
    yaml_path = repo_root / CLIENTS_DIR / slug / "poc.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"No PoC config at {yaml_path}. Create one or pass --client <slug> for an existing trial."
        )
    raw = yaml.safe_load(yaml_path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{yaml_path} did not parse to a YAML mapping")

    # Validate slug match — guards against renamed dirs.
    yaml_slug = raw.get("slug")
    if yaml_slug != slug:
        raise ValueError(
            f"slug mismatch: directory says {slug!r} but {yaml_path.name} says {yaml_slug!r}"
        )

    scope = raw.get("scope") or {}
    epic = scope.get("epic")
    if not epic:
        raise ValueError(f"{yaml_path}: scope.epic is required")

    return PocConfig(
        slug=slug,
        trial_dates=raw.get("trial_dates", "TBD"),
        epic=epic,
        adjacent_epics=tuple(scope.get("adjacent_epics") or ()),
        ticket_keys=tuple(scope.get("ticket_keys") or ()),
        keyword_jql=scope.get("keyword_jql", "").strip(),
        repos=tuple(raw.get("repos") or ()),
        slack_channel_id=(raw.get("slack") or {}).get("channel_id", ""),
        ownership=tuple(
            Owner(
                owner=row["owner"],
                lane=row["lane"],
                slack_id=row.get("slack_id"),
            )
            for row in (raw.get("ownership") or [])
        ),
        phases=tuple(_parse_phase(phase) for phase in (raw.get("phases") or [])),
        auth=_load_auth(),
    )


def _parse_phase(payload: dict[str, Any]) -> Phase:
    expectations = tuple(
        Expectation(
            day=item["day"],
            outcome=item["outcome"],
            linked=tuple(item.get("linked") or ()),
        )
        for item in (payload.get("expectations") or [])
    )
    return Phase(
        title=payload["title"],
        description=(payload.get("description") or "").strip(),
        expectations=expectations,
    )


def _load_auth() -> Auth:
    """Resolve Jira + Slack creds from env (with sensible fallbacks)."""
    base_url = (
        os.environ.get("JIRA_BASE_URL")
        or os.environ.get("JIRA_BASE")
        or "https://brighthiveio.atlassian.net"
    ).rstrip("/")
    user_email = os.environ.get("JIRA_USER_EMAIL") or os.environ.get("JIRA_USER")
    api_token = os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN")
    missing = [
        name for name, val in (
            ("JIRA_USER_EMAIL or JIRA_USER", user_email),
            ("JIRA_API_TOKEN or JIRA_TOKEN", api_token),
        ) if not val
    ]
    if missing:
        raise ValueError(f"Missing required env vars for Jira: {', '.join(missing)}")

    slack_token = os.environ.get("SLACK_BOT_TOKEN") or _slack_token_from_file()
    return Auth(
        jira_base_url=base_url,
        jira_user_email=user_email,
        jira_api_token=api_token,
        slack_bot_token=slack_token,
    )


def _slack_token_from_file() -> str | None:
    import json
    path = Path.home() / ".claude" / "slack" / "tokens.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text()).get("bot_token") or None
    except (OSError, json.JSONDecodeError):
        return None
