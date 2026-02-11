"""Unit tests for config module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from config import load_config


def test_config_defaults():
    config = load_config(env={})

    assert config.region == "us-east-1"
    assert config.dynamodb_table == "PlatformAccountsTable"
    assert config.main_profile == "brighthive-main"
    assert config.profiles["dev"] == "brighthive-development"
    assert config.profiles["stg"] == "brighthive-staging"
    assert config.profiles["prod"] == "brighthive-production"


def test_config_env_overrides():
    env = {
        "AWS_CLI_ROOT": "/tmp/aws-cli",
        "AWS_CLI_DATA_DIR": "/tmp/aws-data",
        "AWS_CLI_REGION": "eu-west-1",
        "AWS_CLI_DYNAMODB_TABLE": "CustomTable",
        "AWS_CLI_PROFILE_MAIN": "custom-main",
        "AWS_CLI_PROFILE_DEV": "custom-dev",
    }

    config = load_config(env=env)

    assert config.root_dir == Path("/tmp/aws-cli")
    assert config.data_dir == Path("/tmp/aws-data")
    assert config.region == "eu-west-1"
    assert config.dynamodb_table == "CustomTable"
    assert config.main_profile == "custom-main"
    assert config.profiles["dev"] == "custom-dev"
    assert config.profiles["stg"] == "brighthive-staging"  # unchanged


def test_config_catalog_path():
    config = load_config(env={})
    assert config.catalog_path == config.data_dir / "catalog.json"
