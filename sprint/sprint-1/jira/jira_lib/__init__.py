"""Jira API library - Functional, composable Jira automation.

This library provides a clean, type-safe, functional API for Jira automation.

Core principles:
- Pure functions where possible
- Explicit error handling (no exceptions for API errors)
- Immutable data structures
- Type safety with full type hints
- Composable operations

Usage:
    from jira_lib import load_config, get_user_by_email, assign_issue

    config = load_config()
    user, error = get_user_by_email(config, "user@example.com")
    if error:
        print(f"Error: {error}")
        return

    success, error = assign_issue(config, "BH-123", user)
    if not success:
        print(f"Assignment failed: {error}")
"""

from .adf_builder import (
    bold,
    bullet_list,
    code,
    code_block,
    document,
    heading,
    ordered_list,
    paragraph,
    section,
    text,
    ticket_description,
)
from .jira_client import delete, get, post, put, search_jql
from .jira_config import JiraConfig, load_config
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
from .jira_operations import (
    add_issue_to_sprint,
    assign_issue,
    create_issue,
    create_sprint,
    get_board_by_project,
    get_board_sprints,
    get_issue,
    get_user_by_email,
    get_user_by_email_with_fallbacks,
    search_issues,
    transition_issue,
    verify_assignment,
)

__all__ = [
    # Config
    "JiraConfig",
    "load_config",
    # Models
    "User",
    "Issue",
    "Sprint",
    "Board",
    "JiraError",
    "IssueType",
    "IssueStatus",
    "Priority",
    "SprintState",
    # Client (low-level)
    "get",
    "post",
    "put",
    "delete",
    "search_jql",
    # Operations (high-level)
    "get_user_by_email",
    "get_user_by_email_with_fallbacks",
    "get_issue",
    "search_issues",
    "assign_issue",
    "transition_issue",
    "add_issue_to_sprint",
    "get_board_by_project",
    "get_board_sprints",
    "create_sprint",
    "create_issue",
    "verify_assignment",
    # ADF Builders
    "text",
    "bold",
    "code",
    "paragraph",
    "heading",
    "bullet_list",
    "ordered_list",
    "code_block",
    "document",
    "section",
    "ticket_description",
]

__version__ = "0.1.0"
