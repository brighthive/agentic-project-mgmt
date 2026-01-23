"""Configuration loader with Pydantic validation for YAML configs."""

from pathlib import Path

import yaml
from pydantic import BaseModel, EmailStr, field_validator


class TeamMemberConfig(BaseModel):
    """Team member configuration with validated email and tickets."""

    email: EmailStr
    tickets: list[str]

    @field_validator("tickets")
    @classmethod
    def tickets_not_empty(cls, v: list[str]) -> list[str]:
        """Validate that tickets list is not empty."""
        if not v:
            raise ValueError("tickets list cannot be empty")
        return v


class AssignmentConfig(BaseModel):
    """Assignment configuration with team members."""

    team: dict[str, TeamMemberConfig]

    @field_validator("team")
    @classmethod
    def team_not_empty(cls, v: dict[str, TeamMemberConfig]) -> dict[str, TeamMemberConfig]:
        """Validate that team dict is not empty."""
        if not v:
            raise ValueError("team dict cannot be empty")
        return v


class SprintConfig(BaseModel):
    """Sprint configuration with name and tickets."""

    sprint_name: str
    tickets: list[str]

    @field_validator("tickets")
    @classmethod
    def tickets_not_empty(cls, v: list[str]) -> list[str]:
        """Validate that tickets list is not empty."""
        if not v:
            raise ValueError("tickets list cannot be empty")
        return v


def load_assignment_config(config_path: Path) -> AssignmentConfig:
    """Load assignment configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated AssignmentConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
        pydantic.ValidationError: If config doesn't match schema
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return AssignmentConfig(**data)


def load_sprint_config(config_path: Path) -> SprintConfig:
    """Load sprint configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated SprintConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
        pydantic.ValidationError: If config doesn't match schema
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    return SprintConfig(**data)
