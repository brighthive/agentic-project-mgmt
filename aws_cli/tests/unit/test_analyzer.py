"""Unit tests for analyzer module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from analyzer import SecretsAnalyzer
from models import AWSSecret, Environment, SecretSource


def _make_secret(
    secret_id: str,
    name: str,
    env: Environment = Environment.PROD,
    account_number: str | None = None,
    source: SecretSource = SecretSource.SECRETS_MANAGER,
) -> AWSSecret:
    return AWSSecret(
        id=secret_id,
        name=name,
        environment=env,
        source=source,
        account_number=account_number,
    )


def test_find_duplicates_same_name_cross_env():
    analyzer = SecretsAnalyzer()

    s1 = _make_secret(secret_id="arn:1", name="neo4j-connection", env=Environment.PROD)
    s2 = _make_secret(secret_id="arn:2", name="neo4j-connection", env=Environment.DEV)

    duplicates = analyzer.find_duplicates(secrets=[s1, s2])

    assert len(duplicates) == 1
    assert duplicates[0].confidence == 1.0
    assert "envs" in duplicates[0].reason


def test_find_duplicates_same_account_different_source():
    analyzer = SecretsAnalyzer()

    s1 = _make_secret(
        secret_id="arn:1",
        name="cdk-admin-secret/123",
        account_number="123",
        source=SecretSource.SECRETS_MANAGER,
    )
    s2 = _make_secret(
        secret_id="arn:2",
        name="account-123-creds",
        account_number="123",
        source=SecretSource.DYNAMODB_CROSS_REF,
    )

    duplicates = analyzer.find_duplicates(secrets=[s1, s2])

    assert len(duplicates) == 1
    assert duplicates[0].confidence == 0.95


def test_find_duplicates_similar_names():
    analyzer = SecretsAnalyzer()

    s1 = _make_secret(secret_id="arn:1", name="brighthive-prod-database")
    s2 = _make_secret(secret_id="arn:2", name="brighthive-prod-database-v2")

    duplicates = analyzer.find_duplicates(secrets=[s1, s2])

    assert len(duplicates) >= 1
    assert duplicates[0].confidence >= 0.85


def test_no_false_positives():
    analyzer = SecretsAnalyzer()

    s1 = _make_secret(secret_id="arn:1", name="neo4j-connection")
    s2 = _make_secret(secret_id="arn:2", name="stripe-api-key")

    duplicates = analyzer.find_duplicates(secrets=[s1, s2])

    assert len(duplicates) == 0


def test_health_score_healthy():
    analyzer = SecretsAnalyzer()

    secrets = [
        _make_secret(secret_id="arn:1", name="cdk-admin-secret/111"),
        _make_secret(secret_id="arn:2", name="prod-neo4j-connection"),
    ]

    # Add descriptions to avoid penalty
    for s in secrets:
        s.description = "A described secret"
        # Re-trigger post_init won't help, so set directly
    secrets[0].description = "Credential"
    secrets[1].description = "Database"

    health = analyzer.get_health_score(secrets=secrets)

    assert health["overall_score"] >= 0
    assert health["overall_score"] <= 100
    assert health["total_secrets"] == 2


def test_health_score_empty():
    analyzer = SecretsAnalyzer()

    health = analyzer.get_health_score(secrets=[])

    assert health["overall_score"] == 100.0
    assert health["total_secrets"] == 0


def test_find_cross_env_secrets():
    analyzer = SecretsAnalyzer()

    s1 = _make_secret(secret_id="arn:1", name="neo4j-connection", env=Environment.PROD)
    s2 = _make_secret(secret_id="arn:2", name="neo4j-connection", env=Environment.DEV)
    s3 = _make_secret(secret_id="arn:3", name="stripe-api-key", env=Environment.PROD)

    cross_env = analyzer.find_cross_env_secrets(secrets=[s1, s2, s3])

    # neo4j-connection should appear in cross-env results
    assert len(cross_env) >= 1
