"""JiraClient — REST v3 + Agile API wrapper with DI for testing.

The HTTP client is injected so contract tests can pass a stub without
`unittest.mock.patch`. No module-level singletons; every dependency is
constructor-injected per testable-code.md.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from scripts.jira_cli.adf import text_to_adf
from scripts.jira_cli.config import JiraConfig
from scripts.jira_cli.errors import (
    AuthError,
    EpicNotFoundError,
    JiraAPIError,
    UsageError,
)
from scripts.jira_cli.models import JiraEpic, JiraIssue, JiraTransition, JiraUser
from scripts.jira_cli.template import (
    enforce_template_marker,
    validate_epic_key,
    validate_summary,
)

def _auth_header(user: str, token: str) -> str:
    raw = f"{user}:{token}".encode()
    return "Basic " + base64.b64encode(raw).decode("ascii")


def build_http_client(
    config: JiraConfig, *, timeout: float = 15.0, transport: httpx.BaseTransport | None = None
) -> httpx.Client:
    """Factory for the default httpx.Client. Tests pass `transport=MockTransport(...)`."""
    kwargs: dict[str, object] = dict(
        base_url=config.base_url,
        headers={
            "Authorization": _auth_header(user=config.user, token=config.token),
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=timeout,
    )
    if transport is not None:
        kwargs["transport"] = transport
    return httpx.Client(**kwargs)  # type: ignore[arg-type]


def _scrub(text: str, secrets: tuple[str, ...]) -> str:
    """Replace each secret substring with `***` (defense-in-depth for upstream echo)."""
    out = text
    for secret in secrets:
        if secret:
            out = out.replace(secret, "***")
    return out


class JiraClient:
    """All Jira interactions go through here. Receives an httpx.Client via DI."""

    def __init__(self, *, config: JiraConfig, http: httpx.Client) -> None:
        self._config = config
        self._http = http

    @property
    def config(self) -> JiraConfig:
        return self._config

    def whoami(self) -> JiraUser:
        data = self._get(path="/rest/api/3/myself")
        return JiraUser(
            account_id=data["accountId"],
            display_name=data.get("displayName", ""),
            email=data.get("emailAddress"),
        )

    def list_epics(self, *, include_done: bool = False) -> list[JiraEpic]:
        path = f"/rest/agile/1.0/board/{self._config.board_id}/epic"
        params = {"done": "true" if include_done else "false"}
        data = self._get(path=path, params=params)
        return [
            JiraEpic(
                key=item["key"],
                summary=item.get("name") or item.get("summary", ""),
                status_category="done" if item.get("done") else "indeterminate",
                done=bool(item.get("done", False)),
            )
            for item in data.get("values", [])
        ]

    def assert_epic_is_open(self, *, epic_key: str) -> JiraEpic:
        """Look up the epic in the live open-epic list; raise EpicNotFoundError if absent."""
        validate_epic_key(epic_key)
        for epic in self.list_epics(include_done=False):
            if epic.key == epic_key:
                return epic
        raise EpicNotFoundError(
            f"epic {epic_key} not found in open epics for board {self._config.board_id}"
        )

    def create_task(
        self,
        *,
        epic_key: str,
        summary: str,
        description: str,
        priority: str = "Medium",
        labels: list[str] | None = None,
        assignee_account_id: str | None = None,
        issue_type: str = "Task",
    ) -> JiraIssue:
        if issue_type != "Task":
            raise UsageError(f"issueType={issue_type} is forbidden; use Task")

        validate_epic_key(epic_key)
        validate_summary(summary)
        enforce_template_marker(description)
        self.assert_epic_is_open(epic_key=epic_key)

        fields: dict[str, Any] = {
            "project": {"key": self._config.project_key},
            "issuetype": {"name": "Task"},
            "parent": {"key": epic_key},
            "summary": summary,
            "description": text_to_adf(description),
            "priority": {"name": priority},
        }
        if labels:
            fields["labels"] = list(labels)
        assignee_clean = (assignee_account_id or "").strip()
        if assignee_clean:
            fields["assignee"] = {"accountId": assignee_clean}

        data = self._post(path="/rest/api/3/issue", json={"fields": fields})
        key = data["key"]
        return JiraIssue(
            key=key,
            summary=summary,
            status="To Do",
            issue_type="Task",
            parent_key=epic_key,
            assignee_display=None,
            points=None,
            url=f"{self._config.base_url}/browse/{key}",
        )

    def my_open_issues(self, *, statuses: list[str] | None = None) -> list[JiraIssue]:
        status_clause = ""
        if statuses:
            quoted = ",".join(f'"{s}"' for s in statuses)
            status_clause = f" AND status in ({quoted})"
        jql = (
            f'project = {self._config.project_key} AND assignee = currentUser()'
            f"{status_clause} ORDER BY updated DESC"
        )
        data = self._get(
            path="/rest/api/3/search",
            params={
                "jql": jql,
                "maxResults": "50",
                "fields": "summary,status,issuetype,parent,assignee,customfield_10016",
            },
        )
        return [self._issue_from_search(raw=item) for item in data.get("issues", [])]

    def transitions_for(self, key: str) -> list[JiraTransition]:
        data = self._get(path=f"/rest/api/3/issue/{key}/transitions")
        return [
            JiraTransition(
                transition_id=t["id"],
                name=t["name"],
                to_status=t["to"]["name"],
            )
            for t in data.get("transitions", [])
        ]

    def transition(self, key: str, *, to_state: str) -> JiraTransition:
        transitions = self.transitions_for(key=key)
        match = next(
            (t for t in transitions if t.to_status.lower() == to_state.lower()),
            None,
        )
        if match is None:
            available = ", ".join(sorted(t.to_status for t in transitions)) or "(none)"
            raise UsageError(
                f"no transition to {to_state!r} from current state; available: {available}"
            )
        self._post(
            path=f"/rest/api/3/issue/{key}/transitions",
            json={"transition": {"id": match.transition_id}},
        )
        return match

    def _issue_from_search(self, *, raw: dict[str, Any]) -> JiraIssue:
        fields = raw.get("fields", {})
        parent = fields.get("parent") or {}
        assignee = fields.get("assignee") or {}
        return JiraIssue(
            key=raw["key"],
            summary=fields.get("summary", ""),
            status=(fields.get("status") or {}).get("name", ""),
            issue_type=(fields.get("issuetype") or {}).get("name", ""),
            parent_key=parent.get("key"),
            assignee_display=assignee.get("displayName"),
            points=fields.get("customfield_10016"),
            url=f"{self._config.base_url}/browse/{raw['key']}",
        )

    def _get(self, *, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request(method="GET", path=path, params=params)

    def _post(self, *, path: str, json: dict[str, Any]) -> dict[str, Any]:
        return self._request(method="POST", path=path, json_body=json)

    def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._http.request(method=method, url=path, params=params, json=json_body)
        except httpx.RequestError as exc:
            raise JiraAPIError(f"network error talking to Jira: {exc!s}") from exc

        if response.status_code == 401:
            raise AuthError(
                "authentication failed — token may have expired; "
                "regenerate at id.atlassian.com/manage-profile/security/api-tokens"
            )
        if response.status_code == 403:
            raise AuthError("authorization failed — token lacks required permissions")
        if response.status_code >= 400:
            snippet = _scrub(response.text[:500], secrets=(self._config.token,))
            raise JiraAPIError(
                f"jira {method} {path} returned {response.status_code}: {snippet}"
            )

        if not response.content:
            return {}
        try:
            payload = response.json()
        except ValueError as exc:
            raise JiraAPIError(f"non-JSON response from {path}: {exc!s}") from exc
        return payload if isinstance(payload, dict) else {"values": payload}
