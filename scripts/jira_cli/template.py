"""Ticket body template — matches jira/TICKET_TEMPLATE.md exactly. Enforces marker prefix."""

from __future__ import annotations

import re

from scripts.jira_cli.errors import TemplateError, UsageError

TEMPLATE_MARKER = "📝 Description"
SUMMARY_MAX_LEN = 72
EPIC_KEY_PATTERN = re.compile(r"^BH-\d+$")


def validate_epic_key(key: str) -> None:
    if not EPIC_KEY_PATTERN.match(key):
        raise UsageError(f"epic key must match BH-<digits>, got: {key!r}")


def validate_summary(summary: str) -> None:
    if "\n" in summary or "\r" in summary:
        raise UsageError("summary must be a single line — newlines forbidden")
    if not summary.strip():
        raise UsageError("summary cannot be empty")
    if len(summary) > SUMMARY_MAX_LEN:
        raise UsageError(f"summary too long ({len(summary)} > {SUMMARY_MAX_LEN}): {summary!r}")


def enforce_template_marker(description: str) -> None:
    """Raise TemplateError unless the body starts with the canonical marker."""
    if not description.lstrip().startswith(TEMPLATE_MARKER):
        raise TemplateError(
            f"description must start with {TEMPLATE_MARKER!r} — see jira/TICKET_TEMPLATE.md"
        )


def render_task_body(
    *,
    description: str,
    scope_in: list[str] | None = None,
    scope_out: list[str] | None = None,
    areas: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    technical_notes: str = "",
    business_notes: str = "",
    related: list[str] | None = None,
    contact: str = "",
) -> str:
    """Render a ticket body in the canonical TICKET_TEMPLATE.md shape."""
    parts: list[str] = [f"{TEMPLATE_MARKER}\n\n{description.strip()}\n"]

    if scope_in or scope_out:
        scope_block = ["📍 Scope\n"]
        if scope_in:
            scope_block.append("Include:")
            scope_block.extend(f"- {item}" for item in scope_in)
        if scope_out:
            scope_block.append("\nExclude:" if scope_in else "Exclude:")
            scope_block.extend(f"- {item}" for item in scope_out)
        parts.append("\n".join(scope_block) + "\n")

    if areas:
        parts.append("🏗️ Areas\n\n" + "\n".join(f"- {area}" for area in areas) + "\n")

    if acceptance_criteria:
        parts.append(
            "✅ Acceptance Criteria\n\n"
            + "\n".join(f"- [ ] {item}" for item in acceptance_criteria)
            + "\n"
        )

    if contact:
        parts.append(f"👥 Contact\n\n{contact}\n")

    if technical_notes:
        parts.append(f"🔧 Technical Notes\n\n{technical_notes.strip()}\n")

    if business_notes:
        parts.append(f"💼 Business Notes\n\n{business_notes.strip()}\n")

    if related:
        parts.append("🔗 Related Issues\n\n" + "\n".join(f"- {item}" for item in related) + "\n")

    body = "\n".join(parts)
    enforce_template_marker(body)
    return body


SKELETON = f"""{TEMPLATE_MARKER}

<replace this with what needs to be done and why; 2-4 sentences>

📍 Scope

Include:
- <add at least one>

Exclude:
- <add at least one, or delete this section>

🏗️ Areas

<keep only the ones that apply; delete the rest>
- BrightAgent
- Webapp
- Platform Core
- Slack Server
- CDK
- Infra

✅ Acceptance Criteria

- [ ] <replace with measurable criterion 1>
- [ ] <add more as needed>

🔧 Technical Notes

<file paths, function names, hints — or delete if obvious>

🔗 Related Issues

- <blocks BH-XXX / blocked by BH-YYY — or delete>
"""


def is_unedited_skeleton(body: str) -> bool:
    """True if the body still contains the literal placeholder markers `<...>`."""
    return "<replace" in body or "<add" in body or "<file paths" in body
