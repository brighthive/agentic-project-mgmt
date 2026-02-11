"""Unit tests for catalog module."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from catalog import SecretsCatalog
from models import AWSSecret, Environment, SecretCategory, SecretSource


def _make_secret(
    secret_id: str,
    name: str,
    env: Environment = Environment.PROD,
    account_number: str | None = None,
    account_type: str | None = None,
) -> AWSSecret:
    return AWSSecret(
        id=secret_id,
        name=name,
        environment=env,
        source=SecretSource.SECRETS_MANAGER,
        account_number=account_number,
        account_type=account_type,
    )


def test_catalog_add_and_get():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(catalog_path=Path(tmp.name))
        secret = _make_secret(secret_id="arn:1", name="test-secret")

        catalog.add(secret=secret)
        retrieved = catalog.get(secret_id="arn:1")

        assert retrieved is not None
        assert retrieved.name == "test-secret"

        Path(tmp.name).unlink()


def test_catalog_search():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(catalog_path=Path(tmp.name))

        catalog.add(secret=_make_secret(secret_id="arn:1", name="prod-neo4j-connection"))
        catalog.add(secret=_make_secret(secret_id="arn:2", name="prod-rds-credentials"))

        results = catalog.search(query="neo4j")
        assert len(results) == 1
        assert results[0].id == "arn:1"

        results = catalog.search(query="prod")
        assert len(results) == 2

        results = catalog.search(query="nonexistent")
        assert len(results) == 0

        Path(tmp.name).unlink()


def test_catalog_filter_by_category():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(catalog_path=Path(tmp.name))

        catalog.add(secret=_make_secret(secret_id="arn:1", name="cdk-admin-secret/123"))
        catalog.add(secret=_make_secret(secret_id="arn:2", name="prod-neo4j-connection"))

        aws_creds = catalog.get_by_category(category=SecretCategory.AWS_CREDENTIAL)
        assert len(aws_creds) == 1
        assert aws_creds[0].id == "arn:1"

        db_secrets = catalog.get_by_category(category=SecretCategory.DATABASE)
        assert len(db_secrets) == 1
        assert db_secrets[0].id == "arn:2"

        Path(tmp.name).unlink()


def test_catalog_filter_by_environment():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(catalog_path=Path(tmp.name))

        catalog.add(secret=_make_secret(secret_id="arn:1", name="prod-secret", env=Environment.PROD))
        catalog.add(secret=_make_secret(secret_id="arn:2", name="dev-secret", env=Environment.DEV))

        prod = catalog.get_by_environment(environment=Environment.PROD)
        assert len(prod) == 1

        dev = catalog.get_by_environment(environment=Environment.DEV)
        assert len(dev) == 1

        Path(tmp.name).unlink()


def test_catalog_filter_by_account_type():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(catalog_path=Path(tmp.name))

        catalog.add(secret=_make_secret(
            secret_id="arn:1",
            name="cdk-admin-secret/111",
            account_number="111",
            account_type="Organization",
        ))
        catalog.add(secret=_make_secret(
            secret_id="arn:2",
            name="cdk-admin-secret/222",
            account_number="222",
            account_type="Workspace",
        ))

        orgs = catalog.get_by_account_type(account_type="Organization")
        assert len(orgs) == 1
        assert orgs[0].account_number == "111"

        Path(tmp.name).unlink()


def test_catalog_persistence():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog_path = Path(tmp.name)

        catalog1 = SecretsCatalog(catalog_path=catalog_path)
        catalog1.add(secret=_make_secret(secret_id="arn:1", name="persistent-secret"))
        catalog1.save()

        catalog2 = SecretsCatalog(catalog_path=catalog_path)
        retrieved = catalog2.get(secret_id="arn:1")

        assert retrieved is not None
        assert retrieved.name == "persistent-secret"

        catalog_path.unlink()


def test_catalog_stats():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        catalog = SecretsCatalog(catalog_path=Path(tmp.name))

        catalog.add(secret=_make_secret(secret_id="arn:1", name="cdk-admin-secret/111"))
        catalog.add(secret=_make_secret(secret_id="arn:2", name="prod-neo4j-connection"))

        stats = catalog.get_stats()

        assert stats["total"] == 2
        assert "by_category" in stats
        assert "by_environment" in stats
        assert "by_source" in stats

        Path(tmp.name).unlink()
