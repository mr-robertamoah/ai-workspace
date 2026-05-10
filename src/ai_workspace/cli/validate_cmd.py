"""validate and validate security commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ai_workspace.core.errors import WorkspaceError
from ai_workspace.core.paths import find_project_root
from ai_workspace.security.scanner import scan_security
from ai_workspace.security.validator import ValidationResult, validate_workspace

console = Console()
app = typer.Typer(
    help="Validate workspace configuration and safety checks.",
    invoke_without_command=True,
)

_STATUS_COLOR = {"pass": "green", "warn": "yellow", "fail": "red"}


def _print_results(results: list[ValidationResult], title: str) -> bool:
    table = Table(title=title)
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Message")
    has_fail = False
    for r in results:
        color = _STATUS_COLOR.get(r.status, "white")
        table.add_row(r.check, f"[{color}]{r.status}[/{color}]", r.message)
        if r.status == "fail":
            has_fail = True
    console.print(table)
    return has_fail


@app.callback()
def validate_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        try:
            root = find_project_root()
        except WorkspaceError as exc:
            console.print(f"[red][ERROR][/red] {exc}")
            raise typer.Exit(1)
        results = validate_workspace(root)
        has_fail = _print_results(results, "Workspace Validation")
        if has_fail:
            raise typer.Exit(1)


@app.command("security")
def validate_security() -> None:
    """Run security scans: pip-audit, bandit, secrets, YAML safety, permissions."""
    try:
        root = find_project_root()
    except WorkspaceError as exc:
        console.print(f"[red][ERROR][/red] {exc}")
        raise typer.Exit(1)
    results = scan_security(root)
    has_fail = _print_results(results, "Security Scan")
    passed = sum(1 for r in results if r.status == "pass")
    warned = sum(1 for r in results if r.status == "warn")
    failed = sum(1 for r in results if r.status == "fail")
    console.print(
        f"\n[green]{passed} passed[/green], [yellow]{warned} warnings[/yellow], [red]{failed} failed[/red]"
    )
    if has_fail:
        raise typer.Exit(1)
