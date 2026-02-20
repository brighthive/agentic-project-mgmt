"""Tests for jira_config module.

Pure function tests - no mocking needed.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from jira_lib.jira_config import JiraConfig, load_config


def test_jira_config_immutable() -> None:
    """Test that JiraConfig is immutable."""
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        username="test@example.com",
        token="secret",
    )

    # Should not be able to modify
    with pytest.raises(Exception):
        config.base_url = "https://other.atlassian.net"  # type: ignore


def test_jira_config_auth_property() -> None:
    """Test auth property returns correct tuple."""
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        username="test@example.com",
        token="secret",
    )

    auth = config.auth
    assert auth == ("test@example.com", "secret")
    assert isinstance(auth, tuple)


def test_load_config_success() -> None:
    """Test loading valid config."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "jira_api_base_url": "https://test.atlassian.net/",
            "jira_api_username": "test@example.com",
            "jira_api_token": "secret123",
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        config = load_config(config_path)

        assert config.base_url == "https://test.atlassian.net"  # Trailing slash removed
        assert config.username == "test@example.com"
        assert config.token == "secret123"
    finally:
        config_path.unlink()


def test_load_config_missing_file() -> None:
    """Test error when config file doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(Path("/nonexistent/config.yaml"))


def test_load_config_missing_keys() -> None:
    """Test error when config is missing required keys."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "jira_api_base_url": "https://test.atlassian.net",
            # Missing username and token
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        with pytest.raises(KeyError, match="Missing required config key"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_config_invalid_base_url() -> None:
    """Test error when base_url is invalid."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "jira_api_base_url": "not-a-url",
            "jira_api_username": "test@example.com",
            "jira_api_token": "secret",
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Invalid base_url"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_config_empty_username() -> None:
    """Test error when username is empty."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "jira_api_base_url": "https://test.atlassian.net",
            "jira_api_username": "",
            "jira_api_token": "secret",
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="username cannot be empty"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_config_empty_token() -> None:
    """Test error when token is empty."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "jira_api_base_url": "https://test.atlassian.net",
            "jira_api_username": "test@example.com",
            "jira_api_token": "",
        }
        yaml.dump(config_data, f)
        config_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="token cannot be empty"):
            load_config(config_path)
    finally:
        config_path.unlink()
