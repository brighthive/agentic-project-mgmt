"""AWS account configuration for BrightHive DynamoDB workspace vault.

Imports account registry from shared lib/accounts.py.
"""

import sys
from pathlib import Path

# Add repo root to path for shared lib import
_repo_root = Path(__file__).parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.accounts import (  # noqa: E402
    AWS_ACCOUNTS,
    AWS_PROFILES,
    AWS_REGION,
    PLATFORM_ACCOUNTS,
    TEST_DEMO_ACCOUNTS,
    get_accounts_for_env,
)

# Core workspace config tables to scan
WORKSPACE_TABLES = [
    "AdminConfig",
    "PlatformAccountsTable",
    "PlatformS3BucketsByAccount",
]

# All known DynamoDB tables
ALL_TABLES = [
    "AdminConfig",
    "PlatformAccountsTable",
    "PlatformS3BucketsByAccount",
    "LangsmithTokenUsage",
    "AgentBasedUsageData",
    "UserCreation",
    "TableIdsByDataAssetUuid",
    "amplify-dynamodb-table",
    "IBMServiceInstances",
]

# Fields containing sensitive values that should be masked
SENSITIVE_FIELDS = {
    "client_secret",
    "client_id",
    "token_endpoint",
    "password",
    "secret",
}
