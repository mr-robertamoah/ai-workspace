"""handoff generate command."""

from __future__ import annotations

import typer
from rich.console import Console

from ai_workspace.core.errors import WorkspaceError
from ai_workspace.core.paths import find_project_root
from ai_workspace.workspace.handoff import HandoffData, generate_handoff

console = Console()
app = typer.Typer(help="Generate and manage handoffs.", invoke_without_command=True)


@app.callback()
def handoff_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print("[yellow]Not yet implemented[/yellow]")


@app.command("generate")
def handoff_generate() -> None:
    """Generate a handoff document interactively."""
    try:
        root = find_project_root()
    except WorkspaceError as exc:
        console.print(f"[red][ERROR][/red] {exc}")
        raise typer.Exit(1)

    accomplished = typer.prompt("What was accomplished?")
    current_state = typer.prompt("Current state?")
    blockers = typer.prompt("Blockers?", default="None")
    next_steps = typer.prompt("Next steps?")
    files_modified = typer.prompt(
        "Files modified? (comma-separated or brief description)", default="(not specified)"
    )
    decisions_made = typer.prompt("Decisions made?", default="(none)")
    tests_ok = typer.confirm("Are tests passing?", default=True)

    data = HandoffData(
        accomplished=accomplished,
        current_state=current_state,
        blockers=blockers,
        next_steps=next_steps,
        tests_passing=tests_ok,
        files_modified=files_modified,
        decisions_made=decisions_made,
    )
    path = generate_handoff(root, data)
    console.print(f"[green]Handoff written to:[/green] {path}")
