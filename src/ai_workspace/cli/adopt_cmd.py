"""Stub for the `ai-workspace adopt` command."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def register(app: typer.Typer) -> None:
    """Register the `adopt` command on the root CLI app."""

    @app.command("adopt")
    def adopt_command() -> None:
        console.print("[yellow]Not yet implemented[/yellow]")
