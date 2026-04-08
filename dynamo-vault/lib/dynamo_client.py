"""DynamoDB client for scanning workspace configuration tables."""

import logging
from typing import Optional

import boto3

from config import AWS_ACCOUNTS, AWS_REGION, AWS_PROFILES, WORKSPACE_TABLES
from models import WorkspaceConfig, EntityType

logger = logging.getLogger(__name__)


def get_session(account_name: str) -> boto3.Session:
    """Create boto3 session for the given account."""
    profile = AWS_PROFILES.get(account_name)
    if not profile:
        raise ValueError(f"Unknown account: {account_name}")
    return boto3.Session(profile_name=profile, region_name=AWS_REGION)


def list_tables(account_name: str) -> list[str]:
    """List all DynamoDB tables in an account."""
    session = get_session(account_name=account_name)
    client = session.client("dynamodb")
    tables = []
    kwargs = {}
    while True:
        resp = client.list_tables(**kwargs)
        tables.extend(resp.get("TableNames", []))
        if "LastEvaluatedTableName" in resp:
            kwargs["ExclusiveStartTableName"] = resp["LastEvaluatedTableName"]
        else:
            break
    return sorted(tables)


def scan_table(account_name: str, table_name: str) -> list[dict]:
    """Full scan of a DynamoDB table with auto-deserialization via resource API."""
    session = get_session(account_name=account_name)
    table = session.resource("dynamodb").Table(table_name)
    items = []
    kwargs = {}
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" in resp:
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        else:
            break
    logger.info(f"Scanned {len(items)} items from {account_name}:{table_name}")
    return items


def _extract_uuid(item: dict) -> Optional[str]:
    """Extract UUID primary key from an item."""
    for key in ("UUID", "uuid", "Id", "id"):
        if key in item:
            return str(item[key])
    return None


def _extract_entity_type(item: dict) -> EntityType:
    """Determine if item is Workspace or Organization."""
    for key in ("type", "Type", "entityType", "EntityType"):
        if key in item:
            val = str(item[key])
            if "org" in val.lower():
                return EntityType.ORGANIZATION
            if "work" in val.lower():
                return EntityType.WORKSPACE
    return EntityType.UNKNOWN


def _safe_dict(val) -> dict:
    """Convert a value to dict, handling DynamoDB set types."""
    if isinstance(val, dict):
        return val
    if isinstance(val, set):
        return {v: True for v in val}
    return {}


def _safe_list(val) -> list:
    """Convert a value to list."""
    if isinstance(val, list):
        return val
    if isinstance(val, set):
        return list(val)
    return []


def build_workspace_index(
    account_name: str,
    tables: Optional[list[str]] = None,
) -> list[WorkspaceConfig]:
    """Scan workspace tables and merge into WorkspaceConfig objects by UUID."""
    tables = tables or WORKSPACE_TABLES
    account_id = AWS_ACCOUNTS[account_name]

    admin_items = {}
    platform_items = {}
    s3_items = {}

    for table_name in tables:
        try:
            items = scan_table(account_name=account_name, table_name=table_name)
        except Exception as e:
            logger.warning(f"Failed to scan {table_name} in {account_name}: {e}")
            continue

        for item in items:
            uuid = _extract_uuid(item)
            if not uuid:
                continue

            if table_name == "AdminConfig":
                admin_items[uuid] = item
            elif table_name == "PlatformAccountsTable":
                platform_items[uuid] = item
            elif table_name == "PlatformS3BucketsByAccount":
                s3_items[uuid] = item

    all_uuids = set(admin_items.keys()) | set(platform_items.keys()) | set(s3_items.keys())
    workspaces = []

    for uuid in sorted(all_uuids):
        admin = admin_items.get(uuid, {})
        platform = platform_items.get(uuid, {})
        s3 = s3_items.get(uuid, {})

        # AdminConfig stores config in nested 'AdminConfig' map
        admin_nested = admin.get("AdminConfig", {}) if isinstance(admin.get("AdminConfig"), dict) else {}

        # Name: PlatformAccountsTable.EntityName > AdminConfig.AdminConfig.name > UUID prefix
        name = (
            platform.get("EntityName")
            or platform.get("AWSAccountName")
            or admin_nested.get("name")
            or uuid[:12]
        )

        # Entity type from PlatformAccountsTable.type or S3.entityType
        entity_type = _extract_entity_type(platform) or _extract_entity_type(s3)

        # Owner from nested AdminConfig map
        owner = admin_nested.get("owner")

        # IAM roles from platform item — collect all *Arn* dict/string fields with role in name
        iam_roles = {}
        for k, v in platform.items():
            if isinstance(v, dict) and "arn" in k.lower():
                iam_roles[k] = v
            elif isinstance(v, str) and "role" in k.lower() and "arn" in v.lower():
                iam_roles[k] = v

        # S3 buckets from S3 table
        s3_buckets = _safe_dict(s3.get("s3BucketArns"))

        # Neo4j envs — stored as a DynamoDB string set
        neo4j_envs = _safe_dict(platform.get("Neo4Jenvs") or platform.get("Neo4jEnvs"))

        ws = WorkspaceConfig(
            uuid=uuid,
            name=str(name),
            account_name=account_name,
            account_id=account_id,
            entity_type=entity_type,
            owner=str(owner) if owner else None,
            environment=admin.get("Environment") or platform.get("Environment"),
            cdk_stack_arn=admin.get("WorkspaceCDKCodeBuildARN") or admin.get("OrganizationCDKCodeBuildARN"),
            groups=_safe_list(admin_nested.get("groups")),
            aws_account_number=platform.get("AWSAccountNumber"),
            env_secret_arn=platform.get("EnvSecretArn"),
            account_secret_arn=platform.get("accountSecretARN"),
            api_urls=_safe_dict(platform.get("ApiUrls")),
            iam_roles=iam_roles,
            neo4j_envs=neo4j_envs,
            s3_buckets=s3_buckets,
            s3_role_arn=s3.get("s3RoleArn"),
            admin_raw=admin,
            platform_raw=platform,
            s3_raw=s3,
        )
        workspaces.append(ws)

    logger.info(f"Built {len(workspaces)} workspace configs from {account_name}")
    return workspaces


def search_workspaces(
    account_name: str,
    query: str,
) -> list[WorkspaceConfig]:
    """Search workspaces by name substring (case-insensitive)."""
    all_ws = build_workspace_index(account_name=account_name)
    q = query.lower()
    return [ws for ws in all_ws if q in ws.name.lower()]


def get_workspace_by_name(
    account_name: str,
    workspace_name: str,
) -> Optional[WorkspaceConfig]:
    """Fetch a single workspace by exact or partial name match."""
    all_ws = build_workspace_index(account_name=account_name)
    # Exact match first
    for ws in all_ws:
        if ws.name.lower() == workspace_name.lower():
            return ws
    # Substring fallback
    matches = [ws for ws in all_ws if workspace_name.lower() in ws.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        logger.warning(f"Multiple matches for '{workspace_name}': {[w.name for w in matches]}")
        return matches[0]
    return None
