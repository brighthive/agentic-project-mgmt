"""Assign command - bulk assign tickets to team members from YAML config."""

from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from jira_cli.config_loader import load_assignment_config
from jira_lib.jira_config import load_config
from jira_lib.jira_operations import assign_issue, get_user_by_email

console = Console()


def assign_command(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="Path to assignment YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
) -> None:
    """Bulk assign tickets to team members from YAML configuration.

    Example:
        jira assign --config config/assignments.yaml

    Config format:
        team:
          member_name:
            email: member@example.com
            tickets:
              - TICKET-123
              - TICKET-456
    """
    console.print("\n[bold blue]🎯 Jira Ticket Assignment Tool[/bold blue]\n")

    # Load Jira configuration
    try:
        jira_config = load_config()
        console.print(f"[green]✓[/green] Loaded Jira config from {jira_config.base_url}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load Jira config: {e}")
        raise typer.Exit(code=1)

    # Load assignment configuration
    try:
        assignment_config = load_assignment_config(config)
        console.print(f"[green]✓[/green] Loaded assignment config from {config}")
    except FileNotFoundError:
        console.print(f"[red]✗[/red] Config file not found: {config}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        console.print(f"[red]✗[/red] Invalid configuration schema:")
        for error in e.errors():
            console.print(f"  - {error['loc'][0]}: {error['msg']}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load config: {e}")
        raise typer.Exit(code=1)

    # Track results
    results = {"success": [], "failed": []}

    # Process each team member
    total_tickets = sum(len(member.tickets) for member in assignment_config.team.values())
    console.print(f"\n[bold]Processing {total_tickets} ticket assignments...[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for member_name, member_config in assignment_config.team.items():
            task = progress.add_task(
                f"Processing {member_name} ({len(member_config.tickets)} tickets)...",
                total=len(member_config.tickets),
            )

            # Get user by email
            user, error = get_user_by_email(jira_config, member_config.email)
            if error:
                console.print(
                    f"[red]✗[/red] Failed to find user {member_config.email}: {error}"
                )
                for ticket in member_config.tickets:
                    results["failed"].append((ticket, member_config.email, error.message))
                progress.update(task, advance=len(member_config.tickets))
                continue

            # Assign each ticket
            for ticket in member_config.tickets:
                assigned_issue, assign_error = assign_issue(
                    jira_config, ticket, user.account_id
                )

                if assigned_issue and not assign_error:
                    results["success"].append((ticket, member_config.email))
                    console.print(
                        f"[green]✓[/green] {ticket} → {member_name} ({member_config.email})"
                    )
                else:
                    error_msg = assign_error.message if assign_error else "Unknown error"
                    results["failed"].append((ticket, member_config.email, error_msg))
                    console.print(
                        f"[red]✗[/red] {ticket} → {member_name}: {error_msg}"
                    )

                progress.update(task, advance=1)

    # Show summary
    console.print("\n[bold]📊 Assignment Summary[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Percentage", justify="right")

    success_count = len(results["success"])
    failed_count = len(results["failed"])
    total = success_count + failed_count

    if total > 0:
        success_pct = (success_count / total) * 100
        failed_pct = (failed_count / total) * 100
    else:
        success_pct = failed_pct = 0

    table.add_row(
        "[green]✓ Successful[/green]",
        str(success_count),
        f"{success_pct:.1f}%",
    )
    table.add_row(
        "[red]✗ Failed[/red]",
        str(failed_count),
        f"{failed_pct:.1f}%",
    )
    table.add_row(
        "[bold]Total[/bold]",
        str(total),
        "100.0%",
    )

    console.print(table)

    # Show failures in detail if any
    if results["failed"]:
        console.print("\n[bold red]Failed Assignments:[/bold red]")
        for ticket, email, error in results["failed"]:
            console.print(f"  [red]•[/red] {ticket} ({email}): {error}")

    # Exit with appropriate code
    if failed_count > 0:
        console.print(
            f"\n[yellow]⚠[/yellow]  {failed_count}/{total} assignments failed"
        )
        raise typer.Exit(code=1)
    else:
        console.print(f"\n[green]✓[/green] All {success_count} assignments successful!")
        raise typer.Exit(code=0)
