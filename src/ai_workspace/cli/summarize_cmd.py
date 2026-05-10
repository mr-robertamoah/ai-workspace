"""The `ai-workspace summarize` command."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.core.errors import WorkspaceError
from ai_workspace.core.paths import find_project_root
from ai_workspace.workspace.summarizer import summarize_workspace

console = Console()


def register(app: typer.Typer) -> None:
    """Register the `summarize` command on the root CLI app."""

    @app.command("summarize")
    def summarize_command(
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Print what would be generated without writing"
        ),
    ) -> None:
        try:
            root = find_project_root()
        except WorkspaceError as exc:
            console.print(f"[red][ERROR][/red] {exc}")
            raise typer.Exit(1)

        try:
            config = load_workspace_yaml(root / "workspace.yaml")
        except WorkspaceError as exc:
            console.print(f"[red][ERROR][/red] {exc}")
            raise typer.Exit(1)

        if dry_run:
            console.print("[bold]Dry run — would generate:[/bold]")
            for name in ("repo-map-generated.md", "dependency-summary.md", "tech-detection.yaml"):
                console.print(f"  {root / '.ai' / 'generated' / name}")
            return

        try:
            written = summarize_workspace(root, config)
        except WorkspaceError as exc:
            console.print(f"[red][ERROR][/red] {exc}")
            raise typer.Exit(1)

        table = Table(title="Generated Summaries")
        table.add_column("File")
        table.add_column("Path")
        for name, path in written.items():
            table.add_row(name, str(path))
        console.print(table)
