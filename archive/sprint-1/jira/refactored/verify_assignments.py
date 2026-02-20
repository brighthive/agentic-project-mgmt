#!/usr/bin/env python3
"""Verify all Sprint 1 ticket assignments.

REFACTORED VERSION - Clean and functional.

Before: 95 lines with hardcoded ticket lists and manual API calls
After: ~50 lines using composable operations
"""

from jira_lib import JiraConfig, get_issue, load_config


def get_all_sprint_tickets() -> dict[str, list[str]]:
    """Define all Sprint 1 ticket assignments.

    Pure function returning immutable mapping.
    """
    return {
        "Marwan": [
            "BH-150", "BH-151", "BH-152", "BH-156", "BH-157", "BH-159", "BH-162",
            "BH-167", "BH-168", "BH-169",
            "BH-174", "BH-175", "BH-176", "BH-177", "BH-178", "BH-179", "BH-180",
            "BH-181", "BH-182",
            "BH-199",
        ],
        "Ahmed": [
            "BH-160", "BH-164",
            "BH-183", "BH-184", "BH-185", "BH-186", "BH-187", "BH-188", "BH-189",
            "BH-190", "BH-191", "BH-192", "BH-193", "BH-195",
            "BH-194", "BH-200",
        ],
        "Hikuri": [
            "BH-153", "BH-154", "BH-155", "BH-158", "BH-161", "BH-163", "BH-165",
            "BH-166",
            "BH-197", "BH-198",
        ],
    }


def verify_ticket(
    config: JiraConfig,
    ticket_key: str,
    expected_name: str,
) -> tuple[bool, str]:
    """Verify single ticket assignment.

    Args:
        config: Jira configuration
        ticket_key: Ticket to verify
        expected_name: Expected assignee name

    Returns:
        Tuple of (is_correct, status_message)
    """
    issue, error = get_issue(config, ticket_key)

    if error:
        return (False, f"❌ {ticket_key}: API ERROR - {error}")

    if not issue.assignee:
        return (False, f"❌ {ticket_key}: UNASSIGNED - {issue.status.value}")

    if expected_name.lower() in issue.assignee.display_name.lower():
        return (True, f"✅ {ticket_key}: {issue.assignee.display_name} - {issue.status.value}")

    return (
        False,
        f"⚠️  {ticket_key}: Expected '{expected_name}', got '{issue.assignee.display_name}' - {issue.status.value}",
    )


def main() -> None:
    """Main execution."""
    config = load_config()
    assignments = get_all_sprint_tickets()

    print("🔍 Direct Jira API Verification of All Sprint 1 Assignments:")
    print("=" * 70)
    print()

    results = {name: [] for name in assignments.keys()}
    results["unassigned"] = []

    for expected_name, tickets in assignments.items():
        print(f"👤 {expected_name} ({len(tickets)} tickets):")
        for ticket in tickets:
            is_correct, message = verify_ticket(config, ticket, expected_name)
            print(f"  {message}")

            if is_correct:
                results[expected_name].append(ticket)
            else:
                results["unassigned"].append(ticket)

        print()

    # Summary
    print("=" * 70)
    print("📊 SUMMARY:")
    print("=" * 70)

    total_tickets = sum(len(tickets) for tickets in assignments.values())
    total_assigned = sum(len(results[name]) for name in assignments.keys())

    for name, tickets in assignments.items():
        expected_count = len(tickets)
        actual_count = len(results[name])
        print(f"{name:8} {actual_count}/{expected_count} assigned")

    print(f"Unassigned: {len(results['unassigned'])}/{total_tickets}")
    print()
    print(f"TOTAL:      {total_assigned}/{total_tickets} successfully assigned ({total_assigned*100//total_tickets}%)")

    if results["unassigned"]:
        print()
        print("⚠️  UNASSIGNED/INCORRECT TICKETS:")
        for ticket in results["unassigned"]:
            print(f"  - {ticket}")


if __name__ == "__main__":
    main()
