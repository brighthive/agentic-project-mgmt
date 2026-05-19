"""Contract tests for JiraClient — uses httpx.MockTransport for DI (no patch())."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from scripts.jira_cli.client import JiraClient, build_http_client
from scripts.jira_cli.config import JiraConfig, load_config_from_env
from scripts.jira_cli.errors import (
    AuthError,
    EpicNotFoundError,
    JiraAPIError,
    TemplateError,
    UsageError,
)
from scripts.jira_cli.template import (
    TEMPLATE_MARKER,
    enforce_template_marker,
    render_task_body,
    validate_summary,
)

TEST_BASE = "https://brighthiveio.atlassian.net"
SECRET_TOKEN = "secret-deadbeef-must-not-leak"


def _config() -> JiraConfig:
    return JiraConfig(base_url=TEST_BASE, user="kuri@brighthive.io", token=SECRET_TOKEN)


def _client_with_handler(handler: httpx.MockTransport) -> JiraClient:
    config = _config()
    http = build_http_client(config=config, transport=handler)
    return JiraClient(config=config, http=http)


def _open_epic(key: str = "BH-260", summary: str = "Test epic") -> dict[str, Any]:
    return {"key": key, "name": summary, "done": False}


def _valid_body() -> str:
    return render_task_body(
        description="A test ticket.",
        scope_in=["Do X"],
        scope_out=["Don't do Y"],
        acceptance_criteria=["X works"],
    )


# ── Invariant 6 / Property 3: template marker is the gate ────────────────────


def test_template_marker_present_in_rendered_body() -> None:
    body = _valid_body()
    assert body.startswith(TEMPLATE_MARKER)


def test_template_marker_missing_is_rejected() -> None:
    with pytest.raises(TemplateError):
        enforce_template_marker("hello world, no marker here")


def test_create_refuses_to_post_when_marker_missing() -> None:
    """Property 3: API is not called IFF marker is absent."""
    posts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/board/152/epic"):
            return httpx.Response(200, json={"values": [_open_epic("BH-260")]})
        if request.method == "POST":
            posts.append(request.url.path)
            return httpx.Response(201, json={"key": "BH-9001"})
        return httpx.Response(404)

    client = _client_with_handler(httpx.MockTransport(handler))
    with pytest.raises(TemplateError):
        client.create_task(
            epic_key="BH-260", summary="x", description="no marker here at all"
        )
    assert posts == []


# ── Invariants 1, 8: forbidden types + parent shape ──────────────────────────


def test_story_issue_type_is_forbidden() -> None:
    client = _client_with_handler(httpx.MockTransport(lambda req: httpx.Response(200)))
    with pytest.raises(UsageError, match="forbidden"):
        client.create_task(
            epic_key="BH-260",
            summary="x",
            description=_valid_body(),
            issue_type="Story",
        )


def test_create_task_sends_parent_field_not_customfield_10014() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/board/152/epic"):
            return httpx.Response(200, json={"values": [_open_epic("BH-260")]})
        if request.method == "POST" and "/rest/api/3/issue" in request.url.path:
            captured["body"] = json.loads(request.content.decode())
            return httpx.Response(201, json={"key": "BH-9001"})
        return httpx.Response(404)

    client = _client_with_handler(httpx.MockTransport(handler))
    issue = client.create_task(
        epic_key="BH-260", summary="feat(x): test", description=_valid_body()
    )

    assert issue.key == "BH-9001"
    fields = captured["body"]["fields"]
    assert fields["issuetype"] == {"name": "Task"}
    assert fields["parent"] == {"key": "BH-260"}
    assert fields["project"] == {"key": "BH"}
    assert "customfield_10014" not in fields


# ── Invariant 4: live epic check before create ───────────────────────────────


def test_unknown_epic_raises_before_create_call() -> None:
    create_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal create_calls
        if request.url.path.endswith("/board/152/epic"):
            return httpx.Response(200, json={"values": [_open_epic("BH-260")]})
        if request.method == "POST":
            create_calls += 1
            return httpx.Response(201, json={"key": "BH-9001"})
        return httpx.Response(404)

    client = _client_with_handler(httpx.MockTransport(handler))
    with pytest.raises(EpicNotFoundError, match="BH-999"):
        client.create_task(epic_key="BH-999", summary="x", description=_valid_body())
    assert create_calls == 0


def test_empty_epic_list_raises() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"values": []})

    client = _client_with_handler(httpx.MockTransport(handler))
    with pytest.raises(EpicNotFoundError):
        client.create_task(epic_key="BH-260", summary="x", description=_valid_body())


# ── Invariant 5: summary constraints ─────────────────────────────────────────


def test_summary_with_newline_rejected() -> None:
    with pytest.raises(UsageError, match="single line"):
        validate_summary("first line\nsecond line")


def test_summary_too_long_rejected() -> None:
    with pytest.raises(UsageError, match="too long"):
        validate_summary("x" * 73)


def test_summary_at_max_length_accepted() -> None:
    validate_summary("x" * 72)


# ── Invariant 7: Basic auth header is sent ───────────────────────────────────


def test_authorization_header_is_basic_auth() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json={"accountId": "abc", "displayName": "Kuri"})

    config = _config()
    http = build_http_client(config=config, transport=httpx.MockTransport(handler))
    client = JiraClient(config=config, http=http)
    user = client.whoami()
    assert user.account_id == "abc"
    assert seen["auth"].startswith("Basic ")


# ── Invariant 11 / Property 2: token never appears in error output ───────────


def test_500_error_scrubs_token_from_response_text() -> None:
    """Even if upstream echoes the token, JiraAPIError repr must not contain it."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500, text=f"server boom — Authorization: Basic {SECRET_TOKEN} just-kidding"
        )

    client = _client_with_handler(httpx.MockTransport(handler))
    with pytest.raises(JiraAPIError) as exc:
        client.whoami()
    assert SECRET_TOKEN not in str(exc.value)
    assert SECRET_TOKEN not in repr(exc.value)


def test_401_raises_auth_error_without_token() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    client = _client_with_handler(httpx.MockTransport(handler))
    with pytest.raises(AuthError) as exc:
        client.whoami()
    assert SECRET_TOKEN not in str(exc.value)
    assert "id.atlassian.com" in str(exc.value)


# ── Config loading ───────────────────────────────────────────────────────────


def test_missing_env_var_raises_auth_error_naming_var() -> None:
    with pytest.raises(AuthError, match="JIRA_TOKEN"):
        load_config_from_env(env={"JIRA_USER": "u", "JIRA_BASE": "https://x"})


def test_non_https_base_url_rejected() -> None:
    with pytest.raises(AuthError, match="https://"):
        load_config_from_env(
            env={"JIRA_USER": "u", "JIRA_TOKEN": "t", "JIRA_BASE": "http://insecure"}
        )


def test_board_id_must_be_integer() -> None:
    with pytest.raises(AuthError, match="JIRA_BOARD_ID"):
        load_config_from_env(
            env={
                "JIRA_USER": "u",
                "JIRA_TOKEN": "t",
                "JIRA_BASE": "https://x",
                "JIRA_BOARD_ID": "not-a-number",
            }
        )


def test_base_url_trailing_slash_stripped() -> None:
    config = load_config_from_env(
        env={"JIRA_USER": "u", "JIRA_TOKEN": "t", "JIRA_BASE": "https://x/"}
    )
    assert config.base_url == "https://x"


# ── Transitions ──────────────────────────────────────────────────────────────


def test_transition_picks_matching_to_status() -> None:
    posted: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and "/transitions" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "transitions": [
                        {"id": "11", "name": "Start", "to": {"name": "In Progress"}},
                        {"id": "21", "name": "Done", "to": {"name": "Done"}},
                    ]
                },
            )
        if request.method == "POST" and "/transitions" in request.url.path:
            posted["body"] = json.loads(request.content.decode())
            return httpx.Response(204)
        return httpx.Response(404)

    client = _client_with_handler(httpx.MockTransport(handler))
    result = client.transition("BH-12345", to_state="In Progress")
    assert result.transition_id == "11"
    assert posted["body"] == {"transition": {"id": "11"}}


def test_transition_to_unknown_state_raises() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"transitions": []})

    client = _client_with_handler(httpx.MockTransport(handler))
    with pytest.raises(UsageError, match="no transition"):
        client.transition("BH-12345", to_state="Nowhere")


# ── ADF rendering of bullet lists ────────────────────────────────────────────


def test_adf_renders_bullet_list_from_dashes() -> None:
    from scripts.jira_cli.adf import text_to_adf

    doc = text_to_adf(f"{TEMPLATE_MARKER}\n\nIntro paragraph.\n\n- item one\n- item two")
    types = [node["type"] for node in doc["content"]]
    assert "bulletList" in types
    bullet = next(n for n in doc["content"] if n["type"] == "bulletList")
    assert len(bullet["content"]) == 2
