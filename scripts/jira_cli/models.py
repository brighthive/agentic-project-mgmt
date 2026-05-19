"""Typed value objects for Jira entities — frozen dataclasses, no dicts in the API surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

JiraStatusCategory = Literal["new", "indeterminate", "done"]


@dataclass(frozen=True)
class JiraUser:
    account_id: str
    display_name: str
    email: str | None


@dataclass(frozen=True)
class JiraEpic:
    key: str
    summary: str
    status_category: JiraStatusCategory
    done: bool


@dataclass(frozen=True)
class JiraIssue:
    key: str
    summary: str
    status: str
    issue_type: str
    parent_key: str | None
    assignee_display: str | None
    points: float | None
    url: str


@dataclass(frozen=True)
class JiraTransition:
    transition_id: str
    name: str
    to_status: str
