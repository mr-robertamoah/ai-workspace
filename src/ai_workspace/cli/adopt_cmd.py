"""The `ai-workspace adopt` command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.core.errors import WorkspaceError
from ai_workspace.workspace.adopter import adopt_project

console = Console()


def register(app: typer.Typer) -> None:
    """Register the `adopt` command on the root CLI app."""

    @app.command("adopt")
    def adopt_command(
        root: Optional[str] = typer.Option(None, "--root", help="Target directory (default: cwd)"),
        dry_run: bool = typer.Option(
            False, "--dry-run", help="Detect and suggest but create nothing"
        ),
        force: bool = typer.Option(False, "--force", help="Overwrite existing .ai/ files"),
    ) -> None:
        target = Path(root) if root else Path.cwd()

        workspace_yaml = target / "workspace.yaml"
        if not workspace_yaml.exists():
            console.print(
                "[red][ERROR][/red] No workspace.yaml found. "
                "Run `ai-workspace init` first or provide --root pointing to a project with workspace.yaml."
            )
            raise typer.Exit(1)

        try:
            config = load_workspace_yaml(workspace_yaml)
        except WorkspaceError as exc:
            console.print(f"[red][ERROR][/red] {exc}")
            raise typer.Exit(1)

        if dry_run:
            from ai_workspace.workspace.detector import detect_project

            detection = detect_project(target)
            console.print(
                Panel(
                    f"[bold]Dry run — nothing written[/bold]\n\n"
                    f"Languages: {', '.join(detection.languages)}\n"
                    f"Frameworks: {', '.join(detection.frameworks) or 'none'}\n"
                    f"CI: {', '.join(detection.ci_systems) or 'none'}\n"
                    f"Has tests: {detection.has_tests}\n"
                    f"Has docs: {detection.has_docs}",
                    title="adopt --dry-run",
                )
            )
            return

        try:
            result = adopt_project(target, config, force=force)
        except WorkspaceError as exc:
            console.print(f"[red][ERROR][/red] {exc}")
            raise typer.Exit(1)

        console.print(
            Panel(
                "\n".join(f"  {p}" for p in result.files_created[:20]),
                title=f"[green]Adopted {config.workspace.name}[/green]",
            )
        )

        if result.suggested_docs:
            console.print(
                Panel(
                    "\n".join(f"  • {s}" for s in result.suggested_docs),
                    title="[yellow]Suggested documentation (not created)[/yellow]",
                )
            )
