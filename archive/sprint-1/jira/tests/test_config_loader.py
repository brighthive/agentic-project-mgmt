"""Tests for YAML configuration loader (TDD - write tests first)."""

import pytest
from pathlib import Path
from pydantic import ValidationError
from jira_cli.config_loader import (
    AssignmentConfig,
    TeamMemberConfig,
    SprintConfig,
    load_assignment_config,
    load_sprint_config,
)


class TestTeamMemberConfig:
    """Test TeamMemberConfig model."""

    def test_valid_team_member(self) -> None:
        """Test valid team member configuration."""
        config = TeamMemberConfig(
            email="marwan@brighthive.io",
            tickets=["BH-150", "BH-151"]
        )
        assert config.email == "marwan@brighthive.io"
        assert config.tickets == ["BH-150", "BH-151"]

    def test_team_member_requires_email(self) -> None:
        """Test that email is required."""
        with pytest.raises(ValidationError):
            TeamMemberConfig(tickets=["BH-150"])  # type: ignore

    def test_team_member_requires_tickets(self) -> None:
        """Test that tickets list is required."""
        with pytest.raises(ValidationError):
            TeamMemberConfig(email="test@example.com")  # type: ignore

    def test_team_member_empty_tickets_invalid(self) -> None:
        """Test that empty tickets list is invalid."""
        with pytest.raises(ValidationError):
            TeamMemberConfig(
                email="test@example.com",
                tickets=[]
            )

    def test_team_member_email_validation(self) -> None:
        """Test that invalid emails are rejected."""
        with pytest.raises(ValidationError):
            TeamMemberConfig(
                email="not-an-email",
                tickets=["BH-150"]
            )


class TestAssignmentConfig:
    """Test AssignmentConfig model."""

    def test_valid_assignment_config(self) -> None:
        """Test valid assignment configuration."""
        config = AssignmentConfig(
            team={
                "marwan": TeamMemberConfig(
                    email="marwan@brighthive.io",
                    tickets=["BH-150", "BH-151"]
                ),
                "ahmed": TeamMemberConfig(
                    email="ahmed@brighthive.io",
                    tickets=["BH-183", "BH-184"]
                )
            }
        )
        assert "marwan" in config.team
        assert "ahmed" in config.team
        assert config.team["marwan"].email == "marwan@brighthive.io"

    def test_assignment_config_requires_team(self) -> None:
        """Test that team is required."""
        with pytest.raises(ValidationError):
            AssignmentConfig()  # type: ignore

    def test_assignment_config_empty_team_invalid(self) -> None:
        """Test that empty team dict is invalid."""
        with pytest.raises(ValidationError):
            AssignmentConfig(team={})


class TestSprintConfig:
    """Test SprintConfig model."""

    def test_valid_sprint_config(self) -> None:
        """Test valid sprint configuration."""
        config = SprintConfig(
            sprint_name="Sprint 1",
            tickets=["BH-150", "BH-151", "BH-152"]
        )
        assert config.sprint_name == "Sprint 1"
        assert len(config.tickets) == 3

    def test_sprint_config_requires_name(self) -> None:
        """Test that sprint_name is required."""
        with pytest.raises(ValidationError):
            SprintConfig(tickets=["BH-150"])  # type: ignore

    def test_sprint_config_requires_tickets(self) -> None:
        """Test that tickets list is required."""
        with pytest.raises(ValidationError):
            SprintConfig(sprint_name="Sprint 1")  # type: ignore

    def test_sprint_config_empty_tickets_invalid(self) -> None:
        """Test that empty tickets list is invalid."""
        with pytest.raises(ValidationError):
            SprintConfig(
                sprint_name="Sprint 1",
                tickets=[]
            )


class TestLoadAssignmentConfig:
    """Test load_assignment_config function."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        """Test loading valid YAML configuration."""
        config_file = tmp_path / "assignments.yaml"
        config_file.write_text("""
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
""")

        config = load_assignment_config(config_file)

        assert config is not None
        assert "marwan" in config.team
        assert "ahmed" in config.team
        assert config.team["marwan"].email == "marwan@brighthive.io"
        assert len(config.team["marwan"].tickets) == 2

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading non-existent file raises error."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_assignment_config(config_file)

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        """Test loading invalid YAML raises error."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("{ invalid yaml [")

        with pytest.raises(Exception):  # YAML parse error
            load_assignment_config(config_file)

    def test_load_yaml_missing_required_fields(self, tmp_path: Path) -> None:
        """Test loading YAML with missing required fields."""
        config_file = tmp_path / "incomplete.yaml"
        config_file.write_text("""
team:
  marwan:
    email: marwan@brighthive.io
    # Missing tickets field
""")

        with pytest.raises(ValidationError):
            load_assignment_config(config_file)


class TestLoadSprintConfig:
    """Test load_sprint_config function."""

    def test_load_valid_sprint_yaml(self, tmp_path: Path) -> None:
        """Test loading valid sprint YAML configuration."""
        config_file = tmp_path / "sprint.yaml"
        config_file.write_text("""
sprint_name: Sprint 1
tickets:
  - BH-150
  - BH-151
  - BH-152
""")

        config = load_sprint_config(config_file)

        assert config is not None
        assert config.sprint_name == "Sprint 1"
        assert len(config.tickets) == 3
        assert "BH-150" in config.tickets

    def test_load_sprint_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading non-existent sprint file raises error."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_sprint_config(config_file)
