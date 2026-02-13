#!/usr/bin/env python3
"""Verify Sprint 4 ticket updates were successful."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "jira_lib"))

from jira_config import load_config
from jira_client import get

config = load_config()

print("=" * 80)
print("Verifying Sprint 4 Ticket Updates")
print("=" * 80)

tickets = [
    "BH-136", "BH-210", "BH-226", "BH-233", "BH-238", 
    "BH-239", "BH-240", "BH-241", "BH-242", 
    "BH-249", "BH-254", "BH-256", "BH-257"
]

for ticket in tickets:
    data, error = get(config, f"/rest/api/3/issue/{ticket}?fields=summary,assignee,customfield_10016,description")
    if error:
        print(f"\n{ticket}: ERROR - {error.message}")
    else:
        fields = data.get("fields", {})
        assignee = fields.get("assignee", {})
        assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
        points = fields.get("customfield_10016")
        description = fields.get("description", {})
        content = description.get("content", [])
        
        # Count Dependencies and Size sections
        headings = [c.get("content", [{}])[0].get("text", "") for c in content if c.get("type") == "heading"]
        has_deps = "🔗 Dependencies" in headings
        has_size = "📏 Size Estimate" in headings
        
        status = "✓" if (has_deps and has_size and points) else "⚠"
        print(f"\n{status} {ticket}: {assignee_name} | {points} pts")
        print(f"   Dependencies: {'YES' if has_deps else 'NO'} | Size: {'YES' if has_size else 'NO'}")
        print(f"   Sections: {len(content)}")

print("\n" + "=" * 80)
