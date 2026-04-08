"""
Secret classifier - categorizes secrets by type using pattern matching.
"""

import json
import re
from typing import Dict, Any, Optional
from models import SecretType, SecretClassification


class SecretClassifier:
    """Classifies secrets into types based on name patterns and content."""

    def __init__(self):
        """Initialize classifier with pattern rules."""
        self.patterns = {
            SecretType.DATABASE_PASSWORD: {
                "name_patterns": [
                    r"(?:redshift|rds|postgres|mysql|db|database).*(?:password|pwd|pass)",
                    r"(?:password|pwd|pass).*(?:redshift|rds|postgres|mysql|db|database)",
                    r"db_password",
                    r"database_password",
                ],
                "content_patterns": [
                    r"username.*password",
                    r"host.*port.*database",
                    r"jdbc:.*connection",
                ],
                "confidence_boost": 0.9,
            },
            SecretType.API_KEY: {
                "name_patterns": [
                    r"(?:api|apikey|api_key).*(?:key|token|secret)",
                    r"(?:key|token|secret).*(?:api|apikey)",
                    r"api_key",
                    r"apikey",
                    r"api_secret",
                ],
                "content_patterns": [
                    r"sk_[a-z0-9]{24,}",  # Stripe-like format
                    r"api[_-]?key",
                    r"access[_-]?key",
                ],
                "confidence_boost": 0.85,
            },
            SecretType.SSH_KEY: {
                "name_patterns": [
                    r"ssh",
                    r"private[_-]?key",
                    r"rsa[_-]?key",
                    r"pem",
                    r"id_rsa",
                ],
                "content_patterns": [
                    r"-----BEGIN.*PRIVATE KEY-----",
                    r"-----BEGIN RSA PRIVATE KEY-----",
                    r"-----BEGIN OPENSSH PRIVATE KEY-----",
                ],
                "confidence_boost": 0.99,
            },
            SecretType.CONNECTION_STRING: {
                "name_patterns": [
                    r"connection",
                    r"connection[_-]?string",
                    r"conn[_-]?str",
                    r"dsn",
                ],
                "content_patterns": [
                    r"(?:user|username|uid)=.*(?:password|pwd)",
                    r"server=.*database=",
                    r"host=.*port=",
                ],
                "confidence_boost": 0.9,
            },
            SecretType.OAUTH_TOKEN: {
                "name_patterns": [
                    r"oauth",
                    r"jwt",
                    r"token",
                    r"access[_-]?token",
                    r"refresh[_-]?token",
                    r"github[_-]?token",
                    r"slack[_-]?token",
                ],
                "content_patterns": [
                    r"eyJ[a-zA-Z0-9_-]{20,}",  # JWT format
                    r"^[a-z0-9]{40,}$",  # Token-like format
                ],
                "confidence_boost": 0.85,
            },
            SecretType.WEBHOOK_SECRET: {
                "name_patterns": [
                    r"webhook",
                    r"hook[_-]?secret",
                    r"signing[_-]?secret",
                ],
                "content_patterns": [
                    r"whsec_[a-z0-9]{30,}",
                    r"webhook",
                ],
                "confidence_boost": 0.8,
            },
            SecretType.ENCRYPTION_KEY: {
                "name_patterns": [
                    r"encryption",
                    r"cipher",
                    r"kms",
                    r"key",
                    r"master[_-]?key",
                ],
                "content_patterns": [
                    r"-----BEGIN.*KEY-----",
                ],
                "confidence_boost": 0.75,
            },
            SecretType.CERTIFICATE: {
                "name_patterns": [
                    r"cert",
                    r"certificate",
                    r"ssl",
                    r"tls",
                    r"ca[_-]?cert",
                ],
                "content_patterns": [
                    r"-----BEGIN CERTIFICATE-----",
                    r"-----BEGIN X509 CERTIFICATE-----",
                ],
                "confidence_boost": 0.95,
            },
            SecretType.CREDENTIALS_JSON: {
                "name_patterns": [
                    r"credentials",
                    r"service[_-]?account",
                    r"json",
                ],
                "content_patterns": [
                    r'{\s*"[a-z_]+"\s*:',  # JSON-like format
                ],
                "confidence_boost": 0.8,
            },
        }

    def classify(
        self, secret_name: str, secret_value: Optional[str] = None
    ) -> SecretClassification:
        """
        Classify a secret by name and optional content.

        Args:
            secret_name: Name of the secret
            secret_value: Optional content/value of the secret

        Returns:
            SecretClassification with type, confidence, and evidence
        """
        name_lower = secret_name.lower()
        value_lower = secret_value.lower() if secret_value else ""

        best_type = SecretType.UNKNOWN
        best_confidence = 0.0
        best_patterns = []
        best_evidence = {}

        for secret_type, rules in self.patterns.items():
            confidence = 0.0
            matched_patterns = []
            evidence = {}

            # Check content patterns first (higher priority)
            if secret_value:
                for pattern in rules["content_patterns"]:
                    if re.search(pattern.lower(), value_lower, re.DOTALL):
                        confidence = rules["confidence_boost"]
                        matched_patterns.append(f"content:{pattern}")
                        evidence["content_match"] = True
                        break

            # Check name patterns
            for pattern in rules["name_patterns"]:
                if re.search(pattern, name_lower):
                    confidence = max(confidence, rules["confidence_boost"])
                    matched_patterns.append(f"name:{pattern}")
                    evidence["name_match"] = secret_name

            # Update best match
            if confidence > best_confidence:
                best_confidence = confidence
                best_type = secret_type
                best_patterns = matched_patterns
                best_evidence = evidence

        return SecretClassification(
            secret_type=best_type,
            confidence=round(best_confidence, 2),
            patterns_matched=best_patterns,
            evidence=best_evidence,
        )
