"""Snapshot + diff for Slack notifications.

Persists a minimal JSON snapshot of ticket statuses + PR states between
refreshes. Used to compute a human-readable diff so the Slack post says what
*changed* rather than recapping the whole tracker every time.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .github_client import GitHubPR
from .jira_client import JiraTicket


@dataclass(frozen=True)
class TrackerSnapshot:
    timestamp: str
    ticket_statuses: dict[str, str]   # key -> status name
    pr_states: dict[str, str]         # repo#num -> state (OPEN/MERGED/CLOSED/DRAFT)


@dataclass(frozen=True)
class TrackerDiff:
    """Human-readable change summary between two snapshots."""

    new_tickets: list[str]
    closed_tickets: list[str]
    status_changes: list[tuple[str, str, str]]  # (key, old, new)
    new_prs: list[str]                          # repo#num
    merged_prs: list[str]

    @property
    def is_empty(self) -> bool:
        return not (
            self.new_tickets
            or self.closed_tickets
            or self.status_changes
            or self.new_prs
            or self.merged_prs
        )


def build_snapshot(
    *, tickets: Iterable[JiraTicket], pr_map: dict[str, list[GitHubPR]]
) -> TrackerSnapshot:
    pr_states: dict[str, str] = {}
    for prs in pr_map.values():
        for pr in prs:
            label = "DRAFT" if pr.is_draft else pr.state
            pr_states[f"{pr.short_repo}#{pr.number}"] = label
    return TrackerSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ticket_statuses={t.key: t.status for t in tickets},
        pr_states=pr_states,
    )


def load_snapshot(*, path: Path) -> TrackerSnapshot | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    return TrackerSnapshot(
        timestamp=raw.get("timestamp", ""),
        ticket_statuses=raw.get("ticket_statuses", {}),
        pr_states=raw.get("pr_states", {}),
    )


def save_snapshot(*, snapshot: TrackerSnapshot, path: Path) -> None:
    path.write_text(json.dumps(asdict(snapshot), indent=2, sort_keys=True) + "\n")


def diff_snapshots(
    *, previous: TrackerSnapshot | None, current: TrackerSnapshot
) -> TrackerDiff:
    if previous is None:
        # First-ever run on this machine: skip the diff post (would otherwise
        # dump 38+ "new tickets" into Slack). Persist the snapshot — the next
        # refresh becomes the first real signal.
        return TrackerDiff(
            new_tickets=[],
            closed_tickets=[],
            status_changes=[],
            new_prs=[],
            merged_prs=[],
        )

    prev_keys = set(previous.ticket_statuses)
    curr_keys = set(current.ticket_statuses)
    new_tickets = sorted(curr_keys - prev_keys)
    closed_tickets = sorted(prev_keys - curr_keys)
    status_changes = sorted(
        (key, previous.ticket_statuses[key], current.ticket_statuses[key])
        for key in prev_keys & curr_keys
        if previous.ticket_statuses[key] != current.ticket_statuses[key]
    )

    prev_pr_keys = set(previous.pr_states)
    curr_pr_keys = set(current.pr_states)
    new_prs = sorted(curr_pr_keys - prev_pr_keys)
    merged_prs = sorted(
        pr_key
        for pr_key in prev_pr_keys & curr_pr_keys
        if previous.pr_states[pr_key] != "MERGED" and current.pr_states[pr_key] == "MERGED"
    )

    return TrackerDiff(
        new_tickets=new_tickets,
        closed_tickets=closed_tickets,
        status_changes=status_changes,
        new_prs=new_prs,
        merged_prs=merged_prs,
    )
