"""Stub for the `ai-workspace summarize` command."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def register(app: typer.Typer) -> None:
    """Register the `summarize` command on the root CLI app."""

    @app.command("summarize")
    def summarize_command() -> None:
        console.print("[yellow]Not yet implemented[/yellow]")
