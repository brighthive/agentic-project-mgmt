"""Unit tests for secret classifier."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from classifier import SecretClassifier
from models import SecretType


def test_database_password_classification():
    """Test database password classification."""
    classifier = SecretClassifier()

    # Test name-based classification
    result = classifier.classify("redshift_admin_password")
    assert result.secret_type == SecretType.DATABASE_PASSWORD
    assert result.confidence > 0.8

    result = classifier.classify("rds_db_password")
    assert result.secret_type == SecretType.DATABASE_PASSWORD

    result = classifier.classify("postgres_password")
    assert result.secret_type == SecretType.DATABASE_PASSWORD


def test_api_key_classification():
    """Test API key classification."""
    classifier = SecretClassifier()

    result = classifier.classify("github_api_key")
    assert result.secret_type == SecretType.API_KEY

    result = classifier.classify("openmetadata_api_token")
    assert result.secret_type == SecretType.API_KEY


def test_ssh_key_classification():
    """Test SSH key classification."""
    classifier = SecretClassifier()

    # Name-based
    result = classifier.classify("id_rsa")
    assert result.secret_type == SecretType.SSH_KEY
    assert result.confidence >= 0.9

    # Content-based with PEM header (should match regardless of name)
    pem_key = "-----BEGIN OPENSSH PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."
    result = classifier.classify("my_secret", pem_key)
    assert result.secret_type == SecretType.SSH_KEY
    assert result.confidence >= 0.9


def test_connection_string_classification():
    """Test connection string classification."""
    classifier = SecretClassifier()

    result = classifier.classify("redshift_connection_string")
    assert result.secret_type == SecretType.CONNECTION_STRING

    # Content-based
    conn_str = "user=admin password=secret123 host=db.example.com port=5439"
    result = classifier.classify("db_conn", conn_str)
    assert result.secret_type == SecretType.CONNECTION_STRING


def test_jwt_token_classification():
    """Test JWT/OAuth token classification."""
    classifier = SecretClassifier()

    result = classifier.classify("jwt_token")
    assert result.secret_type == SecretType.OAUTH_TOKEN

    # JWT format
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.TJVA95OrM7E2cBab30RMHrHDcEfxjoYZgeFONFh7HgQ"
    result = classifier.classify("token", jwt)
    assert result.secret_type == SecretType.OAUTH_TOKEN


def test_certificate_classification():
    """Test certificate classification."""
    classifier = SecretClassifier()

    result = classifier.classify("ssl_certificate")
    assert result.secret_type == SecretType.CERTIFICATE

    # PEM cert content
    cert = "-----BEGIN CERTIFICATE-----\nMIIC..."
    result = classifier.classify("cert", cert)
    assert result.secret_type == SecretType.CERTIFICATE
    assert result.confidence > 0.9


def test_unknown_classification():
    """Test unknown secret classification."""
    classifier = SecretClassifier()

    result = classifier.classify("some_random_secret_name")
    assert result.secret_type == SecretType.UNKNOWN


if __name__ == "__main__":
    print("\n🧪 Running classifier unit tests...\n")

    test_database_password_classification()
    print("✓ Database password classification")

    test_api_key_classification()
    print("✓ API key classification")

    test_ssh_key_classification()
    print("✓ SSH key classification")

    test_connection_string_classification()
    print("✓ Connection string classification")

    test_jwt_token_classification()
    print("✓ JWT token classification")

    test_certificate_classification()
    print("✓ Certificate classification")

    test_unknown_classification()
    print("✓ Unknown classification")

    print("\n✅ All classifier tests passed!\n")
