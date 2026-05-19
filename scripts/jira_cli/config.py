"""Config loader — reads env, raises AuthError with a clean message if anything is missing."""

from __future__ import annotations

import os
from dataclasses import dataclass

from scripts.jira_cli.errors import AuthError


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    user: str
    token: str
    project_key: str = "BH"
    board_id: int = 152

    def __post_init__(self) -> None:
        if not self.base_url.startswith("https://"):
            raise AuthError(f"JIRA_BASE must be https:// URL, got: {self.base_url}")


def load_config_from_env(env: dict[str, str] | None = None) -> JiraConfig:
    """Read JIRA_USER/JIRA_TOKEN/JIRA_BASE; raise AuthError naming the first missing var."""
    source = env if env is not None else os.environ
    for name in ("JIRA_USER", "JIRA_TOKEN", "JIRA_BASE"):
        if not source.get(name, "").strip():
            raise AuthError(f"{name} not set — see ONBOARDING.md step 6.5")
    board_raw = source.get("JIRA_BOARD_ID", "152")
    try:
        board_id = int(board_raw)
    except ValueError as exc:
        raise AuthError(f"JIRA_BOARD_ID must be an integer, got: {board_raw!r}") from exc
    return JiraConfig(
        base_url=source["JIRA_BASE"].rstrip("/"),
        user=source["JIRA_USER"].strip(),
        token=source["JIRA_TOKEN"].strip(),
        project_key=source.get("JIRA_PROJECT_KEY", "BH"),
        board_id=board_id,
    )
