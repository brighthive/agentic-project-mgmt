"""Tests for ADF builder module.

Pure function tests - no I/O or mocking needed.
"""

import pytest

from jira_lib.adf_builder import (
    bold,
    bullet_list,
    code,
    code_block,
    document,
    heading,
    ordered_list,
    paragraph,
    section,
    text,
)


def test_text() -> None:
    """Test text node creation."""
    node = text("Hello, World!")

    assert node == {
        "type": "text",
        "text": "Hello, World!",
    }


def test_bold() -> None:
    """Test bold text node creation."""
    node = bold("Important")

    assert node == {
        "type": "text",
        "text": "Important",
        "marks": [{"type": "strong"}],
    }


def test_code() -> None:
    """Test inline code node creation."""
    node = code("print('hello')")

    assert node == {
        "type": "text",
        "text": "print('hello')",
        "marks": [{"type": "code"}],
    }


def test_paragraph_with_string() -> None:
    """Test paragraph with single string."""
    node = paragraph("Simple paragraph")

    assert node == {
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "Simple paragraph"}
        ],
    }


def test_paragraph_with_nodes() -> None:
    """Test paragraph with mixed nodes."""
    node = paragraph(
        "This is ",
        bold("important"),
        " text with ",
        code("code"),
    )

    assert node["type"] == "paragraph"
    assert len(node["content"]) == 4
    assert node["content"][0]["text"] == "This is "
    assert node["content"][1]["text"] == "important"
    assert node["content"][1]["marks"] == [{"type": "strong"}]


def test_heading() -> None:
    """Test heading node creation."""
    node = heading("Section Title", level=2)

    assert node == {
        "type": "heading",
        "attrs": {"level": 2},
        "content": [{"type": "text", "text": "Section Title"}],
    }


def test_heading_default_level() -> None:
    """Test heading with default level 3."""
    node = heading("Title")

    assert node["attrs"]["level"] == 3


def test_heading_invalid_level() -> None:
    """Test heading with invalid level."""
    with pytest.raises(ValueError, match="Heading level must be 1-6"):
        heading("Title", level=7)

    with pytest.raises(ValueError, match="Heading level must be 1-6"):
        heading("Title", level=0)


def test_bullet_list_with_strings() -> None:
    """Test bullet list with string items."""
    node = bullet_list([
        "First item",
        "Second item",
        "Third item",
    ])

    assert node["type"] == "bulletList"
    assert len(node["content"]) == 3
    assert node["content"][0]["type"] == "listItem"
    assert node["content"][0]["content"][0]["type"] == "paragraph"


def test_ordered_list_with_strings() -> None:
    """Test ordered list with string items."""
    node = ordered_list([
        "Step 1",
        "Step 2",
        "Step 3",
    ])

    assert node["type"] == "orderedList"
    assert len(node["content"]) == 3


def test_code_block() -> None:
    """Test code block creation."""
    code = 'def hello():\n    print("Hello, World!")'
    node = code_block(code, language="python")

    assert node == {
        "type": "codeBlock",
        "attrs": {"language": "python"},
        "content": [{"type": "text", "text": code}],
    }


def test_code_block_default_language() -> None:
    """Test code block with default language."""
    node = code_block("print('test')")

    assert node["attrs"]["language"] == "python"


def test_document() -> None:
    """Test document creation."""
    doc = document(
        heading("Title"),
        paragraph("Content"),
    )

    assert doc["version"] == 1
    assert doc["type"] == "doc"
    assert len(doc["content"]) == 2
    assert doc["content"][0]["type"] == "heading"
    assert doc["content"][1]["type"] == "paragraph"


def test_section() -> None:
    """Test section helper."""
    nodes = section(
        "Section Title",
        paragraph("First paragraph"),
        paragraph("Second paragraph"),
        level=2,
    )

    assert len(nodes) == 3
    assert nodes[0]["type"] == "heading"
    assert nodes[0]["attrs"]["level"] == 2
    assert nodes[1]["type"] == "paragraph"
    assert nodes[2]["type"] == "paragraph"


def test_complex_document() -> None:
    """Test complex document composition."""
    doc = document(
        heading("Overview", level=1),
        paragraph("This is an overview"),
        heading("Requirements", level=2),
        bullet_list([
            "Must be fast",
            "Must be reliable",
            "Must be secure",
        ]),
        heading("Implementation", level=2),
        paragraph("Here's how we do it:"),
        code_block("def implement():\n    pass", language="python"),
    )

    assert doc["version"] == 1
    assert doc["type"] == "doc"
    assert len(doc["content"]) == 7

    # Verify structure
    content = doc["content"]
    assert content[0]["type"] == "heading"
    assert content[1]["type"] == "paragraph"
    assert content[2]["type"] == "heading"
    assert content[3]["type"] == "bulletList"
    assert content[4]["type"] == "heading"
    assert content[5]["type"] == "paragraph"
    assert content[6]["type"] == "codeBlock"
