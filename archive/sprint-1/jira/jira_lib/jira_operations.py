"""High-level Jira operations.

Composable, pure functions for common Jira operations.
"""

from typing import Any

from . import jira_client
from .jira_config import JiraConfig
from .jira_models import (
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

# Type aliases
UserResult = tuple[User | None, JiraError | None]
IssueResult = tuple[Issue | None, JiraError | None]
IssueListResult = tuple[list[Issue], JiraError | None]
SprintResult = tuple[Sprint | None, JiraError | None]
SprintListResult = tuple[list[Sprint], JiraError | None]
BoardResult = tuple[Board | None, JiraError | None]
BoardListResult = tuple[list[Board], JiraError | None]
OperationResult = tuple[bool, JiraError | None]


def get_user_by_email(config: JiraConfig, email: str) -> UserResult:
    """Get user by email address.

    Args:
        config: Jira configuration
        email: User's email address

    Returns:
        Tuple of (User, error)
    """
    data, error = jira_client.get(
        config,
        "/rest/api/3/user/search",
        params={"query": email},
    )

    if error:
        return (None, error)

    if not data or not isinstance(data, list) or len(data) == 0:
        return (
            None,
            JiraError(
                status_code=404,
                message=f"No user found with email: {email}",
            ),
        )

    return (User.from_api_response(data[0]), None)


def get_user_by_email_with_fallbacks(
    config: JiraConfig,
    emails: list[str],
) -> UserResult:
    """Try multiple email addresses to find a user.

    Args:
        config: Jira configuration
        emails: List of email addresses to try

    Returns:
        Tuple of (User, error) for first successful match
    """
    for email in emails:
        user, error = get_user_by_email(config, email)
        if user:
            return (user, None)

    return (
        None,
        JiraError(
            status_code=404,
            message=f"No user found with any of: {', '.join(emails)}",
        ),
    )


def get_issue(config: JiraConfig, issue_key: str) -> IssueResult:
    """Get issue by key.

    Args:
        config: Jira configuration
        issue_key: Issue key (e.g., BH-123)

    Returns:
        Tuple of (Issue, error)
    """
    data, error = jira_client.get(config, f"/rest/api/3/issue/{issue_key}")

    if error:
        return (None, error)

    if not data:
        return (
            None,
            JiraError(status_code=404, message=f"Issue not found: {issue_key}"),
        )

    return (Issue.from_api_response(data), None)


def search_issues(
    config: JiraConfig,
    jql: str,
    max_results: int = 100,
) -> IssueListResult:
    """Search issues using JQL.

    Args:
        config: Jira configuration
        jql: JQL query string
        max_results: Maximum results to return

    Returns:
        Tuple of (list of Issues, error)
    """
    issues_data, error = jira_client.search_jql(config, jql, max_results=max_results)

    if error:
        return ([], error)

    if not issues_data:
        return ([], None)

    issues = [Issue.from_api_response(data) for data in issues_data]
    return (issues, None)


def assign_issue(
    config: JiraConfig,
    issue_key: str,
    user: User,
) -> OperationResult:
    """Assign issue to user.

    Args:
        config: Jira configuration
        issue_key: Issue key (e.g., BH-123)
        user: User to assign to

    Returns:
        Tuple of (success: bool, error)
    """
    payload = {"accountId": user.account_id}

    _, error = jira_client.put(
        config,
        f"/rest/api/3/issue/{issue_key}/assignee",
        payload,
    )

    if error:
        return (False, error)

    return (True, None)


def transition_issue(
    config: JiraConfig,
    issue_key: str,
    transition_id: str,
) -> OperationResult:
    """Transition issue to new status.

    Args:
        config: Jira configuration
        issue_key: Issue key (e.g., BH-123)
        transition_id: Transition ID

    Returns:
        Tuple of (success: bool, error)
    """
    payload = {"transition": {"id": transition_id}}

    _, error = jira_client.post(
        config,
        f"/rest/api/3/issue/{issue_key}/transitions",
        payload,
    )

    if error:
        return (False, error)

    return (True, None)


def add_issue_to_sprint(
    config: JiraConfig,
    issue_key: str,
    sprint_id: int,
) -> OperationResult:
    """Add issue to sprint.

    Args:
        config: Jira configuration
        issue_key: Issue key (e.g., BH-123)
        sprint_id: Sprint ID

    Returns:
        Tuple of (success: bool, error)
    """
    payload = {"issues": [issue_key]}

    _, error = jira_client.post(
        config,
        f"/rest/agile/1.0/sprint/{sprint_id}/issue",
        payload,
    )

    if error:
        return (False, error)

    return (True, None)


def get_board_by_project(config: JiraConfig, project_key: str) -> BoardResult:
    """Get board by project key.

    Args:
        config: Jira configuration
        project_key: Project key (e.g., BH)

    Returns:
        Tuple of (Board, error)
    """
    data, error = jira_client.get(
        config,
        "/rest/agile/1.0/board",
        params={"projectKeyOrId": project_key},
    )

    if error:
        return (None, error)

    if not data or "values" not in data or len(data["values"]) == 0:
        return (
            None,
            JiraError(
                status_code=404,
                message=f"No board found for project: {project_key}",
            ),
        )

    return (Board.from_api_response(data["values"][0]), None)


def get_board_sprints(
    config: JiraConfig,
    board_id: int,
    state: SprintState | None = None,
) -> SprintListResult:
    """Get sprints for board.

    Args:
        config: Jira configuration
        board_id: Board ID
        state: Optional sprint state filter

    Returns:
        Tuple of (list of Sprints, error)
    """
    params = {}
    if state:
        params["state"] = state.value

    data, error = jira_client.get(
        config,
        f"/rest/agile/1.0/board/{board_id}/sprint",
        params=params,
    )

    if error:
        return ([], error)

    if not data or "values" not in data:
        return ([], None)

    sprints = [Sprint.from_api_response(sprint_data) for sprint_data in data["values"]]
    return (sprints, None)


def create_sprint(
    config: JiraConfig,
    board_id: int,
    name: str,
) -> SprintResult:
    """Create new sprint.

    Args:
        config: Jira configuration
        board_id: Board ID
        name: Sprint name

    Returns:
        Tuple of (Sprint, error)
    """
    payload = {
        "name": name,
        "originBoardId": board_id,
    }

    data, error = jira_client.post(config, "/rest/agile/1.0/sprint", payload)

    if error:
        return (None, error)

    if not data:
        return (
            None,
            JiraError(status_code=500, message="Sprint creation returned no data"),
        )

    return (Sprint.from_api_response(data), None)


def create_issue(
    config: JiraConfig,
    project_key: str,
    summary: str,
    issue_type: IssueType,
    description: dict[str, Any] | str,
    priority: Priority = Priority.MEDIUM,
    assignee: User | None = None,
    labels: list[str] | None = None,
    epic_key: str | None = None,
) -> IssueResult:
    """Create new issue.

    Args:
        config: Jira configuration
        project_key: Project key (e.g., BH)
        summary: Issue summary/title
        issue_type: Type of issue
        description: Issue description (ADF dict or plain text)
        priority: Issue priority
        assignee: User to assign to
        labels: List of labels
        epic_key: Parent epic key

    Returns:
        Tuple of (Issue, error)
    """
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type.value},
        "description": description,
        "priority": {"name": priority.value},
    }

    if assignee:
        fields["assignee"] = {"accountId": assignee.account_id}

    if labels:
        fields["labels"] = labels

    if epic_key:
        fields["parent"] = {"key": epic_key}

    payload = {"fields": fields}

    data, error = jira_client.post(config, "/rest/api/3/issue", payload)

    if error:
        return (None, error)

    if not data or "key" not in data:
        return (
            None,
            JiraError(status_code=500, message="Issue creation returned no key"),
        )

    return get_issue(config, data["key"])


def verify_assignment(
    config: JiraConfig,
    issue_key: str,
    expected_user: User,
) -> tuple[bool, JiraError | None]:
    """Verify issue is assigned to expected user.

    Args:
        config: Jira configuration
        issue_key: Issue key to verify
        expected_user: Expected assignee

    Returns:
        Tuple of (is_correct: bool, error)
    """
    issue, error = get_issue(config, issue_key)

    if error:
        return (False, error)

    if not issue:
        return (
            False,
            JiraError(status_code=404, message=f"Issue not found: {issue_key}"),
        )

    if not issue.assignee:
        return (
            False,
            JiraError(
                status_code=400,
                message=f"{issue_key} is unassigned",
            ),
        )

    is_correct = issue.assignee.account_id == expected_user.account_id
    return (is_correct, None)
