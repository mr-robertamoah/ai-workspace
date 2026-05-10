"""Implementation of the `ai-workspace init` command."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from ai_workspace.core.config import (
    AIConfig,
    ArchitectureConfig,
    DocumentationConfig,
    LanguageConfig,
    RepositoryConfig,
    SecurityConfig,
    StandardsConfig,
    WorkspaceConfig,
    WorkspaceMetadata,
    WorkspaceType,
    load_workspace_yaml,
    write_workspace_yaml,
)
from ai_workspace.core.errors import WorkspaceError, WorkspaceValidationError
from ai_workspace.workspace.generator import generate_workspace, planned_workspace_paths

console = Console()

WORKSPACE_TYPES: list[WorkspaceType] = ["monorepo", "single", "multi"]
PRIMARY_LANGUAGES = ["python", "go", "typescript", "rust", "java", "other"]
ARCHITECTURE_STYLES = [
    "modular-monolith",
    "microservices",
    "monolith",
    "serverless",
    "library",
    "other",
]
DOC_STRUCTURES = ["minimal", "standard", "full"]


def _error(message: str) -> None:
    console.print(f"[red]\\[ERROR][/red] {message}")


def _success_panel(created_paths: list[Path], dry_run: bool) -> None:
    title = "Dry Run" if dry_run else "Workspace Initialized"
    prefix = "Would create" if dry_run else "Created"
    project_root = Path.cwd()
    display_paths = []
    for path in created_paths:
        try:
            display_paths.append(path.relative_to(project_root))
        except ValueError:
            display_paths.append(path)
    body = "\n".join(f"- {path}" for path in display_paths)
    console.print(Panel.fit(f"{prefix}:\n{body}", title=title))


def _choose_option(prompt_text: str, options: list[str], default_index: int = 0) -> str:
    console.print(f"{prompt_text}:")
    for index, option in enumerate(options, start=1):
        console.print(f"{index}. {option}")

    while True:
        choice = typer.prompt("Select option", default=str(default_index + 1))
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        _error("Please choose one of the numbered options.")


def _prompt_project_name() -> str:
    while True:
        project_name = typer.prompt("Project name")
        if (
            project_name
            and len(project_name) <= 64
            and project_name == project_name.lower()
            and all(character.isalnum() or character == "-" for character in project_name)
        ):
            return project_name
        _error("Project name must be kebab-case, lowercase, and contain no spaces.")


def _default_standards_for_language(primary_language: str) -> StandardsConfig:
    mapping = {
        "python": ("pytest", "black", "ruff"),
        "typescript": ("jest", "prettier", "eslint"),
        "go": ("go-test", "gofmt", "golangci-lint"),
        "rust": ("other", "other", "other"),
        "java": ("other", "other", "other"),
        "other": ("other", "other", "other"),
    }
    testing, formatting, linting = mapping[primary_language]
    return StandardsConfig(testing=testing, formatting=formatting, linting=linting)


def _prompt_repositories(workspace_type: WorkspaceType) -> list[RepositoryConfig]:
    if workspace_type == "single":
        return []

    while True:
        count = typer.prompt("How many repositories are in this workspace?", default="1")
        if count.isdigit() and int(count) > 0:
            break
        _error("Repository count must be a positive integer.")

    repositories: list[RepositoryConfig] = []
    for number in range(int(count)):
        name = typer.prompt(f"Repository {number + 1} name")
        path = typer.prompt(f"Repository {number + 1} path")
        repositories.append(RepositoryConfig(name=name, path=path))
    return repositories


def _build_interactive_config() -> WorkspaceConfig:
    project_name = _prompt_project_name()
    workspace_type = _choose_option("Workspace type", WORKSPACE_TYPES)
    repositories = _prompt_repositories(workspace_type)
    primary_language = _choose_option("Primary language", PRIMARY_LANGUAGES)
    architecture_style = _choose_option("Architecture style", ARCHITECTURE_STYLES, default_index=2)
    enable_ai = typer.confirm("Enable AI features?", default=True)
    enable_docs = typer.confirm("Enable documentation?", default=True)
    doc_structure = _choose_option("Documentation structure", DOC_STRUCTURES, default_index=1)

    return WorkspaceConfig(
        workspace=WorkspaceMetadata(name=project_name, type=workspace_type),
        repositories=repositories,
        language=LanguageConfig(primary=primary_language, secondary=[]),
        architecture=ArchitectureConfig(style=architecture_style),
        ai=AIConfig(
            enabled=enable_ai,
            adr=enable_ai,
            handoffs=enable_ai,
            tasks=enable_ai,
            agents=["codex"] if enable_ai else [],
        ),
        documentation=DocumentationConfig(enabled=enable_docs, structure=doc_structure),
        security=SecurityConfig(),
        standards=_default_standards_for_language(primary_language),
    )


def _planned_paths_for_init(config: WorkspaceConfig, project_root: Path) -> list[Path]:
    return [project_root / "workspace.yaml", *planned_workspace_paths(config, project_root)]


def _run_init(
    config: WorkspaceConfig, project_root: Path, dry_run: bool, force: bool
) -> list[Path]:
    planned_paths = _planned_paths_for_init(config, project_root)
    if dry_run:
        return planned_paths

    scaffold_root = project_root / ".ai"
    if scaffold_root.exists() and not force:
        raise WorkspaceError(
            f"Workspace context already exists at {scaffold_root}. Re-run with --force."
        )

    write_workspace_yaml(project_root / "workspace.yaml", config)
    created_paths = [project_root / "workspace.yaml"]
    created_paths.extend(generate_workspace(config, project_root, force=force))
    return created_paths


def register(app: typer.Typer) -> None:
    """Register the `init` command on the root CLI app."""

    @app.command("init")
    def init_command(
        file: Path | None = typer.Option(None, "--file", "-f", exists=True, dir_okay=False),
        dry_run: bool = typer.Option(False, "--dry-run"),
        force: bool = typer.Option(False, "--force"),
    ) -> None:
        try:
            config = load_workspace_yaml(file) if file else _build_interactive_config()
            created_paths = _run_init(config, Path.cwd(), dry_run=dry_run, force=force)
            _success_panel(created_paths, dry_run=dry_run)
        except (WorkspaceError, WorkspaceValidationError) as exc:
            _error(str(exc))
            raise typer.Exit(code=1) from exc
