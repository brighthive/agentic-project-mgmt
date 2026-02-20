#!/usr/bin/env python3
"""Assign Sprint 1 tickets to team members.

REFACTORED VERSION - Uses jira_lib for clean, composable operations.

Before: 237 lines with duplicated functions
After: ~80 lines using reusable library
"""

from dataclasses import dataclass

from jira_lib import (
    JiraConfig,
    JiraError,
    User,
    assign_issue,
    get_user_by_email_with_fallbacks,
    load_config,
    verify_assignment,
)


@dataclass(frozen=True)
class TeamMember:
    """Team member with email fallbacks and ticket assignments."""

    name: str
    emails: list[str]
    tickets: list[str]


def get_team_members() -> list[TeamMember]:
    """Define team members and their assignments.

    Pure function returning immutable data structure.
    """
    return [
        TeamMember(
            name="Marwan",
            emails=["marwan.samih@brighthive.io", "marwan@brighthive.io"],
            tickets=[
                "BH-150", "BH-151", "BH-152", "BH-159", "BH-162",
                "BH-174", "BH-175", "BH-176", "BH-177", "BH-178",
                "BH-179", "BH-180", "BH-181", "BH-182",
                "BH-199",
            ],
        ),
        TeamMember(
            name="Ahmed",
            emails=[
                "ahmed.sherbiny@brighthive.io",
                "ahmed.elsherbiny@brighthive.io",
                "ahmed@brighthive.io",
            ],
            tickets=[
                "BH-183", "BH-184", "BH-185", "BH-186", "BH-187",
                "BH-188", "BH-189", "BH-190", "BH-191", "BH-192",
                "BH-193", "BH-195", "BH-160", "BH-194", "BH-200",
            ],
        ),
        TeamMember(
            name="Hikuri",
            emails=["kuri@brighthive.io", "hikuri@brighthive.io", "bado@brighthive.io"],
            tickets=[
                "BH-153", "BH-154", "BH-155", "BH-161", "BH-163",
                "BH-165", "BH-166", "BH-197", "BH-198",
            ],
        ),
    ]


def assign_team_tickets(
    config: JiraConfig,
    member: TeamMember,
    user: User,
) -> tuple[int, int]:
    """Assign all tickets for a team member.

    Args:
        config: Jira configuration
        member: Team member info
        user: Resolved Jira user

    Returns:
        Tuple of (success_count, total_count)
    """
    success_count = 0

    for ticket in member.tickets:
        success, error = assign_issue(config, ticket, user)
        if success:
            print(f"  ✅ {ticket} → {member.name}")
            success_count += 1
        else:
            print(f"  ❌ {ticket} failed: {error}")

    return (success_count, len(member.tickets))


def verify_team_assignments(
    config: JiraConfig,
    member: TeamMember,
    user: User,
) -> int:
    """Verify all assignments for a team member.

    Args:
        config: Jira configuration
        member: Team member info
        user: Expected Jira user

    Returns:
        Number of correctly assigned tickets
    """
    verified_count = 0

    for ticket in member.tickets:
        is_correct, error = verify_assignment(config, ticket, user)
        if error:
            print(f"  ❌ {ticket}: {error}")
        elif is_correct:
            verified_count += 1
        else:
            print(f"  ⚠️  {ticket}: Incorrect assignment")

    return verified_count


def main() -> None:
    """Main execution."""
    config = load_config()
    team_members = get_team_members()

    print("=" * 60)
    print("🔧 ASSIGNING SPRINT 1 TICKETS")
    print("=" * 60)
    print()

    # Step 1: Resolve all team members
    print("📋 Step 1: Looking up team members...")
    print()

    resolved_members: list[tuple[TeamMember, User]] = []

    for member in team_members:
        user, error = get_user_by_email_with_fallbacks(config, member.emails)
        if error:
            print(f"  ❌ {member.name}: {error}")
            continue

        print(f"  ✅ Found {member.name}: {user.display_name}")
        resolved_members.append((member, user))

    print()

    if len(resolved_members) != len(team_members):
        print("❌ FAILED: Could not resolve all team members")
        return

    # Step 2: Assign tickets
    print("=" * 60)
    print("📝 Step 2: Assigning tickets...")
    print("=" * 60)
    print()

    total_success = 0
    total_tickets = 0

    for member, user in resolved_members:
        print(f"👤 {member.name} ({len(member.tickets)} tickets):")
        success, total = assign_team_tickets(config, member, user)
        total_success += success
        total_tickets += total
        print(f"  Result: {success}/{total} assigned")
        print()

    # Step 3: Verify assignments
    print("=" * 60)
    print("✅ Step 3: Verifying assignments...")
    print("=" * 60)
    print()

    total_verified = 0

    for member, user in resolved_members:
        print(f"👤 Verifying {member.name}'s tickets:")
        verified = verify_team_assignments(config, member, user)
        total_verified += verified
        print()

    # Final summary
    print("=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    print()
    print(f"Assignments Attempted: {total_success}/{total_tickets} ({total_success*100//total_tickets}%)")
    print(f"Assignments Verified:  {total_verified}/{total_tickets} ({total_verified*100//total_tickets}%)")
    print()

    if total_verified == total_tickets:
        print("✅ SUCCESS: All tickets assigned correctly!")
    else:
        print("⚠️  WARNING: Some tickets failed to assign")
        print("Rerun this script or manually assign failed tickets in Jira UI")

    print()
    print("🔗 View Sprint Board:")
    print("   https://brighthiveio.atlassian.net/jira/software/projects/BH/boards/152")


if __name__ == "__main__":
    main()
