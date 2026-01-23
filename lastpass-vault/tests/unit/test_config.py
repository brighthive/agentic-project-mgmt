"""
Soft unit tests for config module.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from config import load_config


def test_config_env_overrides():
    env = {
        "LASTPASS_VAULT_ROOT": "/tmp/vault-root",
        "LASTPASS_DATA_DIR": "/tmp/vault-data",
        "LASTPASS_BACKUP_DIR": "/tmp/vault-backup",
    }

    config = load_config(env)
    assert config.root_dir == Path("/tmp/vault-root")
    assert config.data_dir == Path("/tmp/vault-data")
    assert config.backup_dir == Path("/tmp/vault-backup")
    print("✓ Config env overrides work")


if __name__ == "__main__":
    print("\n🧪 Running config unit tests...\n")
    test_config_env_overrides()
    print("\n✅ All config tests passed!\n")
