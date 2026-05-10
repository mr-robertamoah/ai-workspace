"""standards list, show, and override commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_workspace.core.paths import global_layer_path
from ai_workspace.intelligence.standards import (
    effective_standards,
    get_standard,
    list_standard_names,
)

console = Console()
app = typer.Typer(help="View and manage engineering standards.", invoke_without_command=True)


@app.callback()
def standards_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print("Use a subcommand: list, show, override")


@app.command("list")
def standards_list() -> None:
    """List all available standards with override status."""
    global_root = global_layer_path()

    try:
        from ai_workspace.core.paths import find_project_root

        project_root: Optional[Path] = find_project_root()
    except Exception:
        project_root = None

    rows = effective_standards(project_root=project_root, global_root=global_root)
    if not rows:
        console.print("No standards found. Run any command to initialize the global layer.")
        return

    table = Table(title="Engineering Standards")
    table.add_column("Name")
    table.add_column("Source")
    table.add_column("Workspace Override")
    for row in rows:
        override_str = "[green]yes[/green]" if row["has_override"] else "—"
        table.add_row(row["name"], row["source"], override_str)
    console.print(table)


@app.command("show")
def standards_show(name: str = typer.Argument("")) -> None:
    """Show the effective standard (global + workspace override merged)."""
    if not name:
        console.print("[red][ERROR][/red] Standard name required.")
        raise typer.Exit(1)

    global_root = global_layer_path()

    try:
        from ai_workspace.core.paths import find_project_root

        project_root: Optional[Path] = find_project_root()
    except Exception:
        project_root = None

    try:
        content = get_standard(name, project_root=project_root, global_root=global_root)
    except FileNotFoundError as exc:
        console.print(f"[red][ERROR][/red] {exc}")
        raise typer.Exit(1)

    label = f"Standard: {name}"
    if project_root and (project_root / ".ai" / "standards" / f"{name}.md").exists():
        label += " [with workspace override]"
    console.print(Panel(content, title=label))


@app.command("override")
def standards_override(
    name: str = typer.Argument(""),
    edit: bool = typer.Option(False, "--edit", help="Open override file in $EDITOR"),
) -> None:
    """Create or edit a workspace-level override for a standard."""
    if not name:
        console.print("[red][ERROR][/red] Standard name required.")
        raise typer.Exit(1)

    global_root = global_layer_path()
    if name not in list_standard_names(global_root):
        console.print(
            f"[red][ERROR][/red] No standard named '{name}'. Run `standards list` to see available."
        )
        raise typer.Exit(1)

    try:
        from ai_workspace.core.paths import find_project_root

        project_root = find_project_root()
    except Exception as exc:
        console.print(f"[red][ERROR][/red] {exc}")
        raise typer.Exit(1)

    override_dir = project_root / ".ai" / "standards"
    override_dir.mkdir(parents=True, exist_ok=True)
    override_file = override_dir / f"{name}.md"

    if not override_file.exists():
        override_file.write_text(
            f"# {name.title()} — Project Overrides\n\n"
            "<!-- Add project-specific rules below. They are appended to the global standard. -->\n\n",
            encoding="utf-8",
        )
        console.print(f"[green]Created override file:[/green] {override_file}")
    else:
        console.print(f"[yellow]Override file already exists:[/yellow] {override_file}")

    if edit:
        import os
        import subprocess

        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(override_file)])
