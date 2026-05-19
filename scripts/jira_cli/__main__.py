"""CLI entrypoint — `python -m scripts.jira_cli ...` or via bin/jira-cli."""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from scripts.jira_cli.client import JiraClient, build_http_client
from scripts.jira_cli.config import load_config_from_env
from scripts.jira_cli.errors import JiraCLIError, UsageError
from scripts.jira_cli.template import SKELETON, is_unedited_skeleton

DRAFT_DIR = Path.home() / ".jira-cli" / "drafts"


def _log(msg: str) -> None:
    print(f"[jira-cli] {msg}", file=sys.stderr)


def _maybe_hint_skill() -> None:
    if os.environ.get("CLAUDECODE") == "1":
        _log("hint: inside Claude Code, prefer /create-jira-ticket for richer context")


def _save_draft(body: str, *, label: str) -> Path:
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    path = DRAFT_DIR / f"{stamp}-{label}.md"
    path.write_text(body, encoding="utf-8")
    return path


def _open_editor(initial: str, *, label: str = "ticket") -> str:
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "vi"
    editor_argv = shlex.split(editor)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(initial)
        path = Path(tmp.name)
    try:
        result = subprocess.run([*editor_argv, str(path)], check=False)
        body = path.read_text(encoding="utf-8")
        if result.returncode != 0:
            saved = _save_draft(body, label=label)
            raise UsageError(
                f"editor exited non-zero ({result.returncode}); draft saved at {saved}"
            )
        return body
    finally:
        path.unlink(missing_ok=True)


def _default_client_factory() -> JiraClient:
    config = load_config_from_env()
    http = build_http_client(config=config)
    return JiraClient(config=config, http=http)


ClientFactory = Callable[[], JiraClient]


def _cmd_whoami(_args: argparse.Namespace, factory: ClientFactory) -> int:
    client = factory()
    user = client.whoami()
    _log("auth.ok")
    print(f"{user.account_id}\t{user.display_name}\t{user.email or ''}")
    return 0


def _cmd_epics(args: argparse.Namespace, factory: ClientFactory) -> int:
    client = factory()
    epics = client.list_epics(include_done=bool(args.all))
    _log(f"epic.lookup.ok count={len(epics)}")
    print("KEY\tSTATUS\tSUMMARY")
    for epic in epics:
        status = "Done" if epic.done else "Open"
        print(f"{epic.key}\t{status}\t{epic.summary}")
    return 0


def _cmd_my(args: argparse.Namespace, factory: ClientFactory) -> int:
    client = factory()
    statuses = [s.strip() for s in args.status.split(",")] if args.status else None
    issues = client.my_open_issues(statuses=statuses)
    print("KEY\tSTATUS\tPOINTS\tSUMMARY")
    for issue in issues:
        points = "" if issue.points is None else f"{issue.points:g}"
        print(f"{issue.key}\t{issue.status}\t{points}\t{issue.summary}")
    return 0


def _cmd_transition(args: argparse.Namespace, factory: ClientFactory) -> int:
    client = factory()
    transition = client.transition(key=args.key, to_state=args.state)
    _log("transition.ok")
    print(f"{args.key} -> {transition.to_status}")
    return 0


def _cmd_create(args: argparse.Namespace, factory: ClientFactory) -> int:
    if args.type and args.type != "Task":
        raise UsageError(f"issueType={args.type} is forbidden; use Task")
    if not args.epic:
        raise UsageError("missing --epic BH-XXX")
    if not args.title:
        raise UsageError("missing --title")

    if args.from_stdin:
        body = sys.stdin.read()
    elif args.body:
        body = args.body
    else:
        body = _open_editor(SKELETON, label=args.epic)

    if not body.strip():
        raise UsageError("description body is empty; aborting")
    if is_unedited_skeleton(body):
        saved = _save_draft(body, label=args.epic)
        raise UsageError(
            f"description still contains placeholder markers — edit and retry. "
            f"Draft saved at {saved}"
        )

    client = factory()
    labels = [item.strip() for item in args.labels.split(",")] if args.labels else None
    assignee = args.assignee
    if assignee == "me":
        assignee = client.whoami().account_id

    issue = client.create_task(
        epic_key=args.epic,
        summary=args.title,
        description=body,
        priority=args.priority,
        labels=labels,
        assignee_account_id=assignee,
    )
    _log(f"ticket.create.ok key={issue.key}")
    print(f"{issue.key}\t{issue.url}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jira-cli",
        description="Universal Jira CLI for BrightHive — see docs/specs/jira-cli-onboarding.md",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="print authenticated user").set_defaults(func=_cmd_whoami)

    epics = sub.add_parser("epics", help="list epics on board 152")
    epics.add_argument("--all", action="store_true", help="include Done epics")
    epics.set_defaults(func=_cmd_epics)

    my_cmd = sub.add_parser("my", help="list my open tickets")
    my_cmd.add_argument("--status", default="", help='comma-separated, e.g. "To Do,In Progress"')
    my_cmd.set_defaults(func=_cmd_my)

    trans = sub.add_parser("transition", help="transition a ticket")
    trans.add_argument("key", help="ticket key, e.g. BH-12345")
    trans.add_argument("state", help='target status name, e.g. "In Progress"')
    trans.set_defaults(func=_cmd_transition)

    create = sub.add_parser("create", help="create a Task under an open epic")
    create.add_argument("--epic", required=False, help="parent epic key, e.g. BH-260")
    create.add_argument("--title", required=False, help="ticket summary (≤72 chars)")
    create.add_argument("--type", default="Task", help="issue type (Task only)")
    create.add_argument("--priority", default="Medium", help="Highest|High|Medium|Low")
    create.add_argument("--labels", default="", help="comma-separated labels")
    create.add_argument("--assignee", default="", help='account ID or "me"')
    create.add_argument("--body", default="", help="description body (overrides editor)")
    create.add_argument("--from-stdin", action="store_true", help="read body from stdin")
    create.set_defaults(func=_cmd_create)

    return parser


def main(argv: list[str] | None = None, *, factory: ClientFactory | None = None) -> int:
    _maybe_hint_skill()
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    client_factory = factory or _default_client_factory
    try:
        return int(args.func(args, client_factory))
    except JiraCLIError as err:
        _log(f"error: {err}")
        return err.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
