"""Stubs for documentation commands."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Manage documentation helpers.", invoke_without_command=True)


def _not_implemented() -> None:
    console.print("[yellow]Not yet implemented[/yellow]")


@app.callback()
def docs_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _not_implemented()


@app.command("templates")
def docs_templates() -> None:
    _not_implemented()


@app.command("create")
def docs_create() -> None:
    _not_implemented()
