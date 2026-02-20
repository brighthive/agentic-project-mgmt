"""Tests for CLI assign command (TDD - write tests first)."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from jira_cli.cli import app
from jira_cli.config_loader import AssignmentConfig, TeamMemberConfig
from jira_lib.jira_config import JiraConfig
from jira_lib.jira_models import Issue, IssueStatus, IssueType, Priority, User


def make_test_user(email: str = "test@example.com") -> User:
    """Helper to create test User objects."""
    return User(
        account_id="123",
        display_name="Test User",
        email=email,
    )


def make_test_issue(key: str = "BH-150", assignee: User | None = None) -> Issue:
    """Helper to create test Issue objects."""
    return Issue(
        key=key,
        summary="Test Issue",
        issue_type=IssueType.TASK,
        status=IssueStatus.TODO,
        description="Test description",
        assignee=assignee,
        priority=Priority.MEDIUM,
        labels=[],
        created=datetime.now(),
        updated=datetime.now(),
    )


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_jira_config() -> JiraConfig:
    """Create mock Jira configuration."""
    return JiraConfig(
        base_url="https://test.atlassian.net",
        username="test@example.com",
        token="test-token",
    )


@pytest.fixture
def sample_assignment_config(tmp_path: Path) -> Path:
    """Create sample assignment configuration file."""
    config_file = tmp_path / "assignments.yaml"
    config_file.write_text(
        """
team:
  marwan:
    email: marwan@brighthive.io
    tickets:
      - BH-150
      - BH-151
  ahmed:
    email: ahmed@brighthive.io
    tickets:
      - BH-183
      - BH-184
"""
    )
    return config_file


class TestAssignCommand:
    """Test jira assign command."""

    def test_assign_command_exists(self, runner: CliRunner) -> None:
        """Test that assign command is registered."""
        result = runner.invoke(app, ["assign", "--help"])
        assert result.exit_code == 0
        assert "assign" in result.output.lower()

    def test_assign_requires_config_file(self, runner: CliRunner) -> None:
        """Test that assign command requires --config argument."""
        result = runner.invoke(app, [])
        assert result.exit_code != 0

    @patch("jira_cli.commands.assign.load_config")
    @patch("jira_cli.commands.assign.get_user_by_email")
    @patch("jira_cli.commands.assign.assign_issue")
    def test_assign_with_valid_config(
        self,
        mock_assign: Mock,
        mock_get_user: Mock,
        mock_load_config: Mock,
        runner: CliRunner,
        sample_assignment_config: Path,
        mock_jira_config: JiraConfig,
    ) -> None:
        """Test assign command with valid configuration file."""
        # Setup mocks
        mock_load_config.return_value = mock_jira_config

        # Mock user lookup
        mock_user = make_test_user()
        mock_get_user.return_value = (mock_user, None)

        # Mock successful assignments
        mock_issue = make_test_issue(assignee=mock_user)
        mock_assign.return_value = (mock_issue, None)

        # Run command
        result = runner.invoke(
            app, ["--config", str(sample_assignment_config)]
        )

        # Verify
        assert result.exit_code == 0
        assert "assigned" in result.output.lower() or "successful" in result.output.lower()
        # Should have called assign for all 4 tickets (2 per person)
        assert mock_assign.call_count == 4

    @patch("jira_cli.commands.assign.load_config")
    @patch("jira_cli.commands.assign.get_user_by_email")
    @patch("jira_cli.commands.assign.assign_issue")
    def test_assign_handles_assignment_failure(
        self,
        mock_assign: Mock,
        mock_get_user: Mock,
        mock_load_config: Mock,
        runner: CliRunner,
        sample_assignment_config: Path,
        mock_jira_config: JiraConfig,
    ) -> None:
        """Test assign command handles assignment failures gracefully."""
        # Setup mocks
        mock_load_config.return_value = mock_jira_config

        # Mock user lookup
        from jira_lib.jira_models import JiraError

        mock_user = make_test_user()
        mock_get_user.return_value = (mock_user, None)

        # Mock some failures
        mock_issue = make_test_issue(assignee=mock_user)
        mock_assign.side_effect = [
            (mock_issue, None),  # BH-150 succeeds
            (None, JiraError(message="User not found", status_code=404)),  # BH-151 fails
            (mock_issue, None),  # BH-183 succeeds
            (None, JiraError(message="Permission denied", status_code=403)),  # BH-184 fails
        ]

        # Run command
        result = runner.invoke(
            app, ["--config", str(sample_assignment_config)]
        )

        # Should complete but show errors
        assert "error" in result.output.lower() or "failed" in result.output.lower()
        assert mock_assign.call_count == 4

    def test_assign_with_nonexistent_config(self, runner: CliRunner) -> None:
        """Test assign command with non-existent config file."""
        result = runner.invoke(app, ["--config", "nonexistent.yaml"])
        assert result.exit_code != 0
        output_lower = result.output.lower() if result.output else ""
        assert "not found" in output_lower or "error" in output_lower or "does not exist" in output_lower

    def test_assign_with_invalid_yaml(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test assign command with invalid YAML."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("{ invalid yaml [")

        result = runner.invoke(app, ["--config", str(config_file)])
        assert result.exit_code != 0

    def test_assign_with_invalid_schema(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test assign command with YAML that doesn't match schema."""
        config_file = tmp_path / "invalid_schema.yaml"
        config_file.write_text(
            """
team:
  marwan:
    email: not-an-email
    tickets:
      - BH-150
"""
        )

        result = runner.invoke(app, ["--config", str(config_file)])
        assert result.exit_code != 0
        assert "validation" in result.output.lower() or "invalid" in result.output.lower()

    @patch("jira_cli.commands.assign.load_config")
    @patch("jira_cli.commands.assign.get_user_by_email")
    def test_assign_handles_user_lookup_failure(
        self,
        mock_get_user: Mock,
        mock_load_config: Mock,
        runner: CliRunner,
        sample_assignment_config: Path,
        mock_jira_config: JiraConfig,
    ) -> None:
        """Test assign command when user email lookup fails."""
        # Setup mocks
        mock_load_config.return_value = mock_jira_config

        # Mock user lookup failure
        from jira_lib.jira_models import JiraError
        mock_get_user.return_value = (None, JiraError(message="User not found in Jira", status_code=404))

        # Run command
        result = runner.invoke(
            app, ["--config", str(sample_assignment_config)]
        )

        # Should show error about user lookup
        assert "error" in result.output.lower() or "not found" in result.output.lower()

    @patch("jira_cli.commands.assign.load_config")
    @patch("jira_cli.commands.assign.get_user_by_email")
    @patch("jira_cli.commands.assign.assign_issue")
    def test_assign_shows_progress(
        self,
        mock_assign: Mock,
        mock_get_user: Mock,
        mock_load_config: Mock,
        runner: CliRunner,
        sample_assignment_config: Path,
        mock_jira_config: JiraConfig,
    ) -> None:
        """Test that assign command shows progress during execution."""
        # Setup mocks
        mock_load_config.return_value = mock_jira_config

        # Mock user lookup
        mock_user = make_test_user()
        mock_get_user.return_value = (mock_user, None)

        # Mock successful assignments
        mock_issue = make_test_issue(assignee=mock_user)
        mock_assign.return_value = (mock_issue, None)

        # Run command
        result = runner.invoke(
            app, ["--config", str(sample_assignment_config)]
        )

        # Should show progress indicators
        stdout_lower = result.output.lower()
        assert any(
            indicator in stdout_lower
            for indicator in ["processing", "assigning", "assigned", "✓", "✅", "successful"]
        )
