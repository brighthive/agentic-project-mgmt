"""
Soft unit tests for backup loader.
"""

import json
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from backup import load_backup_secrets


def _write_secret(path: Path, name: str, entry_id: str) -> None:
    payload = {
        "id": entry_id,
        "name": name,
        "username": "user",
        "password": "pass",
        "url": "https://example.com",
        "note": "purpose: demo",
        "group": "Test",
    }
    path.write_text(json.dumps(payload))


def test_backup_loader_prefers_merged():
    with tempfile.TemporaryDirectory() as temp_dir:
        base = Path(temp_dir)
        merged = base / "complete_latest" / "merged" / "individual"
        merged.mkdir(parents=True)

        latest = base / "latest" / "individual"
        latest.mkdir(parents=True)

        _write_secret(merged / "a.json", "Merged A", "merged-a")
        _write_secret(latest / "b.json", "Latest B", "latest-b")

        secrets = load_backup_secrets(base)
        names = [s.name for s in secrets]
        assert "Merged A" in names
        assert "Latest B" not in names
        print("✓ Backup loader prefers merged exports")


if __name__ == "__main__":
    print("\n🧪 Running backup unit tests...\n")
    test_backup_loader_prefers_merged()
    print("\n✅ All backup tests passed!\n")
