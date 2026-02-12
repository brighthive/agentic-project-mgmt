"""Unit tests for models module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from models import AWSSecret, Environment, SecretCategory, SecretSource


def test_secret_creation():
    secret = AWSSecret(
        id="arn:aws:secretsmanager:us-east-1:123:secret:test",
        name="my-test-secret",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert secret.id == "arn:aws:secretsmanager:us-east-1:123:secret:test"
    assert secret.name == "my-test-secret"
    assert secret.environment == Environment.PROD


def test_auto_categorization_aws_credential():
    secret = AWSSecret(
        id="arn:1",
        name="cdk-admin-secret/123456789012",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert secret.category == SecretCategory.AWS_CREDENTIAL


def test_auto_categorization_database():
    for name in ["prod-rds-credentials", "neo4j-connection", "redshift-admin", "postgres-main"]:
        secret = AWSSecret(
            id=f"arn:{name}",
            name=name,
            environment=Environment.PROD,
            source=SecretSource.SECRETS_MANAGER,
        )
        assert secret.category == SecretCategory.DATABASE, f"Expected DATABASE for {name}"


def test_auto_categorization_api_key():
    secret = AWSSecret(
        id="arn:2",
        name="sendgrid-api-key",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert secret.category == SecretCategory.API_KEY


def test_auto_categorization_third_party():
    secret = AWSSecret(
        id="arn:3",
        name="stripe-webhook-config",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert secret.category == SecretCategory.THIRD_PARTY


def test_auto_categorization_unknown():
    secret = AWSSecret(
        id="arn:4",
        name="random-thing",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert secret.category == SecretCategory.UNKNOWN


def test_environment_detection_from_name():
    secret = AWSSecret(
        id="arn:5",
        name="dev-neo4j-connection",
        environment=Environment.UNKNOWN,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert secret.environment == Environment.DEV


def test_environment_detection_explicit_wins():
    secret = AWSSecret(
        id="arn:6",
        name="dev-neo4j-connection",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
    )

    # Explicit non-UNKNOWN takes priority
    assert secret.environment == Environment.PROD


def test_environment_detection_staging():
    secret = AWSSecret(
        id="arn:7",
        name="stg-rds-credentials",
        environment=Environment.UNKNOWN,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert secret.environment == Environment.STG


def test_to_dict():
    secret = AWSSecret(
        id="arn:8",
        name="test-secret",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
        description="A test secret",
        tags={"env": "prod"},
        account_number="123456",
        secret_value={"accessKeyID": "AKIA...", "secretAccessKey": "wJalr..."},
    )

    data = secret.to_dict()
    assert isinstance(data, dict)
    assert data["id"] == "arn:8"
    assert data["environment"] == "prod"
    assert data["source"] == "secrets_manager"
    assert data["tags"] == {"env": "prod"}
    assert data["account_number"] == "123456"
    assert data["secret_value"]["accessKeyID"] == "AKIA..."


def test_from_dict():
    data = {
        "id": "arn:9",
        "name": "cdk-admin-secret/999999",
        "environment": "prod",
        "source": "dynamodb_cross_ref",
        "description": "Account cred",
        "created_date": "2025-01-01",
        "last_changed_date": None,
        "last_accessed_date": None,
        "tags": {},
        "account_number": "999999",
        "account_name": "TestAccount",
        "account_type": "Organization",
        "secret_value": {"accessKeyID": "AKIA123"},
    }

    secret = AWSSecret.from_dict(data=data)
    assert secret.id == "arn:9"
    assert secret.category == SecretCategory.AWS_CREDENTIAL
    assert secret.environment == Environment.PROD
    assert secret.source == SecretSource.DYNAMODB_CROSS_REF
    assert secret.account_number == "999999"
    assert secret.secret_value == {"accessKeyID": "AKIA123"}


def test_roundtrip_serialization():
    original = AWSSecret(
        id="arn:10",
        name="prod-rds-main",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
        description="Main RDS",
        tags={"team": "platform"},
        secret_value={"host": "db.example.com", "port": 5432, "password": "s3cret"},
    )

    data = original.to_dict()
    restored = AWSSecret.from_dict(data=data)

    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.category == original.category
    assert restored.environment == original.environment
    assert restored.normalized_name == original.normalized_name
    assert restored.secret_value == original.secret_value


def test_normalized_name():
    secret = AWSSecret(
        id="arn:11",
        name="cdk-admin-secret/123456789012",
        environment=Environment.PROD,
        source=SecretSource.SECRETS_MANAGER,
    )

    assert "/" in secret.normalized_name or "_" in secret.normalized_name
    assert secret.normalized_name == secret.normalized_name.lower()
