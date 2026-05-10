"""Stubs for workspace index commands."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Manage workspace indexes.", invoke_without_command=True)


def _not_implemented() -> None:
    console.print("[yellow]Not yet implemented[/yellow]")


@app.callback()
def index_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _not_implemented()


@app.command("rebuild")
def index_rebuild() -> None:
    _not_implemented()
