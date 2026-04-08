"""AWS account configuration for BrightHive secrets vault.

Imports account registry from shared lib/accounts.py.
"""

import os
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

# DynamoDB table for per-workspace secrets
DYNAMODB_WORKSPACE_SECRETS_TABLE = os.getenv(
    "DYNAMODB_WORKSPACE_SECRETS_TABLE", "WorkspaceSecrets"
)
