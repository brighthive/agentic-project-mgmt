"""Configuration for LastPass vault."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    root_dir: Path
    data_dir: Path
    backup_dir: Path


def load_config(env: dict | None = None) -> AppConfig:
    """Load config from env or defaults."""
    env = env or os.environ
    base = Path(__file__).parent.parent
    root = Path(env.get("LASTPASS_VAULT_ROOT", str(base)))
    data = Path(env.get("LASTPASS_DATA_DIR", str(root / "data")))
    backup = Path(env.get("LASTPASS_BACKUP_DIR", str(root / "data" / "backup")))
    return AppConfig(root_dir=root, data_dir=data, backup_dir=backup)
