"""Workspace index commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.core.errors import WorkspaceError, WorkspaceValidationError
from ai_workspace.core.paths import find_project_root
from ai_workspace.workspace.index_builder import rebuild_all_indexes

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
    try:
        project_root = find_project_root()
        config = load_workspace_yaml(project_root / "workspace.yaml")
        counts = rebuild_all_indexes(project_root, config)
    except (WorkspaceError, WorkspaceValidationError) as exc:
        console.print(f"[red]\\[ERROR][/red] {exc}")
        raise typer.Exit(code=1) from exc

    table = Table(title="Index Rebuild Summary")
    table.add_column("Index")
    table.add_column("Entries", justify="right")
    for index_name, entry_count in counts.items():
        table.add_row(index_name, str(entry_count))
    console.print(table)
