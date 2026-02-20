"""Atlassian Document Format (ADF) builder utilities.

Pure functional builders for creating structured ADF documents.
"""

from typing import Any


def text(content: str) -> dict[str, Any]:
    """Create ADF text node.

    Args:
        content: Text content

    Returns:
        ADF text node
    """
    return {"type": "text", "text": content}


def bold(content: str) -> dict[str, Any]:
    """Create ADF bold text node.

    Args:
        content: Text content

    Returns:
        ADF bold text node
    """
    return {
        "type": "text",
        "text": content,
        "marks": [{"type": "strong"}],
    }


def code(content: str) -> dict[str, Any]:
    """Create ADF inline code node.

    Args:
        content: Code content

    Returns:
        ADF code node
    """
    return {
        "type": "text",
        "text": content,
        "marks": [{"type": "code"}],
    }


def paragraph(*nodes: dict[str, Any] | str) -> dict[str, Any]:
    """Create ADF paragraph node.

    Args:
        nodes: Text nodes or strings

    Returns:
        ADF paragraph node
    """
    content = []
    for node in nodes:
        if isinstance(node, str):
            content.append(text(node))
        else:
            content.append(node)

    return {"type": "paragraph", "content": content}


def heading(content: str, level: int = 3) -> dict[str, Any]:
    """Create ADF heading node.

    Args:
        content: Heading text
        level: Heading level (1-6)

    Returns:
        ADF heading node
    """
    if not 1 <= level <= 6:
        raise ValueError(f"Heading level must be 1-6, got {level}")

    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [text(content)],
    }


def bullet_list(items: list[str] | list[dict[str, Any]]) -> dict[str, Any]:
    """Create ADF bullet list.

    Args:
        items: List of strings or paragraph nodes

    Returns:
        ADF bullet list node
    """
    list_items = []
    for item in items:
        if isinstance(item, str):
            list_items.append({
                "type": "listItem",
                "content": [paragraph(item)],
            })
        else:
            list_items.append({
                "type": "listItem",
                "content": [item],
            })

    return {"type": "bulletList", "content": list_items}


def ordered_list(items: list[str] | list[dict[str, Any]]) -> dict[str, Any]:
    """Create ADF ordered list.

    Args:
        items: List of strings or paragraph nodes

    Returns:
        ADF ordered list node
    """
    list_items = []
    for item in items:
        if isinstance(item, str):
            list_items.append({
                "type": "listItem",
                "content": [paragraph(item)],
            })
        else:
            list_items.append({
                "type": "listItem",
                "content": [item],
            })

    return {"type": "orderedList", "content": list_items}


def code_block(content: str, language: str = "python") -> dict[str, Any]:
    """Create ADF code block.

    Args:
        content: Code content
        language: Programming language

    Returns:
        ADF code block node
    """
    return {
        "type": "codeBlock",
        "attrs": {"language": language},
        "content": [text(content)],
    }


def document(*nodes: dict[str, Any]) -> dict[str, Any]:
    """Create ADF document.

    Args:
        nodes: Content nodes

    Returns:
        Complete ADF document
    """
    return {
        "version": 1,
        "type": "doc",
        "content": list(nodes),
    }


def section(
    title: str,
    *content_nodes: dict[str, Any],
    level: int = 3,
) -> list[dict[str, Any]]:
    """Create section with heading and content.

    Args:
        title: Section title
        content_nodes: Content nodes
        level: Heading level

    Returns:
        List of nodes (heading + content)
    """
    return [heading(title, level), *content_nodes]


def ticket_description(
    description: str,
    issue_type: str,
    scope_include: list[str],
    scope_exclude: list[str],
    areas: list[str],
    acceptance_criteria: list[str],
    owner: str,
    stakeholders: list[str],
    technical_notes: str,
    business_notes: str,
    priority: str,
    milestone: str,
) -> dict[str, Any]:
    """Create standard ticket description document.

    Args:
        description: Main description text
        issue_type: Type of issue
        scope_include: Items included in scope
        scope_exclude: Items excluded from scope
        areas: Areas affected
        acceptance_criteria: Acceptance criteria list
        owner: Issue owner
        stakeholders: List of stakeholders
        technical_notes: Technical notes
        business_notes: Business notes
        priority: Priority level
        milestone: Milestone name

    Returns:
        Complete ADF document
    """
    content = [
        *section("📝 Description", paragraph(description)),
        paragraph(""),
        *section("🎯 Type of Issue", paragraph(issue_type)),
        paragraph(""),
        *section(
            "📍 Scope",
            paragraph(bold("Include:")),
            bullet_list(scope_include),
            paragraph(bold("Exclude:")),
            bullet_list(scope_exclude),
        ),
        paragraph(""),
        *section("🏗️ Areas", bullet_list(areas)),
        paragraph(""),
        *section("✅ Acceptance Criteria", bullet_list(acceptance_criteria)),
        paragraph(""),
        *section(
            "👥 Contact",
            paragraph(bold(f"Owner: {owner}")),
            paragraph(bold(f"Stakeholders: {', '.join(stakeholders)}")),
        ),
        paragraph(""),
        *section("🔧 Technical Notes", paragraph(technical_notes)),
        paragraph(""),
        *section("💼 Business Notes", paragraph(business_notes)),
        paragraph(""),
        *section(
            "📊 Priority & Timeline",
            paragraph(bold(f"Priority: {priority}")),
        ),
        paragraph(""),
        *section("📅 Milestone", paragraph(milestone)),
    ]

    return document(*content)
