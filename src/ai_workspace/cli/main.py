"""CLI entry point for ai-workspace."""

from __future__ import annotations

from pathlib import Path

import typer

from ai_workspace.cli import (
    adopt_cmd,
    docs_cmd,
    handoff_cmd,
    index_cmd,
    init_cmd,
    skills_cmd,
    standards_cmd,
    summarize_cmd,
    validate_cmd,
)

app = typer.Typer(
    name="ai-workspace",
    help="AI-native engineering workspace CLI.",
    invoke_without_command=True,
    no_args_is_help=True,
)

init_cmd.register(app)
adopt_cmd.register(app)
summarize_cmd.register(app)

app.add_typer(validate_cmd.app, name="validate")
app.add_typer(index_cmd.app, name="index")
app.add_typer(skills_cmd.app, name="skills")
app.add_typer(docs_cmd.app, name="docs")
app.add_typer(handoff_cmd.app, name="handoff")
app.add_typer(standards_cmd.app, name="standards")


@app.callback(invoke_without_command=True)
def _global_init(ctx: typer.Context) -> None:
    """Silently initialize global layer on first run."""
    _ensure_global_layer()


def _home() -> Path:
    return Path.home()


def _ensure_global_layer() -> None:
    from pathlib import Path

    from rich.console import Console

    global_root = _home() / ".ai-workspace"
    if global_root.exists():
        return

    console = Console()
    console.print("[dim]Initialized global workspace layer at ~/.ai-workspace/[/dim]")

    import shutil

    _data = Path(__file__).parent.parent / "data"
    global_root.mkdir(parents=True, exist_ok=True)
    for subdir in ("skills", "standards", "templates", "prompts", "memory", "indexes", "cache"):
        (global_root / subdir).mkdir(exist_ok=True)

    # Copy built-in skills
    skills_src = _data / "skills"
    if skills_src.is_dir():
        for skill in skills_src.iterdir():
            dst = global_root / "skills" / skill.name
            if not dst.exists():
                shutil.copytree(skill, dst)

    # Copy built-in standards
    standards_src = _data / "standards"
    if standards_src.is_dir():
        for std in standards_src.glob("*.md"):
            shutil.copy2(std, global_root / "standards" / std.name)

    # Write config.yaml
    from ruamel.yaml import YAML

    from ai_workspace.workspace.generator import current_timestamp

    yaml = YAML()
    yaml.default_flow_style = False
    with (global_root / "config.yaml").open("w") as fh:
        yaml.dump({"version": "0.1.0", "created_at": current_timestamp()}, fh)

    # Build global indexes
    from ai_workspace.intelligence.indexes import rebuild_global_indexes

    rebuild_global_indexes(global_root)
