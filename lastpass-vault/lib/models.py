"""Secret models and enums."""

import re
from datetime import datetime
from enum import Enum
from typing import Optional


class SecretCategory(Enum):
    AWS = "aws"
    DATABASE = "database"
    API = "api"
    GCP = "gcp"
    OTHER = "other"


class Environment(Enum):
    PROD = "prod"
    STAGE = "stage"
    DEV = "dev"
    UNKNOWN = "unknown"


class SecretStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class SecretSource(Enum):
    LASTPASS = "lastpass"
    BACKUP_CLI = "backup_cli"
    UNKNOWN = "unknown"


def _detect_category(name: str, url: str, grouping: str) -> SecretCategory:
    """Infer category from name, url, grouping."""
    combined = f"{name} {url} {grouping}".lower()
    if "aws" in combined or "amazon" in combined:
        return SecretCategory.AWS
    if "neo4j" in combined or "postgres" in combined or "mysql" in combined or "database" in combined:
        return SecretCategory.DATABASE
    if "gcp" in combined or "google" in combined:
        return SecretCategory.GCP
    if "api" in combined:
        return SecretCategory.API
    return SecretCategory.OTHER


def _detect_environment(name: str, notes: str) -> Environment:
    """Infer environment from name and notes."""
    combined = f"{name} {notes}".lower()
    if "prod" in combined or "production" in combined:
        return Environment.PROD
    if "stage" in combined or "staging" in combined:
        return Environment.STAGE
    if "dev" in combined or "development" in combined:
        return Environment.DEV
    return Environment.UNKNOWN


def _extract_purpose(notes: str) -> Optional[str]:
    """Extract purpose from notes (purpose: ...)."""
    if not notes:
        return None
    for line in notes.splitlines():
        if "purpose:" in line.lower():
            return line.split(":", 1)[1].strip()
    return None


def _extract_instance(url: str) -> Optional[str]:
    """Extract host from URL."""
    if not url:
        return None
    match = re.search(r"://([^/:]+)", url)
    return match.group(1) if match else None


def _normalize_name(grouping: str, name: str) -> str:
    """Build normalized name for search."""
    parts = []
    if grouping:
        parts.append(re.sub(r"[^a-z0-9]+", "_", grouping.lower()).strip("_"))
    if name:
        parts.append(re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_"))
    return "_".join(p for p in parts if p)


class Secret:
    """A secret entry with metadata."""

    def __init__(
        self,
        id: str,
        name: str,
        username: str = "",
        password: str = "",
        url: str = "",
        notes: str = "",
        grouping: str = "",
        category: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        purpose: Optional[str] = None,
        normalized_name: Optional[str] = None,
        instance: Optional[str] = None,
        **kwargs,
    ):
        self.id = id
        self.name = name
        self.username = username or ""
        self.password = password or ""
        self.url = url or ""
        self.notes = notes or ""
        self.grouping = grouping or ""
        self._category = category
        self._environment = environment
        self._status = status
        self._source = source
        self._purpose = purpose
        self._normalized_name = normalized_name
        self._instance = instance

    @property
    def category(self) -> SecretCategory:
        if self._category:
            try:
                return SecretCategory(self._category.lower())
            except ValueError:
                pass
        return _detect_category(self.name, self.url, self.grouping)

    @property
    def environment(self) -> Environment:
        if self._environment:
            try:
                return Environment(self._environment.lower())
            except ValueError:
                pass
        return _detect_environment(self.name, self.notes)

    @property
    def status(self) -> SecretStatus:
        if self._status:
            try:
                return SecretStatus(self._status.lower())
            except ValueError:
                pass
        return SecretStatus.ACTIVE

    @property
    def source(self) -> SecretSource:
        if self._source:
            try:
                return SecretSource(self._source.lower())
            except ValueError:
                pass
        return SecretSource.LASTPASS

    @property
    def purpose(self) -> Optional[str]:
        return self._purpose or _extract_purpose(self.notes)

    @property
    def instance(self) -> Optional[str]:
        return self._instance or _extract_instance(self.url)

    @property
    def normalized_name(self) -> str:
        return self._normalized_name or _normalize_name(self.grouping, self.name)

    def to_dict(self) -> dict:
        now = datetime.utcnow().isoformat() + "Z"
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "password": self.password,
            "url": self.url,
            "notes": self.notes,
            "grouping": self.grouping,
            "category": self.category.value,
            "environment": self.environment.value,
            "status": self.status.value,
            "source": self.source.value,
            "purpose": self.purpose,
            "instance": self.instance,
            "normalized_name": self.normalized_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Secret":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            url=data.get("url", ""),
            notes=data.get("notes", ""),
            grouping=data.get("grouping", ""),
            category=data.get("category"),
            environment=data.get("environment"),
            status=data.get("status"),
            source=data.get("source"),
            purpose=data.get("purpose"),
            normalized_name=data.get("normalized_name"),
            instance=data.get("instance"),
        )
