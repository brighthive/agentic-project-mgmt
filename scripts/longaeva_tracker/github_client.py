"""GitHub PR fetch via the `gh` CLI — avoids requests + token wrangling.

Returns PRs across LONGAEVA_REPOS that mention any of the given Jira ticket keys
in title or body. Indexed by ticket key for the renderer.
"""

from __future__ import annotations

import json
import logging
import re
import shlex
import subprocess
from dataclasses import dataclass

from .config import LONGAEVA_REPOS

logger = logging.getLogger(__name__)

# Match BH-### in PR title or body. Word-boundary so BH-1234 doesn't catch BH-12.
TICKET_RE = re.compile(r"\bBH-\d+\b")


@dataclass(frozen=True)
class GitHubPR:
    repo: str           # "brighthive/brightbot"
    number: int
    title: str
    state: str          # "OPEN" | "CLOSED" | "MERGED"
    is_draft: bool
    author: str
    url: str
    body_excerpt: str   # first 400 chars
    head_branch: str

    @property
    def short_repo(self) -> str:
        return self.repo.split("/", 1)[-1]

    @property
    def label(self) -> str:
        prefix = "🟢 Merged" if self.state == "MERGED" else (
            "🟡 Draft" if self.is_draft else "🔵 Review"
        )
        return f"{prefix} {self.short_repo}#{self.number}"


def fetch_prs_referencing_tickets(*, ticket_keys: set[str]) -> dict[str, list[GitHubPR]]:
    """Across LONGAEVA_REPOS, find PRs whose title or body references a tracker ticket.

    Returns: {ticket_key: [GitHubPR, ...]} — multiple PRs per ticket allowed.
    """
    by_ticket: dict[str, list[GitHubPR]] = {key: [] for key in ticket_keys}

    for repo in LONGAEVA_REPOS:
        try:
            prs = _list_recent_prs(repo=repo)
        except subprocess.CalledProcessError as exc:
            logger.warning("Skipping %s — gh exited %s: %s", repo, exc.returncode, exc.stderr)
            continue

        for pr in prs:
            referenced = _extract_referenced_tickets(pr=pr, scope=ticket_keys)
            for ticket_key in referenced:
                by_ticket[ticket_key].append(pr)

    return by_ticket


def _list_recent_prs(*, repo: str) -> list[GitHubPR]:
    """`gh pr list` — last 100 PRs in any state, with body for keyword scan.

    Strips GITHUB_TOKEN from the env so `gh` falls back to the keyring auth.
    Local shells often have a fine-grained PAT exported that doesn't cover
    every repo the tracker touches.
    """
    import os

    cmd = (
        f"gh pr list --repo {shlex.quote(repo)} --state all --limit 100 "
        f"--json number,title,state,isDraft,author,url,body,headRefName"
    )
    # Subtract token env vars only — keep PATH/HOME/XDG_CONFIG_HOME so `gh`
    # can find its keyring config and binaries.
    env = {**os.environ}
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)
    result = subprocess.run(
        shlex.split(cmd),
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    raw_prs = json.loads(result.stdout)
    return [
        GitHubPR(
            repo=repo,
            number=p["number"],
            title=p["title"],
            state=p["state"],
            is_draft=bool(p.get("isDraft", False)),
            author=(p.get("author") or {}).get("login", "unknown"),
            url=p["url"],
            body_excerpt=(p.get("body") or "")[:400],
            head_branch=p.get("headRefName", ""),
        )
        for p in raw_prs
    ]


def _extract_referenced_tickets(*, pr: GitHubPR, scope: set[str]) -> set[str]:
    """Find any BH-### tokens in title/body/branch that are in the tracker scope."""
    haystack = f"{pr.title} {pr.body_excerpt} {pr.head_branch}"
    found = set(TICKET_RE.findall(haystack))
    return found & scope
