"""Stub for the `ai-workspace init` command."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def register(app: typer.Typer) -> None:
    """Register the `init` command on the root CLI app."""

    @app.command("init")
    def init_command() -> None:
        console.print("[yellow]Not yet implemented[/yellow]")
