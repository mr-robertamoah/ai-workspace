"""Workspace scaffold generation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from ai_workspace.core.config import WorkspaceConfig, workspace_config_data
from ai_workspace.core.errors import WorkspaceError
from ai_workspace.core.filesystem import ensure_directory, write_file
from ai_workspace.workspace.templates import (
    ADR_TEMPLATE,
    ARCHITECTURE_OVERVIEW_TEMPLATE,
    ARCHITECTURE_SUMMARY_TEMPLATE,
    BLOCKERS_TEMPLATE,
    CURRENT_PLAN_TEMPLATE,
    CURRENT_STATE_TEMPLATE,
    CURRENT_TASK_TEMPLATE,
    DEPENDENCY_SUMMARY_TEMPLATE,
    GENERATED_REPO_MAP_TEMPLATE,
    GETTING_STARTED_TEMPLATE,
    NEXT_STEPS_TEMPLATE,
    PROJECT_SUMMARY_TEMPLATE,
    REPO_MAP_TEMPLATE,
    START_HERE_TEMPLATE,
    TECH_DETECTION_TEMPLATE,
    render,
)

yaml_writer = YAML()
yaml_writer.default_flow_style = False

BASE_AI_DIRECTORIES = [
    ".ai",
    ".ai/indexes",
    ".ai/active-task",
    ".ai/handoffs",
    ".ai/generated",
    ".ai/context",
    ".ai/templates",
    ".ai/cache",
]

STANDARD_DOC_DIRECTORIES = [
    "docs/architecture",
    "docs/decisions",
    "docs/api",
    "docs/workflows",
    "docs/onboarding",
]

FULL_DOC_DIRECTORIES = STANDARD_DOC_DIRECTORIES + [
    "docs/infrastructure",
    "docs/runbooks",
    "docs/product",
]

BASE_TEMPLATED_FILES = {
    ".ai/start-here.md": START_HERE_TEMPLATE,
    ".ai/project-summary.md": PROJECT_SUMMARY_TEMPLATE,
    ".ai/architecture-summary.md": ARCHITECTURE_SUMMARY_TEMPLATE,
    ".ai/repo-map.md": REPO_MAP_TEMPLATE,
    ".ai/current-state.md": CURRENT_STATE_TEMPLATE,
    ".ai/active-task/current-task.md": CURRENT_TASK_TEMPLATE,
    ".ai/active-task/current-plan.md": CURRENT_PLAN_TEMPLATE,
    ".ai/active-task/blockers.md": BLOCKERS_TEMPLATE,
    ".ai/active-task/next-steps.md": NEXT_STEPS_TEMPLATE,
    ".ai/generated/repo-map-generated.md": GENERATED_REPO_MAP_TEMPLATE,
    ".ai/generated/dependency-summary.md": DEPENDENCY_SUMMARY_TEMPLATE,
    ".ai/generated/tech-detection.yaml": TECH_DETECTION_TEMPLATE,
    ".ai/templates/adr-template.md": ADR_TEMPLATE,
}

DOC_TEMPLATED_FILES = {
    "docs/architecture/architecture-overview.md": ARCHITECTURE_OVERVIEW_TEMPLATE,
    "docs/onboarding/getting-started.md": GETTING_STARTED_TEMPLATE,
}

INDEX_CONTENT = {
    "adr-index.yaml": {"generated_at": None, "adrs": []},
    "task-index.yaml": {"generated_at": None, "tasks": []},
    "docs-index.yaml": {"generated_at": None, "docs": []},
    "repo-index.yaml": {"generated_at": None, "repositories": []},
}


def workspace_scaffold_root(project_root: Path) -> Path:
    """Return the `.ai` scaffold root for a project."""

    return project_root / ".ai"


def current_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def documentation_directories(config: WorkspaceConfig) -> list[str]:
    """Return doc directory paths for the selected documentation mode."""

    if not config.documentation.enabled:
        return []
    if config.documentation.structure == "minimal":
        return ["docs/architecture", "docs/decisions"]
    if config.documentation.structure == "full":
        return FULL_DOC_DIRECTORIES
    return STANDARD_DOC_DIRECTORIES


def file_templates_for_config(config: WorkspaceConfig) -> dict[str, str]:
    """Return file templates relevant for the workspace config."""

    templates = dict(BASE_TEMPLATED_FILES)
    if not config.documentation.enabled:
        return templates

    templates["docs/architecture/architecture-overview.md"] = DOC_TEMPLATED_FILES[
        "docs/architecture/architecture-overview.md"
    ]
    if config.documentation.structure in {"standard", "full"}:
        templates["docs/onboarding/getting-started.md"] = DOC_TEMPLATED_FILES[
            "docs/onboarding/getting-started.md"
        ]
    return templates


def empty_directories(config: WorkspaceConfig) -> list[str]:
    """Return directories that should receive a `.gitkeep` file."""

    directories = [".ai/handoffs", ".ai/context", ".ai/cache", ".ai/indexes"]
    directories.extend(documentation_directories(config))
    return directories


def build_template_context(config: WorkspaceConfig) -> dict[str, Any]:
    """Build the substitution context used across workspace templates."""

    data = workspace_config_data(config)
    secondary_languages = data["language"].get("secondary", [])
    return {
        **data,
        "timestamp": current_timestamp(),
        "project_summary_one_liner": f"{config.workspace.name} project workspace scaffold.",
        "active_task_summary_or_none": "No active task yet.",
        "language": {
            **data["language"],
            "secondary_summary": ", ".join(secondary_languages) if secondary_languages else "none",
        },
        "doc": {
            "title": "Architecture Overview",
            "purpose": "Describe the system architecture for human and AI readers",
            "tags_yaml": "  - architecture",
            "used_by_yaml": "  - architecture-summary-generator\n  - onboarding-system",
        },
    }


def planned_workspace_paths(config: WorkspaceConfig, project_root: Path) -> list[Path]:
    """Return the ordered list of directories and files the generator manages."""

    paths: list[Path] = []
    for directory in BASE_AI_DIRECTORIES:
        paths.append(project_root / directory)

    for directory in documentation_directories(config):
        paths.append(project_root / directory)

    for relative_path in file_templates_for_config(config):
        paths.append(project_root / relative_path)

    for index_name in INDEX_CONTENT:
        paths.append(project_root / ".ai" / "indexes" / index_name)

    gitkeep_targets = {
        project_root / directory / ".gitkeep" for directory in empty_directories(config)
    }
    paths.extend(sorted(gitkeep_targets))
    return paths


def _write_yaml(path: Path, data: dict[str, Any], overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise WorkspaceError(f"Refusing to overwrite existing file: {path}")
    with path.open("w", encoding="utf-8") as handle:
        yaml_writer.dump(data, handle)


def generate_workspace(
    config: WorkspaceConfig, project_root: Path, force: bool = False
) -> list[Path]:
    """Generate the `.ai/` scaffold and docs structure for a project."""

    scaffold_root = workspace_scaffold_root(project_root)
    if scaffold_root.exists() and not force:
        raise WorkspaceError(
            f"Workspace context already exists at {scaffold_root}. Re-run with --force."
        )

    created_paths: list[Path] = []
    for directory in BASE_AI_DIRECTORIES:
        path = project_root / directory
        ensure_directory(path)
        created_paths.append(path)

    for directory in documentation_directories(config):
        path = project_root / directory
        ensure_directory(path)
        created_paths.append(path)

    context = build_template_context(config)
    for relative_path, template in file_templates_for_config(config).items():
        path = project_root / relative_path
        if path.name == "architecture-overview.md":
            context["doc"]["title"] = "Architecture Overview"
            context["doc"]["purpose"] = "Describe the system architecture for human and AI readers"
        elif path.name == "getting-started.md":
            context["doc"]["title"] = "Getting Started"
            context["doc"]["purpose"] = "Help new contributors begin working in the project"
        content = render(template, context).rstrip() + "\n"
        write_file(path, content, overwrite=force)
        created_paths.append(path)

    timestamp = context["timestamp"]
    for index_name, payload in INDEX_CONTENT.items():
        path = project_root / ".ai" / "indexes" / index_name
        _write_yaml(path, {**payload, "generated_at": timestamp}, overwrite=force)
        created_paths.append(path)

    for directory in empty_directories(config):
        gitkeep = project_root / directory / ".gitkeep"
        if not gitkeep.exists() or force:
            write_file(gitkeep, "", overwrite=force)
            created_paths.append(gitkeep)

    return created_paths
