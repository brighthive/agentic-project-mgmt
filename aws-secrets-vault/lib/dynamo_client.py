"""
DynamoDB client for listing per-workspace secrets across accounts.

Scans a configurable table (e.g. WorkspaceSecrets) in each account and yields
secret metadata (workspace_id + secret key names) for indexing. Does not read
secret values.
"""

import logging
from datetime import datetime
from typing import Iterator, List, Optional, Set

import boto3

from config import (
    AWS_ACCOUNTS,
    AWS_REGION,
    AWS_PROFILES,
    DYNAMODB_WORKSPACE_SECRETS_TABLE,
)
from models import Secret, SecretMetadata, SecretClassification, SecretType

logger = logging.getLogger(__name__)

# Attribute names that are not secret keys (common table metadata)
SKIP_ATTRIBUTES: Set[str] = {
    "workspace_id",
    "pk",
    "sk",
    "id",
    "created_at",
    "updated_at",
    "createdAt",
    "updatedAt",
    "ttl",
    "GSI1PK",
    "GSI1SK",
}


def get_dynamo_client(account_name: str, region: str = AWS_REGION):
    """Return a boto3 DynamoDB client for the given account."""
    account_id = AWS_ACCOUNTS.get(account_name)
    if not account_id:
        raise ValueError(f"Unknown account: {account_name}")
    profile = AWS_PROFILES.get(account_name)
    session = boto3.Session(profile_name=profile, region_name=region)
    return session.client("dynamodb"), account_id


def _extract_workspace_id(item: dict) -> Optional[str]:
    """Get workspace identifier from item (PK or workspace_id attribute)."""
    if "workspace_id" in item and "S" in item["workspace_id"]:
        return item["workspace_id"]["S"]
    if "pk" in item and "S" in item["pk"]:
        val = item["pk"]["S"]
        if val.startswith("WORKSPACE#") or val.startswith("ws#"):
            return val.split("#", 1)[-1]
        return val
    if "workspaceId" in item and "S" in item["workspaceId"]:
        return item["workspaceId"]["S"]
    return None


def _secret_key_attributes(item: dict) -> List[str]:
    """Return attribute names that likely represent secret keys (exclude metadata)."""
    keys = []
    for k in item.keys():
        if k in SKIP_ATTRIBUTES:
            continue
        # Skip keys that look like indexes
        if k.startswith("GSI") or k.endswith("PK") or k.endswith("SK"):
            continue
        keys.append(k)
    return keys


def scan_workspace_secrets(
    account_name: str,
    table_name: Optional[str] = None,
    region: str = AWS_REGION,
) -> List[Secret]:
    """
    Scan DynamoDB table for per-workspace secret entries in one account.

    Returns one Secret record per (workspace_id, secret_key) with source=dynamodb.
    Does not fetch secret values.
    """
    table_name = table_name or DYNAMODB_WORKSPACE_SECRETS_TABLE
    client, account_id = get_dynamo_client(account_name, region)
    secrets: List[Secret] = []

    try:
        paginator = client.get_paginator("scan")
        for page in paginator.paginate(TableName=table_name):
            for item in page.get("Items", []):
                workspace_id = _extract_workspace_id(item)
                if not workspace_id:
                    continue
                for key in _secret_key_attributes(item):
                    name = f"workspace:{workspace_id}:{key}"
                    metadata = SecretMetadata(
                        arn=f"dynamodb:{account_id}:{table_name}:{workspace_id}:{key}",
                        name=name,
                        description=f"DynamoDB workspace secret ({table_name})",
                        created_at=datetime.now(),
                        last_updated=datetime.now(),
                        last_accessed=None,
                        rotation_enabled=False,
                        rotation_rules=None,
                    )
                    classification = SecretClassification(
                        secret_type=SecretType.UNKNOWN,
                        confidence=0.5,
                        patterns_matched=[],
                        evidence={"source": "dynamodb", "workspace_id": workspace_id, "key": key},
                    )
                    secret = Secret(
                        name=name,
                        account_id=account_id,
                        account_name=account_name,
                        metadata=metadata,
                        classification=classification,
                        source="dynamodb",
                    )
                    secrets.append(secret)
    except client.exceptions.ResourceNotFoundException:
        logger.warning(f"[DynamoDB] Table {table_name} not found in {account_name}")
        return []
    except Exception as e:
        logger.warning(f"[DynamoDB] Failed to scan {table_name} in {account_name}: {e}")
        return secrets

    logger.info(f"[DynamoDB] Found {len(secrets)} workspace secret refs in {account_name}")
    return secrets


def fetch_all_workspace_secrets(
    accounts: Optional[List[str]] = None,
    table_name: Optional[str] = None,
) -> List[Secret]:
    """
    Fetch per-workspace secret metadata from DynamoDB in all (or given) accounts.
    """
    accounts = accounts or list(AWS_ACCOUNTS.keys())
    all_secrets: List[Secret] = []
    for account in accounts:
        all_secrets.extend(
            scan_workspace_secrets(account, table_name=table_name)
        )
    return all_secrets
