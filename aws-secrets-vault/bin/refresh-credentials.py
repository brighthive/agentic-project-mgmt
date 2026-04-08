#!/usr/bin/env python3
"""AWS Credentials Refresher — assumes cdk-admin role into BrightHive accounts.

NOTE: With SSO now configured for all accounts, this script is only needed
for CDK admin credential refresh (writing temp creds to ~/.aws/credentials).
For normal access, use `aws sso login --profile brighthive-main` instead.

Usage:
    ./bin/refresh-credentials.py
    ./bin/refresh-credentials.py --source-profile brighthive-main
    ./bin/refresh-credentials.py --duration 3600
    ./bin/refresh-credentials.py --accounts DEV STAGE
"""

import sys
import argparse
import boto3
import configparser
import logging
from pathlib import Path
from datetime import datetime

# Add repo root to path for shared lib import
_repo_root = Path(__file__).parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.accounts import PLATFORM_ACCOUNTS, AWS_REGION

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Build account config from shared registry
ACCOUNTS = {
    acct.name: {
        "account_id": acct.account_id,
        "role_name": "cdk-admin",
        "profile": acct.profile,
    }
    for acct in PLATFORM_ACCOUNTS
}

DEFAULT_DURATION = 3600  # 1 hour
MAX_DURATION = 43200  # 12 hours


def assume_role(sts_client, account_id: str, role_name: str, duration: int) -> dict:
    """Assume role in target account and get temporary credentials."""
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    session_name = f"brighthive-refresh-{datetime.now().strftime('%s')}"

    try:
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            DurationSeconds=duration,
        )

        credentials = response["Credentials"]
        return {
            "aws_access_key_id": credentials["AccessKeyId"],
            "aws_secret_access_key": credentials["SecretAccessKey"],
            "aws_session_token": credentials["SessionToken"],
            "expiration": credentials["Expiration"].isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to assume role in {account_id}: {e}")
        raise


def update_credentials_file(credentials_dict: dict) -> None:
    """Update ~/.aws/credentials with new temporary credentials."""
    creds_file = Path.home() / ".aws" / "credentials"

    config = configparser.ConfigParser()
    if creds_file.exists():
        config.read(creds_file)

    for profile, creds in credentials_dict.items():
        if profile not in config:
            config[profile] = {}

        config[profile]["aws_access_key_id"] = creds["aws_access_key_id"]
        config[profile]["aws_secret_access_key"] = creds["aws_secret_access_key"]
        config[profile]["aws_session_token"] = creds["aws_session_token"]
        config[profile]["expires_at"] = creds["expiration"]
        config[profile]["region"] = AWS_REGION

    creds_file.parent.mkdir(parents=True, exist_ok=True)
    with open(creds_file, "w") as f:
        config.write(f)

    creds_file.chmod(0o600)
    logger.info(f"Updated credentials file: {creds_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Refresh AWS credentials for BrightHive accounts via cdk-admin role assumption"
    )
    parser.add_argument(
        "--source-profile",
        default="brighthive-main",
        help="Source AWS profile with admin permissions (default: brighthive-main)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"Session duration in seconds (default: {DEFAULT_DURATION}, max: {MAX_DURATION})",
    )
    parser.add_argument(
        "--accounts",
        nargs="+",
        choices=list(ACCOUNTS.keys()),
        default=list(ACCOUNTS.keys()),
        help="Accounts to refresh (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without updating credentials",
    )

    args = parser.parse_args()

    if args.duration < 900:
        logger.error("Duration must be at least 900 seconds (15 minutes)")
        sys.exit(1)
    if args.duration > MAX_DURATION:
        logger.warning(f"Duration exceeds max {MAX_DURATION}s, capping")
        args.duration = MAX_DURATION

    logger.info("Refreshing AWS credentials (cdk-admin role assumption)...")
    logger.info(f"  Source profile: {args.source_profile}")
    logger.info(f"  Duration: {args.duration}s (~{args.duration // 3600}h)")
    logger.info(f"  Accounts: {', '.join(args.accounts)}")
    logger.info("")

    try:
        session = boto3.Session(
            profile_name=args.source_profile, region_name=AWS_REGION
        )
        sts_client = session.client("sts", region_name=AWS_REGION)

        caller_identity = sts_client.get_caller_identity()
        logger.info(f"Authenticated as: {caller_identity['Arn']}")
        logger.info("")

    except Exception as e:
        logger.error(f"Failed to initialize STS client: {e}")
        logger.error(f"Make sure profile '{args.source_profile}' is authenticated")
        logger.error("Run: aws sso login --profile brighthive-main")
        sys.exit(1)

    new_credentials = {}
    for account_name in args.accounts:
        account = ACCOUNTS[account_name]
        logger.info(f"Assuming cdk-admin in {account_name} ({account['account_id']})...")

        try:
            creds = assume_role(
                sts_client=sts_client,
                account_id=account["account_id"],
                role_name=account["role_name"],
                duration=args.duration,
            )

            logger.info(f"  Got temp creds (expires: {creds['expiration']})")
            new_credentials[account["profile"]] = creds

        except Exception as e:
            logger.error(f"  Failed: {e}")
            sys.exit(1)

    logger.info("")

    if args.dry_run:
        logger.info("DRY RUN — would update profiles:")
        for profile in new_credentials:
            logger.info(f"  - {profile}")
    else:
        logger.info("Updating ~/.aws/credentials...")
        try:
            update_credentials_file(new_credentials)
            logger.info("")
            logger.info("All credentials refreshed.")
        except Exception as e:
            logger.error(f"Failed to update credentials: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
