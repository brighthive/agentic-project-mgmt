"""Tests for jira_models module.

Tests for type-safe model creation and API response parsing.
"""

from datetime import datetime, timezone

import pytest

from jira_lib.jira_models import (
    Board,
    Issue,
    IssueStatus,
    IssueType,
    JiraError,
    Priority,
    Sprint,
    SprintState,
    User,
)


class TestUser:
    """Tests for User model."""

    def test_user_creation(self) -> None:
        """Test basic User creation."""
        user = User(
            account_id="123456",
            display_name="John Doe",
            email="john@example.com",
        )

        assert user.account_id == "123456"
        assert user.display_name == "John Doe"
        assert user.email == "john@example.com"

    def test_user_immutable(self) -> None:
        """Test that User is immutable."""
        user = User(
            account_id="123456",
            display_name="John Doe",
            email="john@example.com",
        )

        with pytest.raises(Exception):
            user.account_id = "654321"  # type: ignore

    def test_user_from_api_response(self) -> None:
        """Test User creation from API response."""
        api_response = {
            "accountId": "5b10ac8d82e05b22cc7d4ef5",
            "displayName": "Marwan Samih",
            "emailAddress": "marwan.samih@brighthive.io",
        }

        user = User.from_api_response(api_response)

        assert user.account_id == "5b10ac8d82e05b22cc7d4ef5"
        assert user.display_name == "Marwan Samih"
        assert user.email == "marwan.samih@brighthive.io"

    def test_user_from_api_response_no_email(self) -> None:
        """Test User creation when email is missing."""
        api_response = {
            "accountId": "123456",
            "displayName": "John Doe",
        }

        user = User.from_api_response(api_response)

        assert user.account_id == "123456"
        assert user.display_name == "John Doe"
        assert user.email is None


class TestIssue:
    """Tests for Issue model."""

    def test_issue_creation(self) -> None:
        """Test basic Issue creation."""
        user = User("123", "John Doe", "john@example.com")
        issue = Issue(
            key="BH-150",
            summary="Test task",
            issue_type=IssueType.TASK,
            status=IssueStatus.TODO,
            description="Test description",
            assignee=user,
            priority=Priority.HIGH,
            labels=["sprint-1"],
            created=datetime.now(timezone.utc),
            updated=datetime.now(timezone.utc),
        )

        assert issue.key == "BH-150"
        assert issue.summary == "Test task"
        assert issue.issue_type == IssueType.TASK
        assert issue.status == IssueStatus.TODO
        assert issue.assignee == user
        assert issue.priority == Priority.HIGH
        assert issue.labels == ["sprint-1"]

    def test_issue_immutable(self) -> None:
        """Test that Issue is immutable."""
        issue = Issue(
            key="BH-150",
            summary="Test task",
            issue_type=IssueType.TASK,
            status=IssueStatus.TODO,
            description="Test",
            assignee=None,
            priority=Priority.MEDIUM,
            labels=[],
            created=datetime.now(timezone.utc),
            updated=datetime.now(timezone.utc),
        )

        with pytest.raises(Exception):
            issue.summary = "Changed"  # type: ignore

    def test_issue_from_api_response_full(self) -> None:
        """Test Issue creation from complete API response."""
        api_response = {
            "key": "BH-150",
            "fields": {
                "summary": "Authentication Configuration for JedX Integration",
                "issuetype": {"name": "Task"},
                "status": {"name": "To Do"},
                "description": "Configure authentication",
                "assignee": {
                    "accountId": "5b10ac8d82e05b22cc7d4ef5",
                    "displayName": "Marwan Samih",
                    "emailAddress": "marwan@brighthive.io",
                },
                "priority": {"name": "High"},
                "labels": ["sprint-1", "backend"],
                "created": "2026-01-10T10:30:00.000+0000",
                "updated": "2026-01-15T14:20:00.000+0000",
                "parent": {"key": "BH-100"},
            },
        }

        issue = Issue.from_api_response(api_response)

        assert issue.key == "BH-150"
        assert issue.summary == "Authentication Configuration for JedX Integration"
        assert issue.issue_type == IssueType.TASK
        assert issue.status == IssueStatus.TODO
        assert issue.description == "Configure authentication"
        assert issue.assignee is not None
        assert issue.assignee.account_id == "5b10ac8d82e05b22cc7d4ef5"
        assert issue.priority == Priority.HIGH
        assert issue.labels == ["sprint-1", "backend"]
        assert issue.epic_key == "BH-100"

    def test_issue_from_api_response_minimal(self) -> None:
        """Test Issue creation from minimal API response."""
        api_response = {
            "key": "BH-200",
            "fields": {
                "summary": "Minimal task",
                "issuetype": {"name": "Task"},
                "status": {"name": "To Do"},
                "created": "2026-01-15T10:00:00.000+0000",
                "updated": "2026-01-15T10:00:00.000+0000",
            },
        }

        issue = Issue.from_api_response(api_response)

        assert issue.key == "BH-200"
        assert issue.summary == "Minimal task"
        assert issue.issue_type == IssueType.TASK
        assert issue.status == IssueStatus.TODO
        assert issue.description == ""  # Missing description
        assert issue.assignee is None  # No assignee
        assert issue.priority == Priority.MEDIUM  # Default priority
        assert issue.labels == []  # No labels
        assert issue.epic_key is None  # No parent

    def test_issue_from_api_response_unassigned(self) -> None:
        """Test Issue creation when unassigned."""
        api_response = {
            "key": "BH-201",
            "fields": {
                "summary": "Unassigned task",
                "issuetype": {"name": "Task"},
                "status": {"name": "To Do"},
                "assignee": None,  # Explicitly null
                "priority": {"name": "Medium"},
                "created": "2026-01-15T10:00:00.000+0000",
                "updated": "2026-01-15T10:00:00.000+0000",
            },
        }

        issue = Issue.from_api_response(api_response)

        assert issue.assignee is None


class TestSprint:
    """Tests for Sprint model."""

    def test_sprint_creation(self) -> None:
        """Test basic Sprint creation."""
        sprint = Sprint(
            id=123,
            name="Sprint 1",
            state=SprintState.ACTIVE,
            board_id=456,
        )

        assert sprint.id == 123
        assert sprint.name == "Sprint 1"
        assert sprint.state == SprintState.ACTIVE
        assert sprint.board_id == 456
        assert sprint.start_date is None
        assert sprint.end_date is None

    def test_sprint_immutable(self) -> None:
        """Test that Sprint is immutable."""
        sprint = Sprint(
            id=123,
            name="Sprint 1",
            state=SprintState.ACTIVE,
            board_id=456,
        )

        with pytest.raises(Exception):
            sprint.name = "Sprint 2"  # type: ignore

    def test_sprint_from_api_response_full(self) -> None:
        """Test Sprint creation from complete API response."""
        api_response = {
            "id": 123,
            "name": "Sprint 1",
            "state": "active",
            "originBoardId": 456,
            "startDate": "2026-01-13T09:00:00.000Z",
            "endDate": "2026-01-24T17:00:00.000Z",
        }

        sprint = Sprint.from_api_response(api_response)

        assert sprint.id == 123
        assert sprint.name == "Sprint 1"
        assert sprint.state == SprintState.ACTIVE
        assert sprint.board_id == 456
        assert sprint.start_date is not None
        assert sprint.end_date is not None

    def test_sprint_from_api_response_minimal(self) -> None:
        """Test Sprint creation without dates."""
        api_response = {
            "id": 789,
            "name": "Sprint 2",
            "state": "future",
            "originBoardId": 456,
        }

        sprint = Sprint.from_api_response(api_response)

        assert sprint.id == 789
        assert sprint.name == "Sprint 2"
        assert sprint.state == SprintState.FUTURE
        assert sprint.board_id == 456
        assert sprint.start_date is None
        assert sprint.end_date is None


class TestBoard:
    """Tests for Board model."""

    def test_board_creation(self) -> None:
        """Test basic Board creation."""
        board = Board(
            id=456,
            name="BrightHive Board",
            type="scrum",
        )

        assert board.id == 456
        assert board.name == "BrightHive Board"
        assert board.type == "scrum"

    def test_board_immutable(self) -> None:
        """Test that Board is immutable."""
        board = Board(
            id=456,
            name="BrightHive Board",
            type="scrum",
        )

        with pytest.raises(Exception):
            board.name = "Changed"  # type: ignore

    def test_board_from_api_response(self) -> None:
        """Test Board creation from API response."""
        api_response = {
            "id": 456,
            "name": "BrightHive Scrum Board",
            "type": "scrum",
        }

        board = Board.from_api_response(api_response)

        assert board.id == 456
        assert board.name == "BrightHive Scrum Board"
        assert board.type == "scrum"


class TestJiraError:
    """Tests for JiraError model."""

    def test_jira_error_creation(self) -> None:
        """Test basic JiraError creation."""
        error = JiraError(
            status_code=404,
            message="Not found",
        )

        assert error.status_code == 404
        assert error.message == "Not found"
        assert error.errors is None

    def test_jira_error_with_details(self) -> None:
        """Test JiraError creation with error details."""
        error = JiraError(
            status_code=400,
            message="Validation failed",
            errors={"assignee": "User not found"},
        )

        assert error.status_code == 400
        assert error.message == "Validation failed"
        assert error.errors == {"assignee": "User not found"}

    def test_jira_error_str_simple(self) -> None:
        """Test JiraError string representation without details."""
        error = JiraError(
            status_code=404,
            message="Not found",
        )

        error_str = str(error)
        assert "404" in error_str
        assert "Not found" in error_str

    def test_jira_error_str_with_details(self) -> None:
        """Test JiraError string representation with details."""
        error = JiraError(
            status_code=400,
            message="Validation failed",
            errors={"field": "invalid"},
        )

        error_str = str(error)
        assert "400" in error_str
        assert "Validation failed" in error_str
        assert "field" in error_str

    def test_jira_error_immutable(self) -> None:
        """Test that JiraError is immutable."""
        error = JiraError(
            status_code=404,
            message="Not found",
        )

        with pytest.raises(Exception):
            error.status_code = 500  # type: ignore


class TestEnums:
    """Tests for enum types."""

    def test_issue_type_values(self) -> None:
        """Test IssueType enum values."""
        assert IssueType.EPIC.value == "Epic"
        assert IssueType.STORY.value == "Story"
        assert IssueType.TASK.value == "Task"
        assert IssueType.BUG.value == "Bug"
        assert IssueType.SUBTASK.value == "Sub-task"

    def test_issue_status_values(self) -> None:
        """Test IssueStatus enum values."""
        assert IssueStatus.TODO.value == "To Do"
        assert IssueStatus.IN_PROGRESS.value == "In Progress"
        assert IssueStatus.DONE.value == "Done"
        assert IssueStatus.BLOCKED.value == "Blocked"
        assert IssueStatus.READY.value == "Ready"

    def test_priority_values(self) -> None:
        """Test Priority enum values."""
        assert Priority.HIGHEST.value == "Highest"
        assert Priority.HIGH.value == "High"
        assert Priority.MEDIUM.value == "Medium"
        assert Priority.LOW.value == "Low"
        assert Priority.LOWEST.value == "Lowest"

    def test_sprint_state_values(self) -> None:
        """Test SprintState enum values."""
        assert SprintState.ACTIVE.value == "active"
        assert SprintState.FUTURE.value == "future"
        assert SprintState.CLOSED.value == "closed"
