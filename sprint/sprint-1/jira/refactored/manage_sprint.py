#!/usr/bin/env python3
"""Sprint management operations.

REFACTORED VERSION - Composable sprint operations.

Before: Multiple separate scripts (check_sprints.py, add_to_sprint_1.py, etc.)
After: Single unified interface with clear operations
"""

from enum import Enum

from jira_lib import (
    JiraConfig,
    Sprint,
    SprintState,
    add_issue_to_sprint,
    create_sprint,
    get_board_by_project,
    get_board_sprints,
    load_config,
)


class Operation(Enum):
    """Sprint operations."""

    LIST = "list"
    CREATE = "create"
    ADD_ISSUES = "add"


def list_sprints(config: JiraConfig, project_key: str) -> None:
    """List all sprints for a project.

    Args:
        config: Jira configuration
        project_key: Project key (e.g., BH)
    """
    board, error = get_board_by_project(config, project_key)
    if error:
        print(f"❌ Error finding board: {error}")
        return

    print(f"✅ Found board: {board.name} (ID: {board.id})")
    print()

    sprints, error = get_board_sprints(config, board.id)
    if error:
        print(f"❌ Error fetching sprints: {error}")
        return

    print(f"📊 Found {len(sprints)} sprints:")
    print()

    active_sprint: Sprint | None = None

    for sprint in sprints:
        icon = {
            SprintState.ACTIVE: "🟢",
            SprintState.FUTURE: "🔵",
            SprintState.CLOSED: "⚪",
        }.get(sprint.state, "❓")

        print(f"{icon} {sprint.name} (ID: {sprint.id}) - State: {sprint.state.value}")

        if sprint.state in [SprintState.ACTIVE, SprintState.FUTURE]:
            active_sprint = sprint

    print()

    if active_sprint:
        print(f"✅ Active/Future sprint: {active_sprint.name} (ID: {active_sprint.id})")
        print(f"   State: {active_sprint.state.value}")
    else:
        print("⚠️  No active or future sprint found")


def create_new_sprint(
    config: JiraConfig,
    project_key: str,
    sprint_name: str,
) -> None:
    """Create a new sprint.

    Args:
        config: Jira configuration
        project_key: Project key (e.g., BH)
        sprint_name: Name for new sprint
    """
    board, error = get_board_by_project(config, project_key)
    if error:
        print(f"❌ Error finding board: {error}")
        return

    print(f"✅ Found board: {board.name} (ID: {board.id})")
    print(f"📝 Creating sprint: {sprint_name}...")

    sprint, error = create_sprint(config, board.id, sprint_name)
    if error:
        print(f"❌ Error creating sprint: {error}")
        return

    print(f"✅ Created sprint: {sprint.name} (ID: {sprint.id})")


def add_issues_to_sprint(
    config: JiraConfig,
    sprint_id: int,
    issue_keys: list[str],
) -> None:
    """Add issues to sprint.

    Args:
        config: Jira configuration
        sprint_id: Sprint ID
        issue_keys: List of issue keys to add
    """
    print(f"📝 Adding {len(issue_keys)} issues to sprint {sprint_id}...")
    print()

    success_count = 0

    for issue_key in issue_keys:
        success, error = add_issue_to_sprint(config, issue_key, sprint_id)
        if success:
            print(f"  ✅ {issue_key}")
            success_count += 1
        else:
            print(f"  ❌ {issue_key}: {error}")

    print()
    print(f"✅ Added {success_count}/{len(issue_keys)} issues to sprint")


def main() -> None:
    """Main execution."""
    import sys

    config = load_config()
    project_key = "BH"

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_sprint.py list")
        print("  python manage_sprint.py create <sprint_name>")
        print("  python manage_sprint.py add <sprint_id> <issue_key1> <issue_key2> ...")
        return

    operation = sys.argv[1].lower()

    if operation == "list":
        list_sprints(config, project_key)

    elif operation == "create":
        if len(sys.argv) < 3:
            print("❌ Error: sprint name required")
            print("Usage: python manage_sprint.py create <sprint_name>")
            return

        sprint_name = " ".join(sys.argv[2:])
        create_new_sprint(config, project_key, sprint_name)

    elif operation == "add":
        if len(sys.argv) < 4:
            print("❌ Error: sprint_id and issue keys required")
            print("Usage: python manage_sprint.py add <sprint_id> <issue_key1> <issue_key2> ...")
            return

        try:
            sprint_id = int(sys.argv[2])
        except ValueError:
            print(f"❌ Error: invalid sprint_id '{sys.argv[2]}'")
            return

        issue_keys = sys.argv[3:]
        add_issues_to_sprint(config, sprint_id, issue_keys)

    else:
        print(f"❌ Unknown operation: {operation}")
        print("Valid operations: list, create, add")


if __name__ == "__main__":
    main()
