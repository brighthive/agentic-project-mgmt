"""
Soft unit tests for analysis module.

Testing duplicate detection and health scoring.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from models import Secret, SecretStatus
from analysis import SecretsAnalyzer


def test_duplicate_detection_exact_credentials():
    """Test duplicate detection with exact credentials."""
    analyzer = SecretsAnalyzer()

    secret1 = Secret(
        id="1",
        name="AWS Prod",
        username="admin",
        password="same_password",
        url="",
        notes="",
        grouping="AWS",
    )

    secret2 = Secret(
        id="2",
        name="AWS Prod Copy",
        username="admin",
        password="same_password",
        url="",
        notes="",
        grouping="AWS",
    )

    duplicates = analyzer.find_duplicates([secret1, secret2])

    assert len(duplicates) == 1
    assert duplicates[0].confidence == 1.0
    assert "Identical credentials" in duplicates[0].reason
    print("✓ Exact credentials duplicate detection works")


def test_duplicate_detection_similar_names():
    """Test duplicate detection with similar names."""
    analyzer = SecretsAnalyzer()

    secret1 = Secret(
        id="3",
        name="BrightHive Production Database",
        username="user1",
        password="pass1",
        url="",
        notes="",
        grouping="Databases",
    )

    secret2 = Secret(
        id="4",
        name="BrightHive Production DB",
        username="user2",
        password="pass2",
        url="",
        notes="",
        grouping="Databases",
    )

    duplicates = analyzer.find_duplicates([secret1, secret2])

    assert len(duplicates) == 1
    assert duplicates[0].confidence > 0.85
    print("✓ Similar names duplicate detection works")


def test_no_duplicates():
    """Test no false positives."""
    analyzer = SecretsAnalyzer()

    secret1 = Secret(
        id="5",
        name="AWS Account",
        username="admin",
        password="pass1",
        url="",
        notes="",
        grouping="AWS",
    )

    secret2 = Secret(
        id="6",
        name="GCP Account",
        username="user",
        password="pass2",
        url="",
        notes="",
        grouping="GCP",
    )

    duplicates = analyzer.find_duplicates([secret1, secret2])

    assert len(duplicates) == 0
    print("✓ No false positive duplicates")


def test_deprecation_suggestion():
    """Test deprecation suggestion logic."""
    analyzer = SecretsAnalyzer()

    old_secret = Secret(
        id="7",
        name="Old AWS Account (deprecated)",
        username="admin",
        password="password",
        url="",
        notes="",
        grouping="",
    )

    should_deprecate, reason = analyzer.suggest_deprecation(old_secret)

    assert should_deprecate is True
    assert len(reason) > 0
    print("✓ Deprecation suggestion works")


def test_health_score():
    """Test health score calculation."""
    analyzer = SecretsAnalyzer()

    secrets = [
        Secret(
            id="8",
            name="Good Secret",
            username="user",
            password="secure_pass",
            url="",
            notes="",
            grouping="",
        ),
        Secret(
            id="9",
            name="Another Good Secret",
            username="user2",
            password="another_pass",
            url="",
            notes="",
            grouping="",
        ),
    ]

    health = analyzer.get_health_score(secrets)

    assert "overall_score" in health
    assert health["overall_score"] >= 0
    assert health["overall_score"] <= 100
    assert health["total_secrets"] == 2
    print("✓ Health score calculation works")


if __name__ == "__main__":
    print("\n🧪 Running analysis unit tests...\n")

    test_duplicate_detection_exact_credentials()
    test_duplicate_detection_similar_names()
    test_no_duplicates()
    test_deprecation_suggestion()
    test_health_score()

    print("\n✅ All analysis tests passed!\n")
