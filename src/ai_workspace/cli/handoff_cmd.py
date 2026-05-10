"""Stubs for handoff commands."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Generate and manage handoffs.", invoke_without_command=True)


def _not_implemented() -> None:
    console.print("[yellow]Not yet implemented[/yellow]")


@app.callback()
def handoff_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _not_implemented()


@app.command("generate")
def handoff_generate() -> None:
    _not_implemented()
