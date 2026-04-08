"""BrightHive AWS account registry — single source of truth.

All vault CLIs (dynamo-vault, aws-secrets-vault, lastpass-vault) import from here.
All accounts use AWS SSO. See /aws-auth skill for SSO details.
"""

import os
from dataclasses import dataclass
from enum import Enum


class AccountType(Enum):
    PLATFORM = "platform"
    TEST = "test"
    DEMO = "demo"
    OTHER = "other"


class EntityType(Enum):
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    INFRASTRUCTURE = "infrastructure"


@dataclass(frozen=True)
class AWSAccount:
    """Single AWS account definition."""

    account_id: str
    profile: str
    name: str
    account_type: AccountType
    entity_type: EntityType = EntityType.INFRASTRUCTURE
    parent_env: str = ""
    sso_role: str = "AdministratorAccess"


# ── Platform Accounts ────────────────────────────────────────────
MAIN = AWSAccount(
    account_id="396527728813",
    profile="brighthive-main",
    name="MAIN",
    account_type=AccountType.PLATFORM,
)
DEV = AWSAccount(
    account_id="531731217746",
    profile="brighthive-development",
    name="DEV",
    account_type=AccountType.PLATFORM,
)
STAGE = AWSAccount(
    account_id="873769991712",
    profile="brighthive-staging",
    name="STAGE",
    account_type=AccountType.PLATFORM,
)
PROD = AWSAccount(
    account_id="104403016368",
    profile="brighthive-production",
    name="PROD",
    account_type=AccountType.PLATFORM,
)

# ── PROD Test & Demo ─────────────────────────────────────────────
PROD_TEST_WS = AWSAccount(
    account_id="789941350443",
    profile="prod-test-ws",
    name="ProdTestWorkspace",
    account_type=AccountType.TEST,
    entity_type=EntityType.WORKSPACE,
    parent_env="PROD",
)
PROD_TEST_ORG = AWSAccount(
    account_id="128245155604",
    profile="prod-test-org",
    name="ProdTestOrganization",
    account_type=AccountType.TEST,
    entity_type=EntityType.ORGANIZATION,
    parent_env="PROD",
)
PROD_DEMO_WS = AWSAccount(
    account_id="985539759307",
    profile="prod-demo-ws",
    name="BrighthiveDemoEnvironment",
    account_type=AccountType.DEMO,
    entity_type=EntityType.WORKSPACE,
    parent_env="PROD",
)

# ── STAGE Test & Demo ────────────────────────────────────────────
STAGE_TEST_WS = AWSAccount(
    account_id="930996402201",
    profile="stage-test-ws",
    name="StagingTestWorkspace",
    account_type=AccountType.TEST,
    entity_type=EntityType.WORKSPACE,
    parent_env="STAGE",
)
STAGE_TEST_ORG = AWSAccount(
    account_id="635116939665",
    profile="stage-test-org",
    name="StagingTestOrganization",
    account_type=AccountType.TEST,
    entity_type=EntityType.ORGANIZATION,
    parent_env="STAGE",
)
STAGE_DEMO_WS = AWSAccount(
    account_id="637423483585",
    profile="stage-demo-ws",
    name="StagingInternalDemoWorkspace",
    account_type=AccountType.DEMO,
    entity_type=EntityType.WORKSPACE,
    parent_env="STAGE",
)
STAGE_DEMO_ORG = AWSAccount(
    account_id="905418059066",
    profile="stage-demo-org",
    name="StagingInternalDemoOrganization",
    account_type=AccountType.DEMO,
    entity_type=EntityType.ORGANIZATION,
    parent_env="STAGE",
)
DEMO_ENV = AWSAccount(
    account_id="783764595475",
    profile="demo-env",
    name="BrighthiveDemoEnvironment",
    account_type=AccountType.DEMO,
    entity_type=EntityType.WORKSPACE,
    parent_env="STAGE",
)
DEMO_ORG = AWSAccount(
    account_id="340752819582",
    profile="demo-org",
    name="DemoEnv",
    account_type=AccountType.DEMO,
    entity_type=EntityType.ORGANIZATION,
    parent_env="STAGE",
)

# ── Other Accounts ───────────────────────────────────────────────
SECURITY = AWSAccount(
    account_id="085086814866",
    profile="brighthive-security",
    name="brighthive-security",
    account_type=AccountType.OTHER,
    sso_role="SecurityAudit",
)
DEPLOYMENT = AWSAccount(
    account_id="068555976498",
    profile="brighthive-deployment",
    name="brighthive-deployment",
    account_type=AccountType.OTHER,
    sso_role="SecurityAudit",
)

# ── Lookup Dicts (backwards-compatible with existing vault CLIs) ─
PLATFORM_ACCOUNTS: list[AWSAccount] = [MAIN, DEV, STAGE, PROD]
TEST_DEMO_ACCOUNTS: list[AWSAccount] = [
    PROD_TEST_WS, PROD_TEST_ORG, PROD_DEMO_WS,
    STAGE_TEST_WS, STAGE_TEST_ORG, STAGE_DEMO_WS, STAGE_DEMO_ORG,
    DEMO_ENV, DEMO_ORG,
]
ALL_ACCOUNTS: list[AWSAccount] = PLATFORM_ACCOUNTS + TEST_DEMO_ACCOUNTS + [SECURITY, DEPLOYMENT]

# Backwards-compatible dicts — drop-in replacement for old config.py
AWS_ACCOUNTS: dict[str, str] = {acct.name: acct.account_id for acct in PLATFORM_ACCOUNTS}
AWS_PROFILES: dict[str, str] = {acct.name: acct.profile for acct in PLATFORM_ACCOUNTS}
AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")


def get_account(name: str) -> AWSAccount | None:
    """Look up account by name, profile, or alias (case-insensitive)."""
    name_lower = name.lower().replace("-", "").replace("_", "")
    for acct in ALL_ACCOUNTS:
        candidates = [
            acct.name.lower().replace("-", "").replace("_", ""),
            acct.profile.lower().replace("-", ""),
        ]
        if name_lower in candidates:
            return acct
    return None


def get_accounts_for_env(env: str) -> list[AWSAccount]:
    """Get all test/demo accounts for a given environment (PROD, STAGE)."""
    return [acct for acct in TEST_DEMO_ACCOUNTS if acct.parent_env == env.upper()]
