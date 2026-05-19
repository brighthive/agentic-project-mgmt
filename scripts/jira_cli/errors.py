"""Exception hierarchy with exit-code mapping for CLI."""

from __future__ import annotations


class JiraCLIError(Exception):
    """Base for all CLI errors; carries the exit code to surface."""

    exit_code: int = 1


class UsageError(JiraCLIError):
    """Bad arguments — print usage and exit 2."""

    exit_code = 2


class EpicNotFoundError(JiraCLIError):
    """Epic does not exist or is Done — exit 3."""

    exit_code = 3


class AuthError(JiraCLIError):
    """Missing env vars or invalid token — exit 4."""

    exit_code = 4


class JiraAPIError(JiraCLIError):
    """Non-2xx response or network failure — exit 5."""

    exit_code = 5


class TemplateError(JiraCLIError):
    """Description body fails template enforcement — exit 2."""

    exit_code = 2
