"""Minimal plain-text → ADF converter for Jira REST v3 issue descriptions.

Atlassian Document Format expects a structured JSON tree. For our template
bodies — plain paragraphs separated by blank lines, no inline formatting —
this single-paragraph-per-blank-line conversion is sufficient. If we need
real markdown rendering later, swap for `atlassian-python-api` or a proper
markdown→ADF lib.
"""

from __future__ import annotations

from typing import Any


def _is_bullet(line: str) -> bool:
    return line.lstrip().startswith("- ") or line.lstrip() in ("-", "*")


def _bullet_text(line: str) -> tuple[str, bool]:
    """Return (text, is_checkbox)."""
    stripped = line.lstrip()[2:]  # drop "- "
    if stripped.startswith("[ ]") or stripped.startswith("[x]") or stripped.startswith("[X]"):
        return stripped[3:].lstrip(), True
    return stripped, False


def _para(text: str) -> dict[str, Any]:
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


def _bullet_list(items: list[str]) -> dict[str, Any]:
    return {
        "type": "bulletList",
        "content": [
            {"type": "listItem", "content": [_para(item)]} for item in items
        ],
    }


def text_to_adf(text: str) -> dict[str, Any]:
    """Convert template-shaped text to ADF v1 — handles paragraphs + `- ` bullet lists."""
    content: list[dict[str, Any]] = []
    for block in text.split("\n\n"):
        block = block.strip("\n")
        if not block.strip():
            continue
        lines = block.split("\n")
        if all(_is_bullet(line) or not line.strip() for line in lines if line.strip()):
            items = [_bullet_text(line)[0] for line in lines if line.strip()]
            content.append(_bullet_list(items))
            continue
        # Mixed: emit prose lines as one paragraph, bullet runs as lists
        buffer: list[str] = []
        for line in lines:
            if _is_bullet(line):
                if buffer:
                    content.append(_para("\n".join(buffer)))
                    buffer = []
                # collect consecutive bullets
                content.append(_bullet_list([_bullet_text(line)[0]]))
            else:
                buffer.append(line)
        if buffer:
            content.append(_para("\n".join(buffer)))
    return {"type": "doc", "version": 1, "content": content}
