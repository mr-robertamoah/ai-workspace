"""Skills subcommands: list, search, show, propose."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_workspace.core.errors import SkillError
from ai_workspace.core.paths import global_layer_path
from ai_workspace.intelligence.skills import (
    SkillMetadata,
    ensure_builtin_skills,
    get_skill,
    list_proposed_skills,
    list_skills,
    propose_skill,
    search_skills,
)

console = Console()
app = typer.Typer(help="Manage reusable skills.", invoke_without_command=True)


def _ensure(global_root):
    ensure_builtin_skills(global_root)


def _skills_table(skills: list[SkillMetadata], title: str = "Skills") -> Table:
    table = Table(title=title)
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Tags")
    table.add_column("Description")
    for s in skills:
        desc = s.description.strip().replace("\n", " ")
        if len(desc) > 60:
            desc = desc[:57] + "..."
        table.add_row(s.name, s.status, ", ".join(s.tags), desc)
    return table


@app.callback()
def skills_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print("[yellow]Not yet implemented[/yellow]")


@app.command("list")
def skills_list() -> None:
    """List all available skills."""
    global_root = global_layer_path()
    _ensure(global_root)
    active = list_skills(global_root)
    proposed = list_proposed_skills(global_root)
    all_skills = active + [
        SkillMetadata(**{**s.model_dump(), "status": f"{s.status} [proposed]"}) for s in proposed
    ]
    console.print(_skills_table(all_skills))


@app.command("search")
def skills_search(query: str = typer.Argument("")) -> None:
    """Search skills by name, description, or tag."""
    global_root = global_layer_path()
    _ensure(global_root)
    results = search_skills(global_root, query) if query else list_skills(global_root)
    if not results:
        console.print("No skills found.")
        return
    console.print(_skills_table(results, title=f"Skills matching '{query}'"))


@app.command("show")
def skills_show(name: str = typer.Argument("")) -> None:
    """Show full details for a skill."""
    if not name:
        console.print("[red][ERROR][/red] Skill name required.")
        raise typer.Exit(1)
    global_root = global_layer_path()
    _ensure(global_root)
    try:
        skill = get_skill(global_root, name)
    except SkillError as exc:
        console.print(f"[red][ERROR][/red] {exc}")
        raise typer.Exit(1)

    skill_dir = global_root / "skills" / name
    notes_lines = ""
    notes_file = skill_dir / "notes.md"
    if notes_file.exists():
        notes_lines = "\n".join(notes_file.read_text().splitlines()[:10])

    console.print(
        Panel(
            f"[bold]Name:[/bold] {skill.name}\n"
            f"[bold]Version:[/bold] {skill.version}\n"
            f"[bold]Description:[/bold] {skill.description.strip()}\n"
            f"[bold]Tags:[/bold] {', '.join(skill.tags)}\n"
            f"[bold]Validation:[/bold] {', '.join(skill.validation) or 'none'}\n"
            f"[bold]Related:[/bold] {', '.join(skill.related_skills) or 'none'}\n\n"
            f"[bold]Notes:[/bold]\n{notes_lines}",
            title=f"Skill: {skill.name}",
        )
    )


@app.command("propose")
def skills_propose(
    name: Optional[str] = typer.Option(None, "--name"),
    description: Optional[str] = typer.Option(None, "--description"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
) -> None:
    """Propose a new skill (written to <name>-proposed/)."""
    if not name:
        name = typer.prompt("Skill name (kebab-case)")
    if not description:
        description = typer.prompt("Description")
    if not tags:
        tags = typer.prompt("Tags (comma-separated)", default="")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    global_root = global_layer_path()
    _ensure(global_root)
    metadata = SkillMetadata(name=name, description=description, tags=tag_list)
    try:
        path = propose_skill(global_root, metadata)
    except SkillError as exc:
        console.print(f"[red][ERROR][/red] {exc}")
        raise typer.Exit(1)
    console.print(f"[green]Proposed skill written to:[/green] {path}")
