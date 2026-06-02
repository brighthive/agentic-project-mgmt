"""Thin Jira REST client — read-only ticket fetch for the tracker."""

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
from .loader import PocConfig

logger = logging.getLogger(__name__)

JIRA_FIELDS: tuple[str, ...] = (
    "summary", "status", "assignee", "priority", "issuetype",
    "labels", "parent", "customfield_10016", "updated", "created",
)
JIRA_SEARCH_PATH = "/rest/api/3/search/jql"
JIRA_PAGE_SIZE = 100
MAX_TICKETS = 500
JIRA_BROWSE_BASE = "https://brighthiveio.atlassian.net/browse"

_TICKET_KEY_RE = re.compile(r"^BH-\d+$")


@dataclass(frozen=True)
class JiraTicket:
    key: str
    summary: str
    status: str
    status_category: str
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


def fetch_tickets(*, config: PocConfig) -> list[JiraTicket]:
    bad = [
        k for k in (config.epic, *config.adjacent_epics, *config.ticket_keys)
        if not _TICKET_KEY_RE.fullmatch(k)
    ]
    if bad:
        raise ValueError(f"Malformed Jira ticket key(s) in poc.yaml: {bad}")

    parts = [f"parent = {config.epic}"]
    parts.extend(f"parent = {epic}" for epic in config.adjacent_epics)
    if config.ticket_keys:
        parts.append(f"key in ({','.join(config.ticket_keys)})")
    if config.keyword_jql:
        parts.append(config.keyword_jql)
    jql = " OR ".join(f"({p})" for p in parts)
    logger.info("Tracker JQL: %s", jql)
    return _search_all(config=config, jql=jql)


def _search_all(*, config: PocConfig, jql: str) -> list[JiraTicket]:
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
            url=f"{config.auth.jira_base_url}{JIRA_SEARCH_PATH}",
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
                "Hit MAX_TICKETS=%d cap — truncating. Tighten keyword_jql.",
                MAX_TICKETS,
            )
            break

        next_token = payload.get("nextPageToken")
        if not next_token:
            break

    seen: set[str] = set()
    unique: list[JiraTicket] = []
    for ticket in tickets:
        if ticket.key in seen:
            continue
        seen.add(ticket.key)
        unique.append(ticket)
    return unique


def _basic_auth_header(*, config: PocConfig) -> str:
    creds = f"{config.auth.jira_user_email}:{config.auth.jira_api_token}"
    return "Basic " + base64.b64encode(creds.encode("utf-8")).decode("ascii")


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
