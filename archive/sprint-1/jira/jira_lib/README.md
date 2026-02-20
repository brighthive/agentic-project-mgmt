# jira_lib - Functional Jira API Library

A clean, type-safe, functional API for Jira automation built on pure functions, immutable data, and explicit error handling.

## Features

- **Pure Functions**: No hidden side effects, easy to reason about
- **Type Safety**: Full type hints with Pydantic models
- **Immutable Data**: Frozen dataclasses prevent accidental mutations
- **Explicit Errors**: Result tuples instead of exceptions
- **Composable**: Build complex operations from simple functions
- **Testable**: Pure functions are easy to test

## Installation

```bash
cd /Users/bado/iccha/brighthive/project/sprint/sprint-1/jira
uv pip install -e .
```

## Quick Start

```python
from jira_lib import (
    load_config,
    get_user_by_email,
    assign_issue,
    search_issues,
)

# Load configuration
config = load_config()

# Find a user
user, error = get_user_by_email(config, "user@example.com")
if error:
    print(f"Error: {error}")
    exit(1)

# Assign a ticket
success, error = assign_issue(config, "BH-123", user)
if not success:
    print(f"Assignment failed: {error}")
    exit(1)

print(f"✅ Assigned BH-123 to {user.display_name}")

# Search for issues
issues, error = search_issues(
    config,
    jql="project = BH AND status = 'To Do'",
    max_results=50,
)

for issue in issues:
    print(f"{issue.key}: {issue.summary}")
```

## Architecture

```
jira_lib/
├── __init__.py           # Public API
├── jira_config.py        # Configuration loading
├── jira_models.py        # Type-safe models
├── jira_client.py        # Low-level HTTP client
├── jira_operations.py    # High-level operations
└── adf_builder.py        # ADF document builders
```

### Layers

1. **Config Layer** (`jira_config.py`)
   - Load and validate configuration
   - Immutable `JiraConfig` dataclass

2. **Model Layer** (`jira_models.py`)
   - Type-safe models: `User`, `Issue`, `Sprint`, `Board`
   - Enums for statuses, priorities, types
   - Immutable dataclasses

3. **Client Layer** (`jira_client.py`)
   - Low-level HTTP operations
   - Result types: `tuple[data | None, error | None]`
   - Pure functions with explicit error handling

4. **Operations Layer** (`jira_operations.py`)
   - High-level composable operations
   - Built on top of client layer
   - Business logic and common workflows

5. **Builder Layer** (`adf_builder.py`)
   - Atlassian Document Format builders
   - Pure functions for creating structured documents
   - Composable document creation

## Core Concepts

### Immutable Data Structures

All data structures are frozen dataclasses:

```python
@dataclass(frozen=True)
class User:
    account_id: str
    display_name: str
    email: str | None = None
```

This prevents accidental mutations and makes code more predictable.

### Result Types (Explicit Error Handling)

Instead of exceptions, functions return result tuples:

```python
Result = tuple[T | None, JiraError | None]

user, error = get_user_by_email(config, "user@example.com")
if error:
    # Handle error
    print(f"Error: {error}")
    return

# Use user safely (type checker knows it's not None)
print(user.display_name)
```

Benefits:
- Explicit error handling (can't forget to check)
- Type-safe (mypy knows when values are valid)
- No hidden control flow (no exceptions to catch)

### Pure Functions

Core functions have no side effects:

```python
def load_config(config_path: Path) -> JiraConfig:
    """Pure function - same input always gives same output."""
    # Reads file but returns immutable config
    # Raises exceptions only for configuration errors

def verify_assignment(
    config: JiraConfig,
    issue_key: str,
    expected_user: User,
) -> tuple[bool, JiraError | None]:
    """Pure function - no side effects, explicit dependencies."""
    # All dependencies passed as arguments
    # Returns result tuple instead of raising exceptions
```

### Composable Operations

Small functions compose into larger operations:

```python
def assign_team_tickets(
    config: JiraConfig,
    tickets: list[str],
    user: User,
) -> tuple[int, int]:
    """Compose assign_issue for bulk operations."""
    success_count = 0

    for ticket in tickets:
        success, error = assign_issue(config, ticket, user)
        if success:
            success_count += 1

    return (success_count, len(tickets))
```

## API Reference

### Configuration

```python
from jira_lib import JiraConfig, load_config

# Load from default location (~/.config/jiratui/config.yaml)
config = load_config()

# Load from custom path
from pathlib import Path
config = load_config(Path("/path/to/config.yaml"))

# Access properties
print(config.base_url)
print(config.username)
auth_tuple = config.auth  # (username, token)
```

### User Operations

```python
from jira_lib import get_user_by_email, get_user_by_email_with_fallbacks

# Single email
user, error = get_user_by_email(config, "user@example.com")

# Multiple email fallbacks
user, error = get_user_by_email_with_fallbacks(
    config,
    ["user@company.com", "user.name@company.com", "user@old.com"],
)
```

### Issue Operations

```python
from jira_lib import (
    get_issue,
    search_issues,
    assign_issue,
    create_issue,
    verify_assignment,
    IssueType,
    Priority,
)

# Get single issue
issue, error = get_issue(config, "BH-123")
if issue:
    print(f"{issue.key}: {issue.summary}")
    print(f"Status: {issue.status.value}")
    print(f"Assignee: {issue.assignee.display_name if issue.assignee else 'Unassigned'}")

# Search issues
issues, error = search_issues(
    config,
    jql="project = BH AND status = 'In Progress'",
    max_results=100,
)

# Assign issue
success, error = assign_issue(config, "BH-123", user)

# Create issue
issue, error = create_issue(
    config,
    project_key="BH",
    summary="New task",
    issue_type=IssueType.TASK,
    description="Task description",
    priority=Priority.HIGH,
    assignee=user,
    labels=["sprint-1", "backend"],
)

# Verify assignment
is_correct, error = verify_assignment(config, "BH-123", expected_user)
```

### Sprint Operations

```python
from jira_lib import (
    get_board_by_project,
    get_board_sprints,
    create_sprint,
    add_issue_to_sprint,
    SprintState,
)

# Get board
board, error = get_board_by_project(config, "BH")

# Get sprints
sprints, error = get_board_sprints(config, board.id)
active_sprints, error = get_board_sprints(config, board.id, state=SprintState.ACTIVE)

# Create sprint
sprint, error = create_sprint(config, board.id, "Sprint 2 (Jan 27 - Feb 7)")

# Add issues to sprint
success, error = add_issue_to_sprint(config, "BH-123", sprint.id)
```

### ADF Document Building

```python
from jira_lib import (
    document,
    heading,
    paragraph,
    bullet_list,
    ordered_list,
    code_block,
    bold,
    code,
)

# Simple document
doc = document(
    heading("Overview", level=2),
    paragraph("This is a task description"),
)

# Complex document
doc = document(
    heading("Task Description", level=2),
    paragraph("This task involves the following work:"),

    heading("Requirements", level=3),
    bullet_list([
        "Implement user authentication",
        "Add password reset flow",
        "Write tests",
    ]),

    heading("Technical Notes", level=3),
    paragraph("Use the following approach:"),
    code_block(
        "def authenticate(username, password):\n    # Implementation here\n    pass",
        language="python",
    ),

    heading("Acceptance Criteria", level=3),
    ordered_list([
        "Users can log in",
        "Users can reset password",
        "All tests pass",
    ]),
)

# Use in issue creation
issue, error = create_issue(
    config,
    project_key="BH",
    summary="Implement authentication",
    issue_type=IssueType.STORY,
    description=doc,  # ADF document
)
```

### Inline ADF Formatting

```python
from jira_lib import paragraph, bold, code

# Paragraph with mixed formatting
para = paragraph(
    "The function ",
    code("authenticate()"),
    " is ",
    bold("critical"),
    " for security.",
)
```

## Error Handling Patterns

### Pattern 1: Early Return

```python
def process_ticket(config: JiraConfig, ticket_key: str) -> None:
    issue, error = get_issue(config, ticket_key)
    if error:
        print(f"Error: {error}")
        return

    # issue is guaranteed to be valid here
    print(f"Processing {issue.key}: {issue.summary}")
```

### Pattern 2: Accumulate Errors

```python
def assign_multiple(
    config: JiraConfig,
    tickets: list[str],
    user: User,
) -> tuple[int, list[str]]:
    """Return success count and list of failed tickets."""
    failed = []

    for ticket in tickets:
        success, error = assign_issue(config, ticket, user)
        if not success:
            failed.append(ticket)

    return (len(tickets) - len(failed), failed)
```

### Pattern 3: Fallback on Error

```python
def get_user_resilient(config: JiraConfig, emails: list[str]) -> User | None:
    """Try multiple emails, return first successful match."""
    for email in emails:
        user, error = get_user_by_email(config, email)
        if user:
            return user

    return None
```

## Testing

The library is designed for testability:

```python
# Pure functions are easy to test
def test_verify_assignment_with_mock():
    config = JiraConfig("https://test", "user", "token")
    user = User("123", "Test User")

    # Mock at the boundary (get_issue)
    with mock.patch('jira_lib.operations.get_issue') as mock_get:
        mock_issue = Issue(
            key="BH-1",
            assignee=user,
            # ... other fields
        )
        mock_get.return_value = (mock_issue, None)

        is_correct, error = verify_assignment(config, "BH-1", user)
        assert is_correct
        assert error is None
```

Run tests:

```bash
cd /Users/bado/iccha/brighthive/project/sprint/sprint-1/jira
uv run pytest tests/ -v
```

## Examples

See `scripts/refactored/` for complete examples:

- `assign_tickets.py` - Bulk ticket assignment with verification
- `verify_assignments.py` - Verify ticket assignments
- `manage_sprint.py` - Sprint management CLI

## Type Checking

The library has 100% type coverage:

```bash
uv run mypy scripts/jira_lib/
```

## Design Philosophy

### 1. Functional Core, Imperative Shell

- **Core**: Pure functions with no I/O (models, builders)
- **Shell**: I/O at the edges (client, operations)

### 2. Make Illegal States Unrepresentable

Use types to prevent errors:

```python
# Can't create invalid issue type
issue_type = IssueType.TASK  # ✅ Valid
issue_type = "task"  # ❌ Type error

# Can't forget to handle errors
user, error = get_user_by_email(config, "...")
print(user.display_name)  # ⚠️  Mypy error: user might be None
```

### 3. Explicit Over Implicit

- No hidden configuration (pass `config` explicitly)
- No silent failures (return errors explicitly)
- No magic (all behavior is visible in function signatures)

### 4. Composition Over Inheritance

Build complex operations by composing simple functions:

```python
def assign_and_verify(
    config: JiraConfig,
    ticket: str,
    user: User,
) -> bool:
    """Compose assign + verify operations."""
    success, error = assign_issue(config, ticket, user)
    if not success:
        return False

    is_correct, error = verify_assignment(config, ticket, user)
    return is_correct
```

## Contributing

When adding new operations:

1. **Start with models** - Add any new types to `jira_models.py`
2. **Add client method** - Low-level HTTP operation in `jira_client.py`
3. **Add operation** - High-level function in `jira_operations.py`
4. **Add tests** - Pure function tests in `tests/`
5. **Update exports** - Add to `__init__.py`

Follow these principles:

- Pure functions where possible
- Immutable data structures
- Explicit error handling (Result types)
- Full type hints
- Comprehensive docstrings

## License

Internal use only - BrightHive

## Version

0.1.0 (Initial functional refactoring)
