"""AWS Secrets Manager vault library."""

from .models import Secret, SecretType, SecretClassification
from .classifier import SecretClassifier
from .aws_client import AWSSecretsManager
from .indexer import build_index, write_index, write_aliases

__all__ = [
    "Secret",
    "SecretType",
    "SecretClassification",
    "SecretClassifier",
    "AWSSecretsManager",
    "build_index",
    "write_index",
    "write_aliases",
]
