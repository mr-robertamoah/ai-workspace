"""Stubs for workspace validation commands."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(
    help="Validate workspace configuration and safety checks.",
    invoke_without_command=True,
)


def _not_implemented() -> None:
    console.print("[yellow]Not yet implemented[/yellow]")


@app.callback()
def validate_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _not_implemented()


@app.command("security")
def validate_security() -> None:
    _not_implemented()
