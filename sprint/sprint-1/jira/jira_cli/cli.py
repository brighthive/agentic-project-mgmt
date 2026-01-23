"""Main CLI application entry point."""

import typer
from rich.console import Console

from jira_cli.commands.assign import assign_command

app = typer.Typer(
    name="jira",
    help="BrightHive Jira automation CLI tool",
    no_args_is_help=True,
)

# Global console for rich output
console = Console()

# Register commands
app.command("assign")(assign_command)


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
