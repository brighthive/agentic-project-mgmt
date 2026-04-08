"""Data models for DynamoDB workspace configuration."""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from enum import Enum


class EntityType(str, Enum):
    """Type of platform entity."""
    WORKSPACE = "Workspace"
    ORGANIZATION = "Organization"
    UNKNOWN = "Unknown"


@dataclass
class WorkspaceConfig:
    """Merged workspace configuration from AdminConfig + PlatformAccountsTable + S3."""

    uuid: str
    name: str
    account_name: str
    account_id: str
    entity_type: EntityType = EntityType.UNKNOWN
    owner: Optional[str] = None
    environment: Optional[str] = None

    # From AdminConfig
    cdk_stack_arn: Optional[str] = None
    groups: Optional[list[str]] = None
    admin_raw: dict = field(default_factory=dict)

    # From PlatformAccountsTable
    aws_account_number: Optional[str] = None
    env_secret_arn: Optional[str] = None
    account_secret_arn: Optional[str] = None
    api_urls: dict = field(default_factory=dict)
    iam_roles: dict = field(default_factory=dict)
    neo4j_envs: dict = field(default_factory=dict)
    platform_raw: dict = field(default_factory=dict)

    # From PlatformS3BucketsByAccount
    s3_buckets: dict = field(default_factory=dict)
    s3_role_arn: Optional[str] = None
    s3_raw: dict = field(default_factory=dict)

    def to_dict(self, show_secrets: bool = False) -> dict[str, Any]:
        """Serialize to dict, masking secrets by default."""
        from config import SENSITIVE_FIELDS

        result = {
            "uuid": self.uuid,
            "name": self.name,
            "account_name": self.account_name,
            "account_id": self.account_id,
            "entity_type": self.entity_type.value,
            "owner": self.owner,
            "environment": self.environment,
            "aws_account_number": self.aws_account_number,
            "env_secret_arn": self.env_secret_arn,
            "account_secret_arn": self.account_secret_arn,
            "api_urls": _mask_dict(self.api_urls, SENSITIVE_FIELDS) if not show_secrets else self.api_urls,
            "iam_roles": self.iam_roles,
            "neo4j_envs": _mask_dict(self.neo4j_envs, SENSITIVE_FIELDS) if not show_secrets else self.neo4j_envs,
            "s3_buckets": self.s3_buckets,
            "s3_role_arn": self.s3_role_arn,
            "cdk_stack_arn": self.cdk_stack_arn,
            "groups": self.groups,
        }
        return result


@dataclass
class ConfigIndex:
    """Index of all workspace configurations with summary stats."""

    workspaces: list[WorkspaceConfig]
    generated_at: str
    account_name: str

    @property
    def summary(self) -> dict[str, Any]:
        """Compute summary stats."""
        by_type = {}
        for ws in self.workspaces:
            t = ws.entity_type.value
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total_workspaces": len(self.workspaces),
            "by_entity_type": by_type,
            "account": self.account_name,
        }

    def to_dict(self, show_secrets: bool = False) -> dict[str, Any]:
        """Serialize full index."""
        return {
            "workspaces": [ws.to_dict(show_secrets=show_secrets) for ws in self.workspaces],
            "summary": self.summary,
            "generated_at": self.generated_at,
        }


def _mask_dict(d: dict, sensitive_keys: set[str]) -> dict:
    """Recursively mask sensitive values in a dict."""
    masked = {}
    for k, v in d.items():
        if isinstance(v, dict):
            masked[k] = _mask_dict(v, sensitive_keys)
        elif k.lower() in {s.lower() for s in sensitive_keys}:
            masked[k] = "***MASKED***"
        else:
            masked[k] = v
    return masked
