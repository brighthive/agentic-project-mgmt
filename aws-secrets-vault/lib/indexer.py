"""
Secret indexing and export functionality.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

from models import Secret, SecretsIndex, SecretType

logger = logging.getLogger(__name__)


def build_summary(secrets: List[Secret]) -> Dict[str, Any]:
    """
    Build summary statistics for secrets.

    Args:
        secrets: List of Secret objects

    Returns:
        Summary dictionary with counts and breakdowns
    """
    summary = {
        "total_secrets": len(secrets),
        "by_type": defaultdict(int),
        "by_account": defaultdict(int),
        "by_account_and_type": defaultdict(lambda: defaultdict(int)),
    }

    for secret in secrets:
        if secret.classification:
            secret_type = secret.classification.secret_type.value
            summary["by_type"][secret_type] += 1
            summary["by_account_and_type"][secret.account_name][secret_type] += 1

        summary["by_account"][secret.account_name] += 1

    # Convert defaultdicts to regular dicts
    summary["by_type"] = dict(summary["by_type"])
    summary["by_account"] = dict(summary["by_account"])
    summary["by_account_and_type"] = {
        k: dict(v) for k, v in summary["by_account_and_type"].items()
    }

    return summary


def build_index(secrets: List[Secret]) -> SecretsIndex:
    """
    Build searchable index of all secrets.

    Args:
        secrets: List of Secret objects

    Returns:
        SecretsIndex with all secrets and summary
    """
    summary = build_summary(secrets)
    return SecretsIndex(
        secrets=secrets,
        summary=summary,
        generated_at=datetime.now(),
    )


def write_index(index: SecretsIndex, output_dir: Path) -> tuple[Path, Path]:
    """
    Write index to JSON and markdown files.

    Args:
        index: SecretsIndex to write
        output_dir: Directory to write files

    Returns:
        Tuple of (json_path, md_path)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON index
    json_path = output_dir / "index.json"
    with open(json_path, "w") as f:
        json.dump(index.to_dict(), f, indent=2)
    logger.info(f"[INDEX] Wrote JSON index to {json_path}")

    # Write markdown documentation
    md_path = output_dir / "index.md"
    with open(md_path, "w") as f:
        f.write(generate_markdown(index))
    logger.info(f"[INDEX] Wrote markdown index to {md_path}")

    return json_path, md_path


def write_aliases(secrets: List[Secret], output_dir: Path) -> Path:
    """
    Write alias/lookup tables for fast retrieval.

    Args:
        secrets: List of Secret objects
        output_dir: Directory to write files

    Returns:
        Path to aliases.json
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    aliases = {
        "by_id": {},
        "by_name": {},
        "by_type": defaultdict(list),
        "by_account": defaultdict(list),
    }

    for secret in secrets:
        secret_dict = secret.to_dict()

        # by_id
        aliases["by_id"][secret.name] = secret_dict

        # by_name (for substring search)
        aliases["by_name"][secret.name.lower()] = secret.name

        # by_type
        if secret.classification:
            secret_type = secret.classification.secret_type.value
            aliases["by_type"][secret_type].append(secret.name)

        # by_account
        aliases["by_account"][secret.account_name].append(secret.name)

    # Convert defaultdicts to regular dicts
    aliases["by_type"] = {k: v for k, v in aliases["by_type"].items()}
    aliases["by_account"] = {k: v for k, v in aliases["by_account"].items()}

    aliases_path = output_dir / "aliases.json"
    with open(aliases_path, "w") as f:
        json.dump(aliases, f, indent=2)
    logger.info(f"[INDEX] Wrote aliases to {aliases_path}")

    return aliases_path


def materialize_metadata(secrets: List[Secret], output_dir: Path) -> Path:
    """
    Organize secrets into directories by type.

    Args:
        secrets: List of Secret objects
        output_dir: Base directory for organization

    Returns:
        Path to output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Group by type
    by_type = defaultdict(list)
    for secret in secrets:
        if secret.classification:
            secret_type = secret.classification.secret_type.value
        else:
            secret_type = "unclassified"
        by_type[secret_type].append(secret)

    # Create subdirectories
    for secret_type, type_secrets in by_type.items():
        type_dir = output_dir / secret_type
        type_dir.mkdir(exist_ok=True)

        # Write secrets to individual files
        for secret in type_secrets:
            # Sanitize filename
            filename = secret.name.replace("/", "_").replace(" ", "_") + ".json"
            file_path = type_dir / filename

            with open(file_path, "w") as f:
                json.dump(secret.to_dict(), f, indent=2)

        logger.info(f"[ORG] Organized {len(type_secrets)} secrets by type: {secret_type}")

    return output_dir


def generate_markdown(index: SecretsIndex) -> str:
    """
    Generate markdown documentation for index.

    Args:
        index: SecretsIndex to document

    Returns:
        Markdown string
    """
    lines = [
        "# AWS Secrets Manager Inventory",
        "",
        f"**Generated**: {index.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- **Total Secrets**: {index.summary['total_secrets']}",
        "",
    ]

    # By account
    if index.summary["by_account"]:
        lines.append("### By Account")
        lines.append("")
        for account, count in sorted(index.summary["by_account"].items()):
            lines.append(f"- **{account}**: {count} secrets")
        lines.append("")

    # By type
    if index.summary["by_type"]:
        lines.append("### By Type")
        lines.append("")
        for secret_type, count in sorted(index.summary["by_type"].items()):
            lines.append(f"- **{secret_type}**: {count} secrets")
        lines.append("")

    # Detailed listing
    lines.append("## Secrets")
    lines.append("")

    for secret in sorted(index.secrets, key=lambda s: (s.account_name, s.name)):
        lines.append(f"### {secret.name}")
        lines.append("")
        lines.append(f"- **Account**: {secret.account_name} ({secret.account_id})")
        lines.append(
            f"- **Created**: {secret.metadata.created_at.strftime('%Y-%m-%d') if secret.metadata.created_at else 'Unknown'}"
        )

        if secret.classification:
            lines.append(f"- **Type**: {secret.classification.secret_type.value}")
            lines.append(f"- **Confidence**: {secret.classification.confidence * 100:.0f}%")

        if secret.metadata.description:
            lines.append(f"- **Description**: {secret.metadata.description}")

        lines.append("")

    return "\n".join(lines)
