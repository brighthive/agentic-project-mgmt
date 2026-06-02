"""Thin Jira REST client — read-only ticket fetch for the tracker.

Uses stdlib urllib so this script has zero third-party dependencies and runs
under any Python 3.11+ install (matters for the cron entry on a fresh box).
"""

from __future__ import annotations

import base64
import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from ._ssl import build_ssl_context
from .config import (
    ADJACENT_EPICS,
    JIRA_BROWSE_BASE,
    LONGAEVA_EPIC,
    LONGAEVA_KEYWORD_JQL,
    SNOWFLAKE_TICKET_KEYS,
    TrackerConfig,
)

# Validate ticket keys before they enter JQL — defends against injection via
# config edits.
_TICKET_KEY_RE = re.compile(r"^BH-\d+$")

# Cap on tickets returned by a single search — guards against unbounded growth
# of the keyword JQL clause.
MAX_TICKETS = 500

logger = logging.getLogger(__name__)

# Default fields the tracker needs. Avoid `*all` to keep payloads tight.
JIRA_FIELDS: tuple[str, ...] = (
    "summary",
    "status",
    "assignee",
    "priority",
    "issuetype",
    "labels",
    "parent",
    "customfield_10016",  # story points (BrightHive board uses this slot)
    "updated",
    "created",
)

JIRA_SEARCH_PATH = "/rest/api/3/search/jql"
JIRA_PAGE_SIZE = 100


@dataclass(frozen=True)
class JiraTicket:
    """Flat shape — only fields the tracker renders."""

    key: str
    summary: str
    status: str
    status_category: str  # "To Do" | "In Progress" | "Done"
    assignee_name: str | None
    assignee_email: str | None
    priority: str | None
    issue_type: str
    labels: tuple[str, ...]
    parent_key: str | None
    points: float | None
    updated: str
    created: str

    @property
    def is_done(self) -> bool:
        return self.status_category == "Done"

    @property
    def url(self) -> str:
        return f"{JIRA_BROWSE_BASE}/{self.key}"


def fetch_longaeva_tickets(*, config: TrackerConfig) -> list[JiraTicket]:
    """Fetch all tickets in scope: BH-526 children + adjacent epics + keyword catch-all + explicit Snowflake keys."""
    # Validate all ticket keys before interpolating into JQL — fail loud on
    # malformed config rather than emit a 400 from Jira at 2am.
    bad_keys = [k for k in (LONGAEVA_EPIC, *ADJACENT_EPICS, *SNOWFLAKE_TICKET_KEYS)
                if not _TICKET_KEY_RE.fullmatch(k)]
    if bad_keys:
        raise ValueError(f"Malformed Jira ticket key(s) in config: {bad_keys}")

    jql_parts = [
        f"parent = {LONGAEVA_EPIC}",
        *[f"parent = {epic}" for epic in ADJACENT_EPICS],
        f"key in ({','.join(SNOWFLAKE_TICKET_KEYS)})",
        LONGAEVA_KEYWORD_JQL,
    ]
    # Combine with OR so we get the union; statusCategory != Done is already
    # in the keyword JQL but we want done tickets too for the Done column —
    # so wrap each part separately.
    jql = " OR ".join(f"({p})" for p in jql_parts)
    logger.info("Tracker JQL: %s", jql)
    return _search_all(config=config, jql=jql)


def _search_all(*, config: TrackerConfig, jql: str) -> list[JiraTicket]:
    """Page through results until we drain the result set or hit MAX_TICKETS."""
    tickets: list[JiraTicket] = []
    next_token: str | None = None
    auth_header = _basic_auth_header(config=config)
    ssl_ctx = build_ssl_context()

    while True:
        body: dict[str, Any] = {
            "jql": jql,
            "fields": list(JIRA_FIELDS),
            "maxResults": JIRA_PAGE_SIZE,
        }
        if next_token:
            body["nextPageToken"] = next_token

        req = urllib.request.Request(
            url=f"{config.jira_base_url}{JIRA_SEARCH_PATH}",
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": auth_header,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
                payload = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Jira search failed: {exc.code} {exc.read()[:300]!r}"
            ) from exc

        for issue in payload.get("issues", []):
            tickets.append(_parse_issue(issue=issue))

        if len(tickets) >= MAX_TICKETS:
            logger.warning(
                "Hit MAX_TICKETS=%d cap — truncating result set. "
                "Tighten LONGAEVA_KEYWORD_JQL if this happens.",
                MAX_TICKETS,
            )
            break

        next_token = payload.get("nextPageToken")
        if not next_token:
            break

    # Dedupe — multiple JQL clauses may overlap.
    seen: set[str] = set()
    unique: list[JiraTicket] = []
    for ticket in tickets:
        if ticket.key in seen:
            continue
        seen.add(ticket.key)
        unique.append(ticket)
    return unique


def _basic_auth_header(*, config: TrackerConfig) -> str:
    creds = f"{config.jira_user_email}:{config.jira_api_token}"
    encoded = base64.b64encode(creds.encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"


def _parse_issue(*, issue: dict[str, Any]) -> JiraTicket:
    fields = issue.get("fields", {})
    status = fields.get("status", {}) or {}
    status_category = (status.get("statusCategory") or {}).get("name", "Unknown")
    assignee = fields.get("assignee") or {}
    parent = fields.get("parent") or {}
    priority = fields.get("priority") or {}
    issue_type = (fields.get("issuetype") or {}).get("name", "Task")

    return JiraTicket(
        key=issue["key"],
        summary=fields.get("summary", ""),
        status=status.get("name", "Unknown"),
        status_category=status_category,
        assignee_name=assignee.get("displayName"),
        assignee_email=assignee.get("emailAddress"),
        priority=priority.get("name"),
        issue_type=issue_type,
        labels=tuple(fields.get("labels") or ()),
        parent_key=(parent.get("key") if parent else None),
        points=_coerce_points(fields.get("customfield_10016")),
        updated=fields.get("updated", ""),
        created=fields.get("created", ""),
    )


def _coerce_points(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
