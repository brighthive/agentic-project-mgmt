"""Secrets catalog — persistent storage and search."""

import json
from pathlib import Path
from typing import Optional

from models import Secret, SecretCategory


class SecretsCatalog:
    def __init__(self, path: Path):
        self._path = path
        self.secrets: dict[str, Secret] = {}
        if path.exists():
            data = json.loads(path.read_text())
            for item in data.get("secrets", []):
                s = Secret.from_dict(item)
                self.secrets[s.id] = s

    def add(self, secret: Secret):
        self.secrets[secret.id] = secret

    def get(self, id: str) -> Optional[Secret]:
        return self.secrets.get(id)

    def search(self, query: str) -> list[Secret]:
        q = query.lower()
        out = []
        for s in self.secrets.values():
            if q in (s.name or "").lower() or q in (s.notes or "").lower() or q in (s.grouping or "").lower():
                out.append(s)
        return out

    def get_by_category(self, category: SecretCategory) -> list[Secret]:
        return [s for s in self.secrets.values() if s.category == category]

    def save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"secrets": [s.to_dict() for s in self.secrets.values()]}
        self._path.write_text(json.dumps(data, indent=2, default=str))

    def get_stats(self) -> dict:
        by_cat = {}
        by_env = {}
        for s in self.secrets.values():
            c = s.category.value
            by_cat[c] = by_cat.get(c, 0) + 1
            e = s.environment.value
            by_env[e] = by_env.get(e, 0) + 1
        return {
            "total": len(self.secrets),
            "duplicates": 0,
            "deprecated": sum(1 for s in self.secrets.values() if s.status.value == "deprecated"),
            "by_category": by_cat,
            "by_environment": by_env,
        }
