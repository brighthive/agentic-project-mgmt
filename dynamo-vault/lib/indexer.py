"""Index building and export for workspace configurations."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from models import ConfigIndex, WorkspaceConfig

logger = logging.getLogger(__name__)


def build_index(
    workspaces: list[WorkspaceConfig],
    account_name: str,
) -> ConfigIndex:
    """Build a ConfigIndex from workspace configs."""
    return ConfigIndex(
        workspaces=workspaces,
        generated_at=datetime.now().isoformat(),
        account_name=account_name,
    )


def write_index(
    index: ConfigIndex,
    output_dir: Path,
    show_secrets: bool = False,
) -> tuple[Path, Path]:
    """Write index to JSON and markdown files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "index.json"
    with open(json_path, "w") as f:
        json.dump(index.to_dict(show_secrets=show_secrets), f, indent=2)
    logger.info(f"Wrote JSON index to {json_path}")

    md_path = output_dir / "index.md"
    with open(md_path, "w") as f:
        f.write(generate_markdown(index=index))
    logger.info(f"Wrote markdown index to {md_path}")

    return json_path, md_path


def generate_markdown(index: ConfigIndex) -> str:
    """Generate markdown summary of workspace configs."""
    lines = [
        "# DynamoDB Workspace Configuration Index",
        "",
        f"**Generated**: {index.generated_at}",
        f"**Account**: {index.account_name}",
        "",
        "## Summary",
        "",
        f"- **Total Workspaces**: {index.summary['total_workspaces']}",
    ]

    for entity_type, count in index.summary["by_entity_type"].items():
        lines.append(f"- **{entity_type}**: {count}")

    lines.append("")
    lines.append("## Workspaces")
    lines.append("")
    lines.append("| Name | UUID | Type | AWS Account | Env Secret |")
    lines.append("|------|------|------|-------------|------------|")

    for ws in sorted(index.workspaces, key=lambda w: w.name):
        env_secret = "Yes" if ws.env_secret_arn else "No"
        lines.append(
            f"| {ws.name} | `{ws.uuid[:12]}...` | {ws.entity_type.value} "
            f"| {ws.aws_account_number or '—'} | {env_secret} |"
        )

    lines.append("")
    return "\n".join(lines)


def generate_diff(
    ws_a: WorkspaceConfig,
    ws_b: WorkspaceConfig,
) -> list[str]:
    """Compare two workspace configs and return diff lines."""
    lines = [
        f"# Diff: {ws_a.name}",
        f"**{ws_a.account_name}** vs **{ws_b.account_name}**",
        "",
    ]

    fields_to_compare = [
        ("entity_type", "Entity Type"),
        ("owner", "Owner"),
        ("environment", "Environment"),
        ("aws_account_number", "AWS Account #"),
        ("env_secret_arn", "EnvSecretArn"),
        ("account_secret_arn", "AccountSecretARN"),
        ("cdk_stack_arn", "CDK Stack ARN"),
        ("s3_role_arn", "S3 Role ARN"),
    ]

    diffs_found = False

    for attr, label in fields_to_compare:
        val_a = getattr(ws_a, attr)
        val_b = getattr(ws_b, attr)
        if val_a != val_b:
            diffs_found = True
            lines.append(f"### {label}")
            lines.append(f"- **{ws_a.account_name}**: `{val_a}`")
            lines.append(f"- **{ws_b.account_name}**: `{val_b}`")
            lines.append("")

    # Compare dict fields
    dict_fields = [
        ("api_urls", "API URLs"),
        ("iam_roles", "IAM Roles"),
        ("s3_buckets", "S3 Buckets"),
        ("neo4j_envs", "Neo4j Envs"),
    ]

    for attr, label in dict_fields:
        dict_a = getattr(ws_a, attr)
        dict_b = getattr(ws_b, attr)
        if dict_a != dict_b:
            diffs_found = True
            lines.append(f"### {label}")
            keys = set(dict_a.keys()) | set(dict_b.keys())
            for key in sorted(keys):
                va = dict_a.get(key, "—")
                vb = dict_b.get(key, "—")
                if va != vb:
                    lines.append(f"- **{key}**:")
                    lines.append(f"  - {ws_a.account_name}: `{va}`")
                    lines.append(f"  - {ws_b.account_name}: `{vb}`")
            lines.append("")

    if not diffs_found:
        lines.append("No differences found.")

    return lines
