#!/usr/bin/env python3
"""Update Sprint 4 tickets with missing template sections and story points.

This script:
1. Appends Dependencies + Size sections to 9 tickets
2. Replaces full descriptions for 2 tickets (BH-249, BH-254)
3. Reassigns and sets points for 2 tickets (BH-256, BH-257)

Uses Atlassian Document Format (ADF) for descriptions.
"""

import json
import sys
from pathlib import Path
from typing import Any

import requests

# Add jira_lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "jira_lib"))

from jira_config import load_config


def create_adf_heading(level: int, text: str) -> dict[str, Any]:
    """Create ADF heading node."""
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def create_adf_paragraph(text: str) -> dict[str, Any]:
    """Create ADF paragraph node."""
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def create_adf_bullet_list(items: list[str]) -> dict[str, Any]:
    """Create ADF bullet list node."""
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": item}]}],
            }
            for item in items
        ],
    }


def create_full_adf_document(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Create complete ADF document."""
    return {"version": 1, "type": "doc", "content": sections}


def get_issue_description(base_url: str, auth: tuple[str, str], issue_key: str) -> dict[str, Any] | None:
    """Fetch current description for an issue."""
    url = f"{base_url}/rest/api/3/issue/{issue_key}?fields=description"
    response = requests.get(url=url, auth=auth, headers={"Accept": "application/json"}, timeout=10)

    if response.status_code == 200:
        data = response.json()
        return data.get("fields", {}).get("description")

    print(f"  ✗ Failed to fetch description for {issue_key}: {response.status_code}")
    return None


def update_issue_description(
    base_url: str, auth: tuple[str, str], issue_key: str, description: dict[str, Any]
) -> bool:
    """Update issue description using ADF format."""
    url = f"{base_url}/rest/api/3/issue/{issue_key}"
    payload = {"fields": {"description": description}}

    response = requests.put(
        url=url,
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )

    if response.status_code == 204:
        print(f"  ✓ Updated description for {issue_key}")
        return True

    print(f"  ✗ Failed to update description for {issue_key}: {response.status_code}")
    print(f"    Response: {response.text[:200]}")
    return False


def set_story_points(base_url: str, auth: tuple[str, str], issue_key: str, points: int) -> bool:
    """Set story points for an issue."""
    url = f"{base_url}/rest/agile/1.0/issue/{issue_key}/estimation?boardId=152"
    payload = {"value": points}

    response = requests.put(
        url=url,
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )

    if response.status_code == 200:
        print(f"  ✓ Set story points to {points} for {issue_key}")
        return True

    print(f"  ✗ Failed to set story points for {issue_key}: {response.status_code}")
    print(f"    Response: {response.text[:200]}")
    return False


def assign_issue(base_url: str, auth: tuple[str, str], issue_key: str, account_id: str) -> bool:
    """Assign issue to user."""
    url = f"{base_url}/rest/api/3/issue/{issue_key}/assignee"
    payload = {"accountId": account_id}

    response = requests.put(
        url=url,
        auth=auth,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )

    if response.status_code == 204:
        print(f"  ✓ Assigned {issue_key} to {account_id}")
        return True

    print(f"  ✗ Failed to assign {issue_key}: {response.status_code}")
    print(f"    Response: {response.text[:200]}")
    return False


def get_user_account_id(base_url: str, auth: tuple[str, str], issue_key: str) -> str | None:
    """Get account ID from an issue's assignee (to find Marwan's ID)."""
    url = f"{base_url}/rest/api/3/issue/{issue_key}?fields=assignee"
    response = requests.get(url=url, auth=auth, headers={"Accept": "application/json"}, timeout=10)

    if response.status_code == 200:
        data = response.json()
        assignee = data.get("fields", {}).get("assignee")
        if assignee:
            return assignee.get("accountId")

    return None


def append_dependencies_and_size(
    base_url: str, auth: tuple[str, str], issue_key: str, dependencies: list[str], size_text: str
) -> bool:
    """Append Dependencies and Size Estimate sections to existing description."""
    # Get current description
    current_desc = get_issue_description(base_url=base_url, auth=auth, issue_key=issue_key)

    if not current_desc:
        print(f"  ✗ No existing description found for {issue_key}")
        return False

    # Append new sections
    content = current_desc.get("content", [])

    # Add Dependencies section
    content.append(create_adf_heading(level=2, text="🔗 Dependencies"))
    content.append(create_adf_bullet_list(items=dependencies))

    # Add Size Estimate section
    content.append(create_adf_heading(level=2, text="📏 Size Estimate"))
    content.append(create_adf_paragraph(text=size_text))

    # Update document
    updated_desc = {"version": 1, "type": "doc", "content": content}

    return update_issue_description(base_url=base_url, auth=auth, issue_key=issue_key, description=updated_desc)


def create_full_template_description(
    description: str, scope_include: list[str], scope_exclude: list[str], acceptance: list[str],
    dependencies: list[str], size_text: str
) -> dict[str, Any]:
    """Create full ticket description with all template sections."""
    sections = []

    # Description
    sections.append(create_adf_heading(level=2, text="📝 Description"))
    sections.append(create_adf_paragraph(text=description))

    # Scope
    sections.append(create_adf_heading(level=2, text="📍 Scope"))
    sections.append(create_adf_heading(level=3, text="Include"))
    sections.append(create_adf_bullet_list(items=scope_include))
    sections.append(create_adf_heading(level=3, text="Exclude"))
    sections.append(create_adf_bullet_list(items=scope_exclude))

    # Acceptance Criteria
    sections.append(create_adf_heading(level=2, text="✅ Acceptance Criteria"))
    sections.append(create_adf_bullet_list(items=acceptance))

    # Dependencies
    sections.append(create_adf_heading(level=2, text="🔗 Dependencies"))
    sections.append(create_adf_bullet_list(items=dependencies))

    # Size Estimate
    sections.append(create_adf_heading(level=2, text="📏 Size Estimate"))
    sections.append(create_adf_paragraph(text=size_text))

    return create_full_adf_document(sections=sections)


def main() -> None:
    """Execute all ticket updates."""
    # Load config
    config = load_config()
    base_url = config.base_url
    auth = config.auth

    print("=" * 80)
    print("Sprint 4 Ticket Updates")
    print("=" * 80)

    # Get Marwan's account ID from BH-236
    print("\n1. Getting Marwan's account ID from BH-236...")
    marwan_id = get_user_account_id(base_url=base_url, auth=auth, issue_key="BH-236")
    if not marwan_id:
        print("  ✗ Failed to get Marwan's account ID. Exiting.")
        sys.exit(1)
    print(f"  ✓ Marwan's account ID: {marwan_id}")

    # Tickets needing only Dependencies + Size appended
    print("\n2. Appending Dependencies + Size to 9 tickets...")

    updates = [
        {
            "key": "BH-136",
            "deps": [
                "BH-254 (enhance logging - related)",
                "Existing APM/monitoring tools in platform-core",
            ],
            "size": "3 story points — Audit scope across existing services, document findings, recommend tooling",
        },
        {
            "key": "BH-210",
            "deps": [
                "BH-246 (local dev + seeding for testing)",
                "BH-240 (context API for project context injection)",
            ],
            "size": "5 story points — BHAgent integration requires context injection, session management, and project-scoped agent responses",
        },
        {
            "key": "BH-226",
            "deps": ["Platform-core auth/permission system"],
            "size": "2 story points — Permission fix on existing GraphQL mutation, straightforward auth adjustment",
        },
        {
            "key": "BH-233",
            "deps": ["BH-230 (OpenMetadata PII detection lambda — Done)"],
            "size": "2 story points — Script creation with existing Lambda infrastructure, quick utility task",
        },
        {
            "key": "BH-238",
            "deps": [
                "Airbyte connector framework",
                "S3 bucket access",
                "platform-core ingestion pipeline",
            ],
            "size": "5 story points — New connector type supporting multiple file formats, parsing logic, and warehouse integration",
        },
        {
            "key": "BH-239",
            "deps": ["BH-240 (Context Engineering workspace API — must land first)"],
            "size": "3 story points — Frontend UI with \"Coming Soon\" placeholder, context display components",
        },
        {
            "key": "BH-240",
            "deps": ["CEMAF architecture", "Neo4j workspace context model"],
            "size": "3 story points — API endpoints for context CRUD, CEMAF integration, workspace scoping",
        },
        {
            "key": "BH-241",
            "deps": [
                "BH-210 (Project BHAgent integration — same work stream)",
                "BH-246 (local dev for testing)",
            ],
            "size": "5 story points — Agent capability integration with project containers, context-aware responses",
        },
        {
            "key": "BH-242",
            "deps": [
                "BH-210 (Project BHAgent integration — API must exist)",
                "BH-241 (BE integration)",
            ],
            "size": "3 story points — Chat UI scoped to project, agent invocation from frontend",
        },
    ]

    for update in updates:
        print(f"\n  {update['key']}:")
        append_dependencies_and_size(
            base_url=base_url,
            auth=auth,
            issue_key=update["key"],
            dependencies=update["deps"],
            size_text=update["size"],
        )

    # BH-249: Full template replacement (needs 2 points)
    print("\n3. Replacing full description for BH-249...")
    bh249_desc = create_full_template_description(
        description="Remove Router V1 dead code (~200 lines) from brightbot-slack-server. V1 (intent-classifier → mcp-router → tool-executor) is never called. V2 is the active router. Rename V2 files to remove the \"V2\" suffix for clean naming.",
        scope_include=[
            "Delete V1 router files",
            "Rename V2 files to standard names",
            "Update all imports",
            "Verify app.ts references",
        ],
        scope_exclude=["New router features", "Test additions", "Architectural changes"],
        acceptance=[
            "V1 code fully removed",
            "V2 files renamed without \"V2\" suffix",
            "All imports updated",
            "App starts and routes correctly",
            "No dead code references remain",
        ],
        dependencies=["BH-244 (Slack Intent Router — Done, established V2 as active)"],
        size_text="2 story points — Mechanical cleanup, find-and-replace, verify no broken imports",
    )

    update_issue_description(base_url=base_url, auth=auth, issue_key="BH-249", description=bh249_desc)
    set_story_points(base_url=base_url, auth=auth, issue_key="BH-249", points=2)

    # BH-254: Full template replacement (needs 3 points, assign to Ahmed)
    print("\n4. Replacing full description for BH-254...")
    bh254_desc = create_full_template_description(
        description="Enhance platform-core logging and observability. Improve structured logging across API endpoints, add request tracing headers, and ensure logs are queryable for debugging production issues.",
        scope_include=[
            "Structured JSON logging format",
            "Request/response correlation IDs",
            "Error logging with stack traces",
            "Log level configuration per environment",
        ],
        scope_exclude=[
            "External monitoring tool setup (separate from BH-136)",
            "Alerting rules",
            "Dashboard creation",
        ],
        acceptance=[
            "All API endpoints emit structured JSON logs",
            "Correlation IDs propagate across service calls",
            "Error logs include full context",
            "Log levels configurable via env vars",
            "Logs are parseable by CloudWatch/ELK",
        ],
        dependencies=["BH-136 (Audit observability stack — provides recommendations this ticket implements)"],
        size_text="3 story points — Logging middleware, structured format, correlation ID propagation across services",
    )

    update_issue_description(base_url=base_url, auth=auth, issue_key="BH-254", description=bh254_desc)
    set_story_points(base_url=base_url, auth=auth, issue_key="BH-254", points=3)

    # Get Ahmed's account ID from BH-136 (already assigned to him)
    print("\n5. Getting Ahmed's account ID from BH-136...")
    ahmed_id = get_user_account_id(base_url=base_url, auth=auth, issue_key="BH-136")
    if ahmed_id:
        print(f"  ✓ Ahmed's account ID: {ahmed_id}")
        assign_issue(base_url=base_url, auth=auth, issue_key="BH-254", account_id=ahmed_id)
    else:
        print("  ✗ Failed to get Ahmed's account ID from BH-136")

    # BH-256: Reassign to Marwan + set 5 points
    print("\n6. Reassigning BH-256 to Marwan and setting 5 story points...")
    assign_issue(base_url=base_url, auth=auth, issue_key="BH-256", account_id=marwan_id)
    set_story_points(base_url=base_url, auth=auth, issue_key="BH-256", points=5)

    # BH-257: Reassign to Marwan + set 5 points
    print("\n7. Reassigning BH-257 to Marwan and setting 5 story points...")
    assign_issue(base_url=base_url, auth=auth, issue_key="BH-257", account_id=marwan_id)
    set_story_points(base_url=base_url, auth=auth, issue_key="BH-257", points=5)

    print("\n" + "=" * 80)
    print("✓ All updates complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
