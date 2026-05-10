"""CLI entry point for ai-workspace."""

from __future__ import annotations

import typer

from ai_workspace.cli import (
    adopt_cmd,
    docs_cmd,
    handoff_cmd,
    index_cmd,
    init_cmd,
    skills_cmd,
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
