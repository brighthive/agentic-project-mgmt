"""
Soft unit tests for catalog module.

Testing catalog management and search.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from models import Secret, SecretCategory, Environment
from catalog import SecretsCatalog


def test_catalog_add_and_get():
    """Test adding and retrieving secrets."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(Path(tmp.name))

        secret = Secret(
            id="1",
            name="Test Secret",
            username="user",
            password="pass",
            url="",
            notes="",
            grouping="",
        )

        catalog.add(secret)
        retrieved = catalog.get("1")

        assert retrieved is not None
        assert retrieved.id == "1"
        assert retrieved.name == "Test Secret"
        print("✓ Catalog add/get works")

        Path(tmp.name).unlink()


def test_catalog_search():
    """Test search functionality."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(Path(tmp.name))

        secret1 = Secret(
            id="2",
            name="AWS Production",
            username="admin",
            password="pass",
            url="",
            notes="Important AWS account",
            grouping="",
        )

        secret2 = Secret(
            id="3",
            name="GCP Development",
            username="dev",
            password="pass",
            url="",
            notes="",
            grouping="",
        )

        catalog.add(secret1)
        catalog.add(secret2)

        results = catalog.search("aws")
        assert len(results) == 1
        assert results[0].id == "2"

        results = catalog.search("production")
        assert len(results) == 1

        results = catalog.search("nonexistent")
        assert len(results) == 0

        print("✓ Catalog search works")

        Path(tmp.name).unlink()


def test_catalog_filter_by_category():
    """Test filtering by category."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(Path(tmp.name))

        secret1 = Secret(
            id="4",
            name="AWS Account",
            username="admin",
            password="pass",
            url="",
            notes="",
            grouping="Infrastructure/AWS",
        )

        secret2 = Secret(
            id="5",
            name="Neo4j Database",
            username="neo4j",
            password="pass",
            url="",
            notes="",
            grouping="",
        )

        catalog.add(secret1)
        catalog.add(secret2)

        aws_secrets = catalog.get_by_category(SecretCategory.AWS)
        assert len(aws_secrets) == 1
        assert aws_secrets[0].id == "4"

        db_secrets = catalog.get_by_category(SecretCategory.DATABASE)
        assert len(db_secrets) == 1
        assert db_secrets[0].id == "5"

        print("✓ Catalog category filtering works")

        Path(tmp.name).unlink()


def test_catalog_persistence():
    """Test save and load."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog_path = Path(tmp.name)

        catalog1 = SecretsCatalog(catalog_path)
        secret = Secret(
            id="6",
            name="Persistent Secret",
            username="user",
            password="pass",
            url="",
            notes="",
            grouping="",
        )
        catalog1.add(secret)
        catalog1.save()

        catalog2 = SecretsCatalog(catalog_path)
        retrieved = catalog2.get("6")

        assert retrieved is not None
        assert retrieved.name == "Persistent Secret"
        print("✓ Catalog persistence works")

        catalog_path.unlink()


def test_catalog_stats():
    """Test statistics."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(Path(tmp.name))

        secret1 = Secret(
            id="7",
            name="AWS Prod",
            username="admin",
            password="pass",
            url="",
            notes="",
            grouping="AWS",
        )

        secret2 = Secret(
            id="8",
            name="AWS Dev",
            username="admin",
            password="pass",
            url="",
            notes="",
            grouping="AWS",
        )

        catalog.add(secret1)
        catalog.add(secret2)

        stats = catalog.get_stats()

        assert stats["total"] == 2
        assert "by_category" in stats
        assert "by_environment" in stats
        print("✓ Catalog statistics works")

        Path(tmp.name).unlink()


if __name__ == "__main__":
    print("\n🧪 Running catalog unit tests...\n")

    test_catalog_add_and_get()
    test_catalog_search()
    test_catalog_filter_by_category()
    test_catalog_persistence()
    test_catalog_stats()

    print("\n✅ All catalog tests passed!\n")
