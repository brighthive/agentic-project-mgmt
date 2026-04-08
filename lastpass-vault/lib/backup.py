"""Load secrets from backup exports."""

import json
from pathlib import Path

from models import Secret


def load_backup_secrets(base_path: Path) -> list[Secret]:
    """Load from complete_latest/merged/individual, fallback to latest/individual."""
    out = []
    merged = base_path / "complete_latest" / "merged" / "individual"
    latest = base_path / "latest" / "individual"

    def load_dir(d: Path):
        if not d.exists():
            return
        for f in d.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                s = Secret(
                    id=data.get("id", ""),
                    name=data.get("name", ""),
                    username=data.get("username", ""),
                    password=data.get("password", ""),
                    url=data.get("url", ""),
                    notes=data.get("notes") or data.get("note", ""),
                    grouping=data.get("grouping") or data.get("group", ""),
                )
                out.append(s)
            except Exception:
                pass

    load_dir(merged)
    load_dir(latest)
    return out
