"""
Soft unit tests for indexer module.
"""

import json
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from indexer import build_index, write_index, write_aliases, materialize_metadata
from models import Secret


def _make_secret(secret_id: str, name: str) -> Secret:
    return Secret(
        id=secret_id,
        name=name,
        username="user",
        password="pass",
        url="https://example.com",
        notes="purpose: demo",
        grouping="Group",
    )


def test_indexer_outputs_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)
        secrets = [_make_secret("1", "Alpha"), _make_secret("2", "Beta")]

        index = build_index(secrets)
        json_path, md_path = write_index(index, data_dir)
        alias_path = write_aliases(secrets, data_dir / "organized")
        metadata_dir = materialize_metadata(secrets, data_dir / "organized")

        assert json_path.exists()
        assert md_path.exists()
        assert alias_path.exists()
        assert metadata_dir.exists()

        alias_data = json.loads(alias_path.read_text())
        assert "by_id" in alias_data
        assert "by_name" in alias_data
        print("✓ Indexer output files created")


if __name__ == "__main__":
    print("\n🧪 Running indexer unit tests...\n")
    test_indexer_outputs_files()
    print("\n✅ All indexer tests passed!\n")
