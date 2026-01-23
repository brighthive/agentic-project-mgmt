"""Configuration loading for Jira API client.

Pure functional configuration loading with immutable data structures.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml


@dataclass(frozen=True)
class JiraConfig:
    """Immutable Jira configuration.

    Attributes:
        base_url: Jira API base URL (e.g., https://brighthiveio.atlassian.net)
        username: Jira API username (email)
        token: Jira API token
    """

    base_url: str
    username: str
    token: str

    @property
    def auth(self) -> tuple[str, str]:
        """Return auth tuple for requests library."""
        return (self.username, self.token)


DEFAULT_CONFIG_PATH: Final[Path] = Path.home() / ".config/jiratui/config.yaml"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> JiraConfig:
    """Load Jira configuration from YAML file.

    Args:
        config_path: Path to config YAML file

    Returns:
        Immutable JiraConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        KeyError: If required config keys are missing
        ValueError: If config values are invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    if not isinstance(raw_config, dict):
        raise ValueError("Config file must contain a YAML dictionary")

    try:
        config = JiraConfig(
            base_url=raw_config["jira_api_base_url"].rstrip("/"),
            username=raw_config["jira_api_username"],
            token=raw_config["jira_api_token"],
        )
    except KeyError as e:
        raise KeyError(f"Missing required config key: {e}") from e

    if not config.base_url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid base_url: {config.base_url}")

    if not config.username:
        raise ValueError("username cannot be empty")

    if not config.token:
        raise ValueError("token cannot be empty")

    return config
