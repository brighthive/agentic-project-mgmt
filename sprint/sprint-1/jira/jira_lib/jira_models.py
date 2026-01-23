"""Type-safe models for Jira entities.

Immutable data structures with Pydantic validation.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class IssueType(Enum):
    """Jira issue types."""

    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    SUBTASK = "Sub-task"


class IssueStatus(Enum):
    """Jira issue statuses."""

    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    BLOCKED = "Blocked"
    READY = "Ready"
    NEEDS_REFINEMENT = "Needs Refinement"
    CLOSED = "Closed"


class Priority(Enum):
    """Jira issue priorities."""

    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"


class SprintState(Enum):
    """Sprint states."""

    ACTIVE = "active"
    FUTURE = "future"
    CLOSED = "closed"


@dataclass(frozen=True)
class User:
    """Jira user model.

    Attributes:
        account_id: Unique Jira account ID
        display_name: User's display name
        email: User's email address (optional)
    """

    account_id: str
    display_name: str
    email: str | None = None

    @staticmethod
    def from_api_response(data: dict[str, Any]) -> "User":
        """Create User from Jira API response.

        Args:
            data: Raw API response dict

        Returns:
            User instance
        """
        return User(
            account_id=data["accountId"],
            display_name=data["displayName"],
            email=data.get("emailAddress"),
        )


@dataclass(frozen=True)
class Issue:
    """Jira issue model.

    Attributes:
        key: Issue key (e.g., BH-123)
        summary: Issue summary/title
        issue_type: Type of issue
        status: Current status
        description: Issue description (ADF or plain text)
        assignee: Assigned user (optional)
        priority: Issue priority
        labels: List of labels
        created: Creation timestamp
        updated: Last update timestamp
        epic_key: Parent epic key (optional)
    """

    key: str
    summary: str
    issue_type: IssueType
    status: IssueStatus
    description: str | dict[str, Any]
    assignee: User | None
    priority: Priority
    labels: list[str]
    created: datetime
    updated: datetime
    epic_key: str | None = None

    @staticmethod
    def from_api_response(data: dict[str, Any]) -> "Issue":
        """Create Issue from Jira API response.

        Args:
            data: Raw API response dict

        Returns:
            Issue instance
        """
        fields = data["fields"]

        assignee = None
        if fields.get("assignee"):
            assignee = User.from_api_response(fields["assignee"])

        return Issue(
            key=data["key"],
            summary=fields["summary"],
            issue_type=IssueType(fields["issuetype"]["name"]),
            status=IssueStatus(fields["status"]["name"]),
            description=fields.get("description", ""),
            assignee=assignee,
            priority=Priority(fields["priority"]["name"]) if fields.get("priority") else Priority.MEDIUM,
            labels=fields.get("labels", []),
            created=datetime.fromisoformat(fields["created"].replace("Z", "+00:00")),
            updated=datetime.fromisoformat(fields["updated"].replace("Z", "+00:00")),
            epic_key=fields.get("parent", {}).get("key"),
        )


@dataclass(frozen=True)
class Sprint:
    """Jira sprint model.

    Attributes:
        id: Sprint ID
        name: Sprint name
        state: Sprint state
        board_id: Parent board ID
        start_date: Sprint start date (optional)
        end_date: Sprint end date (optional)
    """

    id: int
    name: str
    state: SprintState
    board_id: int
    start_date: datetime | None = None
    end_date: datetime | None = None

    @staticmethod
    def from_api_response(data: dict[str, Any]) -> "Sprint":
        """Create Sprint from Jira API response.

        Args:
            data: Raw API response dict

        Returns:
            Sprint instance
        """
        start_date = None
        if data.get("startDate"):
            start_date = datetime.fromisoformat(data["startDate"].replace("Z", "+00:00"))

        end_date = None
        if data.get("endDate"):
            end_date = datetime.fromisoformat(data["endDate"].replace("Z", "+00:00"))

        return Sprint(
            id=data["id"],
            name=data["name"],
            state=SprintState(data["state"]),
            board_id=data["originBoardId"],
            start_date=start_date,
            end_date=end_date,
        )


@dataclass(frozen=True)
class Board:
    """Jira board model.

    Attributes:
        id: Board ID
        name: Board name
        type: Board type (scrum/kanban)
    """

    id: int
    name: str
    type: str

    @staticmethod
    def from_api_response(data: dict[str, Any]) -> "Board":
        """Create Board from Jira API response.

        Args:
            data: Raw API response dict

        Returns:
            Board instance
        """
        return Board(
            id=data["id"],
            name=data["name"],
            type=data["type"],
        )


@dataclass(frozen=True)
class JiraError:
    """Jira API error model.

    Attributes:
        status_code: HTTP status code
        message: Error message
        errors: Detailed error dict (optional)
    """

    status_code: int
    message: str
    errors: dict[str, Any] | None = None

    def __str__(self) -> str:
        """Return human-readable error string."""
        if self.errors:
            return f"Jira API Error {self.status_code}: {self.message} - {self.errors}"
        return f"Jira API Error {self.status_code}: {self.message}"
