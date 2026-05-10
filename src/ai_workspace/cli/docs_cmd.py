"""docs templates and docs create commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ai_workspace.core.errors import WorkspaceError
from ai_workspace.core.paths import find_project_root
from ai_workspace.docs.templates import TEMPLATES, render_template

console = Console()
app = typer.Typer(help="Manage documentation helpers.", invoke_without_command=True)


@app.callback()
def docs_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        console.print("Use a subcommand. Run with --help for options.")


@app.command("templates")
def docs_templates() -> None:
    """List available documentation templates."""
    table = Table(title="Documentation Templates")
    table.add_column("Template Name")
    table.add_column("Description")
    table.add_column("Output Path")
    for name, tmpl in TEMPLATES.items():
        table.add_row(name, tmpl["description"], tmpl["output"])
    console.print(table)


@app.command("create")
def docs_create(
    template_name: str = typer.Argument(""),
    title: Optional[str] = typer.Option(None, "--title"),
    force: bool = typer.Option(False, "--force"),
) -> None:
    """Create a document from a template."""
    if not template_name:
        console.print(
            "[red][ERROR][/red] Template name required. Run `docs templates` to list available templates."
        )
        raise typer.Exit(1)

    if template_name not in TEMPLATES:
        console.print(
            f"[red][ERROR][/red] Unknown template '{template_name}'. Run `docs templates` to list available."
        )
        raise typer.Exit(1)

    try:
        root = find_project_root()
    except WorkspaceError as exc:
        console.print(f"[red][ERROR][/red] {exc}")
        raise typer.Exit(1)

    # Prompt for title if needed
    needs_title = template_name not in ("architecture-overview",)
    if needs_title and not title:
        title = typer.prompt("Title")

    content, output_path = render_template(template_name, root, title or "")

    if output_path.exists() and not force:
        console.print(f"[red][ERROR][/red] {output_path} already exists. Use --force to overwrite.")
        raise typer.Exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    # Update docs-index.yaml
    _update_docs_index(root, output_path, title or template_name)

    console.print(f"[green]Created:[/green] {output_path}")


def _update_docs_index(root: Path, doc_path: Path, title: str) -> None:
    from ruamel.yaml import YAML

    index_path = root / ".ai" / "indexes" / "docs-index.yaml"
    if not index_path.exists():
        return
    yaml = YAML()
    yaml.default_flow_style = False
    try:
        data = yaml.load(index_path.read_text(encoding="utf-8")) or {}
        docs = data.get("docs", [])
        rel = str(doc_path.relative_to(root))
        if not any(d.get("path") == rel for d in docs):
            from ai_workspace.workspace.generator import current_timestamp

            docs.append(
                {
                    "id": doc_path.stem,
                    "title": title,
                    "path": rel,
                    "tags": [],
                    "purpose": "",
                    "last_modified": current_timestamp(),
                }
            )
        data["docs"] = docs
        with index_path.open("w", encoding="utf-8") as fh:
            yaml.dump(data, fh)
    except Exception as exc:
        console.print(f"[yellow][WARN][/yellow] Could not update docs-index.yaml: {exc}")
