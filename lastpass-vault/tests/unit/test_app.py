"""
Soft unit tests for application service layer.
"""

import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from app import SecretsApp
from analysis import SecretsAnalyzer
from catalog import SecretsCatalog
from config import AppConfig
from models import Secret


class FakeLastPassClient:
    def __init__(self, secrets: list[Secret]):
        self._secrets = secrets

    def export_all(self) -> list[Secret]:
        return self._secrets


def test_app_consolidate_merges_sources():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        data_dir = root / "data"
        backup_dir = root / "backup"
        backup_dir.mkdir(parents=True)

        config = AppConfig(root_dir=root, data_dir=data_dir, backup_dir=backup_dir)
        catalog = SecretsCatalog(data_dir / "catalog.json")
        analyzer = SecretsAnalyzer()

        backup_secret = Secret(
            id="b1",
            name="Backup Secret",
            username="user",
            password="pass",
            url="https://backup.example.com",
            notes="purpose: backup",
            grouping="Backup",
        )

        lastpass_secret = Secret(
            id="l1",
            name="LastPass Secret",
            username="user",
            password="pass",
            url="https://lastpass.example.com",
            notes="purpose: lastpass",
            grouping="LastPass",
        )

        def backup_loader(_path: Path) -> list[Secret]:
            return [backup_secret]

        def lastpass_factory() -> FakeLastPassClient:
            return FakeLastPassClient([lastpass_secret])

        app = SecretsApp(
            config=config,
            catalog=catalog,
            analyzer=analyzer,
            backup_loader=backup_loader,
            lastpass_client_factory=lastpass_factory,
        )

        result = app.consolidate(skip_backup=False, skip_lastpass=False, materialize=False)
        assert result.total_secrets == 2
        assert catalog.get("b1") is not None
        assert catalog.get("l1") is not None
        print("✓ App consolidates backup + lastpass sources")


if __name__ == "__main__":
    print("\n🧪 Running app unit tests...\n")
    test_app_consolidate_merges_sources()
    print("\n✅ All app tests passed!\n")
