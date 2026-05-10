"""Stubs for skill management commands."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Manage reusable skills.", invoke_without_command=True)


def _not_implemented() -> None:
    console.print("[yellow]Not yet implemented[/yellow]")


@app.callback()
def skills_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _not_implemented()


@app.command("list")
def skills_list() -> None:
    _not_implemented()


@app.command("search")
def skills_search() -> None:
    _not_implemented()


@app.command("show")
def skills_show() -> None:
    _not_implemented()


@app.command("propose")
def skills_propose() -> None:
    _not_implemented()
