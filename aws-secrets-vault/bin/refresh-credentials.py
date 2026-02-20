#!/usr/bin/env python3
"""
AWS Credentials Refresher

Assumes roles into all 4 BrightHive accounts and updates ~/.aws/credentials
with fresh temporary credentials.

Usage:
    ./bin/refresh-credentials.py
    ./bin/refresh-credentials.py --source-profile my-admin-profile
    ./bin/refresh-credentials.py --duration 3600
"""

import sys
import argparse
import boto3
import configparser
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# BrightHive account configuration
ACCOUNTS = {
    "DEV": {
        "account_id": "531731217746",
        "role_name": "cdk-admin",
        "profile": "brighthive-dev",
    },
    "STAGE": {
        "account_id": "873769991712",
        "role_name": "cdk-admin",
        "profile": "brighthive-stage",
    },
    "PROD": {
        "account_id": "104403016368",
        "role_name": "cdk-admin",
        "profile": "brighthive-prod",
    },
    "MAIN": {
        "account_id": "396527728813",
        "role_name": "cdk-admin",
        "profile": "brighthive-main",
    },
}

DEFAULT_DURATION = 3600  # 1 hour
MAX_DURATION = 43200  # 12 hours


def assume_role(sts_client, account_id: str, role_name: str, duration: int) -> dict:
    """
    Assume role in target account and get temporary credentials.

    Args:
        sts_client: Boto3 STS client
        account_id: Target AWS account ID
        role_name: Role name to assume
        duration: Session duration in seconds

    Returns:
        Dictionary with temporary credentials
    """
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
        logger.error(f"Failed to assume role in {account_id}: {str(e)}")
        raise


def update_credentials_file(credentials_dict: dict) -> None:
    """
    Update ~/.aws/credentials with new temporary credentials.

    Args:
        credentials_dict: Dictionary mapping profile names to credentials
    """
    creds_file = Path.home() / ".aws" / "credentials"

    # Read existing credentials
    config = configparser.ConfigParser()
    if creds_file.exists():
        config.read(creds_file)

    # Update profiles with new credentials
    for profile, creds in credentials_dict.items():
        if profile not in config:
            config[profile] = {}

        config[profile]["aws_access_key_id"] = creds["aws_access_key_id"]
        config[profile]["aws_secret_access_key"] = creds["aws_secret_access_key"]
        config[profile]["aws_session_token"] = creds["aws_session_token"]
        # Note: configparser doesn't write comments, but we'll add the expiration
        config[profile]["expires_at"] = creds["expiration"]
        config[profile]["region"] = "us-east-1"

    # Write back to file
    creds_file.parent.mkdir(parents=True, exist_ok=True)
    with open(creds_file, "w") as f:
        config.write(f)

    # Set restrictive permissions (600 = rw-------)
    creds_file.chmod(0o600)

    logger.info(f"✅ Updated credentials file: {creds_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Refresh AWS credentials for all BrightHive accounts"
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

    # Validate duration
    if args.duration < 900:
        logger.error("Duration must be at least 900 seconds (15 minutes)")
        sys.exit(1)
    if args.duration > MAX_DURATION:
        logger.warning(
            f"Duration exceeds max {MAX_DURATION}s, capping to {MAX_DURATION}s"
        )
        args.duration = MAX_DURATION

    logger.info("🔄 Refreshing AWS credentials...")
    logger.info(f"   Source profile: {args.source_profile}")
    logger.info(f"   Duration: {args.duration}s (~{args.duration//3600}h)")
    logger.info(f"   Accounts: {', '.join(args.accounts)}")
    logger.info("")

    # Create STS client with source profile
    try:
        session = boto3.Session(profile_name=args.source_profile)
        sts_client = session.client("sts", region_name="us-east-1")

        # Verify we have valid credentials
        caller_identity = sts_client.get_caller_identity()
        logger.info(f"✓ Authenticated as: {caller_identity['Arn']}")
        logger.info("")

    except Exception as e:
        logger.error(f"Failed to initialize STS client: {str(e)}")
        logger.error(f"Make sure profile '{args.source_profile}' is configured")
        sys.exit(1)

    # Assume roles into each account
    new_credentials = {}
    for account_name in args.accounts:
        account = ACCOUNTS[account_name]
        logger.info(f"🔐 Assuming role into {account_name}...")

        try:
            creds = assume_role(
                sts_client=sts_client,
                account_id=account["account_id"],
                role_name=account["role_name"],
                duration=args.duration,
            )

            expiration = creds["expiration"]
            logger.info(f"   ✓ Got temporary credentials (expires: {expiration})")

            new_credentials[account["profile"]] = creds

        except Exception as e:
            logger.error(f"   ✗ Failed: {str(e)}")
            sys.exit(1)

    logger.info("")

    # Update credentials file
    if args.dry_run:
        logger.info("📋 DRY RUN - Would update the following profiles:")
        for profile in new_credentials.keys():
            logger.info(f"   - {profile}")
    else:
        logger.info("📝 Updating ~/.aws/credentials...")
        try:
            update_credentials_file(new_credentials)
            logger.info("")
            logger.info("✅ All credentials refreshed successfully!")
            logger.info("")
            logger.info("Next steps:")
            logger.info("  cd /Users/bado/iccha/brighthive/agentic-project-mgmt/aws-secrets-vault")
            logger.info("  source .venv/bin/activate")
            logger.info("  ./cli/secrets list")

        except Exception as e:
            logger.error(f"Failed to update credentials: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
