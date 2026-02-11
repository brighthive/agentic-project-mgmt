"""Unit tests for aws_client module (mocked AWS calls)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from aws_client import AWSSecretsClient
from models import Environment, SecretCategory, SecretSource


def _make_mock_client() -> AWSSecretsClient:
    """Create a client with mocked boto3 session."""
    with patch("aws_client.boto3.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_sm = MagicMock()
        mock_dynamodb = MagicMock()
        mock_session.client.side_effect = lambda service, **kw: (
            mock_sm if service == "secretsmanager" else mock_dynamodb
        )

        client = AWSSecretsClient(
            profile="test-profile",
            region="us-east-1",
            environment=Environment.PROD,
        )
        client._mock_sm = mock_sm
        client._mock_dynamodb = mock_dynamodb

    return client


def test_list_all_secrets():
    client = _make_mock_client()

    paginator = MagicMock()
    client._mock_sm.get_paginator.return_value = paginator
    paginator.paginate.return_value = [
        {
            "SecretList": [
                {
                    "ARN": "arn:aws:secretsmanager:us-east-1:123:secret:prod-neo4j",
                    "Name": "prod-neo4j-connection",
                    "Description": "Neo4j credentials",
                    "Tags": [{"Key": "env", "Value": "prod"}],
                    "CreatedDate": "2025-01-01T00:00:00Z",
                    "LastChangedDate": None,
                    "LastAccessedDate": None,
                },
                {
                    "ARN": "arn:aws:secretsmanager:us-east-1:123:secret:cdk-admin",
                    "Name": "cdk-admin-secret/999999",
                    "Description": "",
                    "Tags": [],
                },
            ]
        }
    ]

    # Rebind the mocked SM client
    client._sm = client._mock_sm

    secrets = client.list_all_secrets()

    assert len(secrets) == 2
    assert secrets[0].name == "prod-neo4j-connection"
    assert secrets[0].category == SecretCategory.DATABASE
    assert secrets[0].source == SecretSource.SECRETS_MANAGER
    assert secrets[1].category == SecretCategory.AWS_CREDENTIAL


def test_get_secret_value_json():
    client = _make_mock_client()
    client._sm = client._mock_sm

    client._mock_sm.get_secret_value.return_value = {
        "SecretString": '{"accessKeyID": "AKIA...", "secretAccessKey": "wJalr..."}'
    }

    value = client.get_secret_value(secret_id="cdk-admin-secret/123")

    assert isinstance(value, dict)
    assert "accessKeyID" in value


def test_get_secret_value_plain_string():
    client = _make_mock_client()
    client._sm = client._mock_sm

    client._mock_sm.get_secret_value.return_value = {
        "SecretString": "plain-text-secret"
    }

    value = client.get_secret_value(secret_id="some-secret")

    assert value == "plain-text-secret"


def test_scan_accounts_table():
    client = _make_mock_client()
    client._dynamodb = client._mock_dynamodb

    client._mock_dynamodb.scan.return_value = {
        "Items": [
            {
                "AWSAccountNumber": {"S": "111111111111"},
                "AWSAccountName": {"S": "OrgAccount"},
                "type": {"S": "Organization"},
                "EnvSecretArn": {"S": "arn:aws:secretsmanager:us-east-1:123:secret:cdk-admin-secret/111"},
            },
            {
                "AWSAccountNumber": {"S": "222222222222"},
                "AWSAccountName": {"S": "WorkspaceAccount"},
                "type": {"S": "Workspace"},
            },
        ]
    }

    accounts = client._scan_accounts_table(table_name="PlatformAccountsTable")

    assert len(accounts) == 2
    assert accounts[0]["account_number"] == "111111111111"
    assert accounts[0]["account_type"] == "Organization"
    assert "env_secret_arn" in accounts[0]
    assert accounts[1]["account_type"] == "Workspace"


def test_scan_accounts_table_with_type_filter():
    client = _make_mock_client()
    client._dynamodb = client._mock_dynamodb

    client._mock_dynamodb.scan.return_value = {
        "Items": [
            {
                "AWSAccountNumber": {"S": "111111111111"},
                "AWSAccountName": {"S": "OrgAccount"},
                "type": {"S": "Organization"},
            },
        ]
    }

    accounts = client._scan_accounts_table(
        table_name="PlatformAccountsTable",
        account_type="Organization",
    )

    # Verify filter expression was passed
    call_kwargs = client._mock_dynamodb.scan.call_args.kwargs
    assert call_kwargs["FilterExpression"] == "#type = :type_val"
    assert len(accounts) == 1
