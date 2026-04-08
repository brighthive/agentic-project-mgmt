"""
AWS Secrets Manager client for fetching secrets across accounts.
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Optional, List

from config import AWS_ACCOUNTS, AWS_REGION, AWS_PROFILES
from models import Secret, SecretMetadata

logger = logging.getLogger(__name__)


class AWSSecretsManager:
    """Client for fetching secrets from AWS Secrets Manager."""

    def __init__(
        self, account_name: str, region: str = AWS_REGION, profile: Optional[str] = None
    ):
        """
        Initialize AWS Secrets Manager client.

        Args:
            account_name: Account name (DEV, STAGE, PROD, MAIN)
            region: AWS region
            profile: AWS CLI profile (defaults from config or None for default credentials)
        """
        self.account_name = account_name
        self.account_id = AWS_ACCOUNTS.get(account_name)
        self.region = region

        if not self.account_id:
            raise ValueError(f"Unknown account: {account_name}")

        # Use provided profile, or get from config (which may be None for default)
        profile = profile if profile is not None else AWS_PROFILES.get(account_name)

        try:
            # If profile is None, boto3 uses default credentials from environment/~/.aws/credentials
            session = boto3.Session(profile_name=profile, region_name=region)
            self.client = session.client("secretsmanager")
            logger.info(f"[AWS] Initialized client for {account_name} ({self.account_id})")
        except Exception as e:
            logger.error(
                f"[AWS] Failed to initialize client for {account_name}: {str(e)}"
            )
            raise

    def list_all_secrets(self) -> List[str]:
        """
        List all secret names in account.

        Returns:
            List of secret names
        """
        try:
            secrets = []
            paginator = self.client.get_paginator("list_secrets")

            for page in paginator.paginate():
                for secret in page.get("SecretList", []):
                    secrets.append(secret["Name"])

            logger.info(f"[AWS] Found {len(secrets)} secrets in {self.account_name}")
            return secrets

        except Exception as e:
            logger.error(
                f"[AWS] Failed to list secrets in {self.account_name}: {str(e)}"
            )
            raise

    def get_secret_metadata(self, secret_name: str) -> Optional[SecretMetadata]:
        """
        Get metadata for a specific secret.

        Args:
            secret_name: Name of the secret

        Returns:
            SecretMetadata or None if not found
        """
        try:
            response = self.client.describe_secret(SecretId=secret_name)

            return SecretMetadata(
                arn=response["ARN"],
                name=response["Name"],
                description=response.get("Description"),
                created_at=response.get("CreatedDate"),
                last_updated=response.get("LastChangedDate"),
                last_accessed=response.get("LastAccessedDate"),
                rotation_enabled=response.get("RotationEnabled", False),
                rotation_rules=response.get("RotationRules"),
            )

        except self.client.exceptions.ResourceNotFoundException:
            logger.warning(f"[AWS] Secret not found: {secret_name}")
            return None
        except Exception as e:
            logger.error(f"[AWS] Failed to get metadata for {secret_name}: {str(e)}")
            return None

    def get_secret_value(self, secret_name: str) -> Optional[str]:
        """
        Get the value of a secret (for classification).

        Args:
            secret_name: Name of the secret

        Returns:
            Secret value as string, or None if not found/cannot be accessed
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)

            if "SecretString" in response:
                return response["SecretString"]
            elif "SecretBinary" in response:
                return "[BINARY_SECRET]"
            else:
                return None

        except self.client.exceptions.AccessDeniedException:
            logger.warning(f"[AWS] Access denied to secret: {secret_name}")
            return None
        except self.client.exceptions.ResourceNotFoundException:
            logger.warning(f"[AWS] Secret not found: {secret_name}")
            return None
        except Exception as e:
            logger.warning(f"[AWS] Failed to get value for {secret_name}: {str(e)}")
            return None

    def fetch_all_secrets(self) -> List[Secret]:
        """
        Fetch all secrets with metadata from account.

        Returns:
            List of Secret objects
        """
        secrets = []
        secret_names = self.list_all_secrets()

        for i, secret_name in enumerate(secret_names, 1):
            logger.debug(f"[AWS] Fetching {i}/{len(secret_names)}: {secret_name}")

            metadata = self.get_secret_metadata(secret_name)
            if not metadata:
                continue

            secret = Secret(
                name=secret_name,
                account_id=self.account_id,
                account_name=self.account_name,
                metadata=metadata,
            )
            secrets.append(secret)

        return secrets
