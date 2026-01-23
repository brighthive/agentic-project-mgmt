"""
Soft unit tests for models module.

Testing core data models work correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from models import Secret, SecretCategory, Environment, SecretStatus, SecretSource


def test_secret_creation():
    """Test basic secret creation."""
    secret = Secret(
        id="123",
        name="Test Secret",
        username="testuser",
        password="testpass",
        url="https://example.com",
        notes="Test notes",
        grouping="Test/Group",
    )

    assert secret.id == "123"
    assert secret.name == "Test Secret"
    assert secret.username == "testuser"
    print("✓ Secret creation works")


def test_auto_categorization_aws():
    """Test AWS auto-categorization."""
    secret = Secret(
        id="1",
        name="AWS Production Account",
        username="admin",
        password="pass",
        url="https://aws.amazon.com",
        notes="",
        grouping="Infrastructure/AWS",
    )

    assert secret.category == SecretCategory.AWS
    print("✓ AWS auto-categorization works")


def test_auto_categorization_database():
    """Test database auto-categorization."""
    secret = Secret(
        id="2",
        name="Neo4j Production Database",
        username="neo4j",
        password="pass",
        url="bolt://localhost:7687",
        notes="",
        grouping="Databases",
    )

    assert secret.category == SecretCategory.DATABASE
    print("✓ Database auto-categorization works")


def test_environment_detection_prod():
    """Test production environment detection."""
    secret = Secret(
        id="3",
        name="BrightHive Prod Neo4j",
        username="neo4j",
        password="pass",
        url="",
        notes="",
        grouping="",
    )

    assert secret.environment == Environment.PROD
    print("✓ Production environment detection works")


def test_environment_detection_dev():
    """Test dev environment detection."""
    secret = Secret(
        id="4",
        name="Dev Database",
        username="user",
        password="pass",
        url="",
        notes="",
        grouping="",
    )

    assert secret.environment == Environment.DEV
    print("✓ Dev environment detection works")


def test_secret_to_dict():
    """Test serialization to dict."""
    secret = Secret(
        id="5",
        name="Test",
        username="user",
        password="pass",
        url="",
        notes="",
        grouping="",
    )

    data = secret.to_dict()
    assert isinstance(data, dict)
    assert data["id"] == "5"
    assert data["name"] == "Test"
    assert data["source"] == SecretSource.LASTPASS.value
    print("✓ Secret serialization works")


def test_secret_from_dict():
    """Test deserialization from dict."""
    from datetime import datetime

    data = {
        "id": "6",
        "name": "Test Secret",
        "username": "user",
        "password": "pass",
        "url": "https://example.com",
        "notes": "purpose: demo access",
        "grouping": "group",
        "category": "aws",
        "environment": "prod",
        "status": "active",
        "source": "backup_cli",
        "purpose": "demo access",
        "normalized_name": "group_test_secret",
        "instance": "example.com",
        "added_date": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "last_accessed": None,
        "is_duplicate": False,
        "duplicate_of": None,
        "confidence_score": 1.0,
    }

    secret = Secret.from_dict(data)
    assert secret.id == "6"
    assert secret.category == SecretCategory.AWS
    assert secret.environment == Environment.PROD
    assert secret.source == SecretSource.BACKUP_CLI
    print("✓ Secret deserialization works")


def test_purpose_and_instance_detection():
    """Test purpose and instance extraction."""
    secret = Secret(
        id="7",
        name="Prod Neo4j",
        username="neo4j",
        password="pass",
        url="bolt://db.example.com:7687",
        notes="purpose: data ingestion",
        grouping="Databases",
    )

    assert secret.purpose == "data ingestion"
    assert secret.instance == "db.example.com"
    assert "prod_neo4j" in secret.normalized_name
    print("✓ Purpose and instance detection works")


if __name__ == "__main__":
    print("\n🧪 Running models unit tests...\n")

    test_secret_creation()
    test_auto_categorization_aws()
    test_auto_categorization_database()
    test_environment_detection_prod()
    test_environment_detection_dev()
    test_secret_to_dict()
    test_secret_from_dict()
    test_purpose_and_instance_detection()

    print("\n✅ All models tests passed!\n")
