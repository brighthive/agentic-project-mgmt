"""
Data models for AWS Secrets Manager inventory and classification.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class SecretType(str, Enum):
    """Classification types for secrets."""

    DATABASE_PASSWORD = "database_password"
    API_KEY = "api_key"
    SSH_KEY = "ssh_key"
    CONNECTION_STRING = "connection_string"
    OAUTH_TOKEN = "oauth_token"
    WEBHOOK_SECRET = "webhook_secret"
    ENCRYPTION_KEY = "encryption_key"
    CERTIFICATE = "certificate"
    CREDENTIALS_JSON = "credentials_json"
    UNKNOWN = "unknown"


@dataclass
class SecretMetadata:
    """Metadata about a secret from AWS."""

    arn: str
    name: str
    description: Optional[str]
    created_at: datetime
    last_updated: datetime
    last_accessed: Optional[datetime]
    rotation_enabled: bool
    rotation_rules: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "arn": self.arn,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "rotation_enabled": self.rotation_enabled,
            "rotation_rules": self.rotation_rules,
        }


@dataclass
class SecretClassification:
    """Classification result for a secret."""

    secret_type: SecretType
    confidence: float  # 0.0 to 1.0
    patterns_matched: list[str]
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.secret_type.value,
            "confidence": self.confidence,
            "patterns_matched": self.patterns_matched,
            "evidence": self.evidence,
        }


@dataclass
class Secret:
    """Complete secret record with metadata and classification."""

    name: str
    account_id: str
    account_name: str
    metadata: SecretMetadata
    classification: Optional[SecretClassification] = None
    source: str = "secrets_manager"  # "secrets_manager" | "dynamodb"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "metadata": self.metadata.to_dict(),
            "classification": self.classification.to_dict() if self.classification else None,
            "source": self.source,
        }


@dataclass
class SecretsIndex:
    """Complete index of all secrets and summary."""

    secrets: list[Secret]
    summary: Dict[str, Any]
    generated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "secrets": [s.to_dict() for s in self.secrets],
            "summary": self.summary,
            "generated_at": self.generated_at.isoformat(),
        }
