"""CLI-surface tests — argparse wiring + exit-code mapping + end-to-end with stub client."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

import httpx
import pytest

from scripts.jira_cli.__main__ import build_parser, main
from scripts.jira_cli.client import JiraClient, build_http_client
from scripts.jira_cli.config import JiraConfig
from scripts.jira_cli.errors import JiraCLIError, UsageError
from scripts.jira_cli.template import TEMPLATE_MARKER

SECRET_TOKEN = "tok-secret-keep-out"


def _stub_factory(handler: httpx.MockTransport):
    def _factory() -> JiraClient:
        config = JiraConfig(base_url="https://x.atlassian.net", user="u@x", token=SECRET_TOKEN)
        http = build_http_client(config=config, transport=handler)
        return JiraClient(config=config, http=http)

    return _factory


def test_parser_create_requires_subcommand() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_parser_accepts_create_with_required_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["create", "--epic", "BH-260", "--title", "feat(x): test", "--body", "ignored"]
    )
    assert args.command == "create"
    assert args.epic == "BH-260"
    assert args.title == "feat(x): test"


def test_main_returns_exit_code_4_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JIRA_USER", raising=False)
    monkeypatch.delenv("JIRA_TOKEN", raising=False)
    monkeypatch.delenv("JIRA_BASE", raising=False)
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        code = main(["whoami"])
    assert code == 4
    assert "not set" in stderr.getvalue()


def test_main_exits_2_on_story_type() -> None:
    stderr = io.StringIO()
    body = f"{TEMPLATE_MARKER}\n\nbody"
    with redirect_stderr(stderr):
        code = main(
            ["create", "--epic", "BH-260", "--title", "x", "--type", "Story", "--body", body],
            factory=_stub_factory(httpx.MockTransport(lambda req: httpx.Response(200))),
        )
    assert code == 2


def test_main_exits_2_on_missing_epic() -> None:
    stderr = io.StringIO()
    body = f"{TEMPLATE_MARKER}\n\nbody"
    with redirect_stderr(stderr):
        code = main(
            ["create", "--title", "x", "--body", body],
            factory=_stub_factory(httpx.MockTransport(lambda req: httpx.Response(200))),
        )
    assert code == 2
    assert "--epic" in stderr.getvalue()


def test_main_create_happy_path_returns_key_and_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/board/152/epic"):
            return httpx.Response(
                200, json={"values": [{"key": "BH-260", "name": "Epic", "done": False}]}
            )
        if request.method == "POST" and "/rest/api/3/issue" in request.url.path:
            return httpx.Response(201, json={"key": "BH-9999"})
        return httpx.Response(404)

    stdout = io.StringIO()
    body = f"{TEMPLATE_MARKER}\n\nA real body."
    with redirect_stdout(stdout):
        code = main(
            ["create", "--epic", "BH-260", "--title", "feat(x): test", "--body", body],
            factory=_stub_factory(httpx.MockTransport(handler)),
        )
    assert code == 0
    out = stdout.getvalue()
    assert "BH-9999" in out
    assert "/browse/BH-9999" in out


def test_main_exits_3_on_unknown_epic() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"values": []})

    stderr = io.StringIO()
    body = f"{TEMPLATE_MARKER}\n\nbody"
    with redirect_stderr(stderr):
        code = main(
            ["create", "--epic", "BH-999", "--title", "x", "--body", body],
            factory=_stub_factory(httpx.MockTransport(handler)),
        )
    assert code == 3
    assert "BH-999" in stderr.getvalue()


def test_main_my_command_renders_table() -> None:
    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "issues": [
                    {
                        "key": "BH-12",
                        "fields": {
                            "summary": "Test",
                            "status": {"name": "To Do"},
                            "issuetype": {"name": "Task"},
                            "parent": {"key": "BH-260"},
                            "assignee": {"displayName": "Kuri"},
                            "customfield_10016": 3,
                        },
                    }
                ]
            },
        )

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(["my"], factory=_stub_factory(httpx.MockTransport(handler)))
    assert code == 0
    out = stdout.getvalue()
    assert out.startswith("KEY\tSTATUS\tPOINTS\tSUMMARY")
    assert "BH-12" in out


def test_main_transition_prints_arrow() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "transitions": [
                        {"id": "11", "name": "Start", "to": {"name": "In Progress"}}
                    ]
                },
            )
        return httpx.Response(204)

    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = main(
            ["transition", "BH-12345", "In Progress"],
            factory=_stub_factory(httpx.MockTransport(handler)),
        )
    assert code == 0
    assert "BH-12345 -> In Progress" in stdout.getvalue()


def test_claudecode_hint_emitted_but_command_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDECODE", "1")

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"accountId": "a", "displayName": "n", "emailAddress": "e"})

    stderr = io.StringIO()
    stdout = io.StringIO()
    with redirect_stderr(stderr), redirect_stdout(stdout):
        code = main(["whoami"], factory=_stub_factory(httpx.MockTransport(handler)))
    assert code == 0
    assert "/create-jira-ticket" in stderr.getvalue()


def test_token_not_in_stderr_across_main_paths() -> None:
    """Property 2 end-to-end: SECRET_TOKEN bytes appear nowhere in stderr/stdout."""

    def handler(_req: httpx.Request) -> httpx.Response:
        # Server echoes token in body to simulate proxy misconfiguration
        return httpx.Response(500, text=f"oops authorization basic {SECRET_TOKEN} oops")

    stderr = io.StringIO()
    stdout = io.StringIO()
    with redirect_stderr(stderr), redirect_stdout(stdout):
        code = main(["whoami"], factory=_stub_factory(httpx.MockTransport(handler)))
    assert code == 5
    combined = stderr.getvalue() + stdout.getvalue()
    assert SECRET_TOKEN not in combined


def test_unedited_skeleton_rejected_saves_draft(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.jira_cli import __main__ as cli_module

    monkeypatch.setattr(cli_module, "DRAFT_DIR", tmp_path / "drafts")
    from scripts.jira_cli.template import SKELETON

    stderr = io.StringIO()
    with redirect_stderr(stderr):
        code = main(
            ["create", "--epic", "BH-260", "--title", "x", "--body", SKELETON],
            factory=_stub_factory(httpx.MockTransport(lambda req: httpx.Response(200))),
        )
    assert code == 2
    assert "placeholder" in stderr.getvalue()
    drafts = list((tmp_path / "drafts").glob("*.md"))
    assert len(drafts) == 1


def test_error_classes_have_distinct_exit_codes() -> None:
    from scripts.jira_cli.errors import (
        AuthError,
        EpicNotFoundError,
        JiraAPIError,
        TemplateError,
    )

    assert UsageError().exit_code == 2
    assert TemplateError().exit_code == 2
    assert EpicNotFoundError().exit_code == 3
    assert AuthError().exit_code == 4
    assert JiraAPIError().exit_code == 5
    assert isinstance(UsageError(), JiraCLIError)
