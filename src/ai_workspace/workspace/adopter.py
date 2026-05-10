"""Existing-project adoption: generate .ai/ context from a live repo."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ruamel.yaml import YAML

from ai_workspace.core.config import WorkspaceConfig
from ai_workspace.workspace.detector import DetectionResult, detect_project
from ai_workspace.workspace.generator import generate_workspace
from ai_workspace.workspace.index_builder import rebuild_all_indexes

yaml_writer = YAML()
yaml_writer.default_flow_style = False

_NOISE = {".git", "__pycache__", "node_modules", ".ai", "dist", "build", ".egg-info"}


@dataclass
class AdoptionResult:
    files_created: list[Path] = field(default_factory=list)
    suggested_docs: list[str] = field(default_factory=list)
    detection: DetectionResult = field(default_factory=DetectionResult)


def _repo_map(root: Path, max_depth: int = 2) -> str:
    """Return a simple Markdown directory tree (max_depth levels)."""

    lines = [f"# Repo Map: {root.name}\n"]

    def _walk(path: Path, depth: int, prefix: str) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return
        for entry in entries:
            if entry.name in _NOISE or entry.name.startswith("."):
                continue
            lines.append(f"{prefix}- {entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                _walk(entry, depth + 1, prefix + "  ")

    _walk(root, 1, "")
    return "\n".join(lines) + "\n"


def _detection_to_dict(d: DetectionResult) -> dict:
    return {
        "languages": d.languages,
        "frameworks": d.frameworks,
        "package_managers": d.package_managers,
        "ci_systems": d.ci_systems,
        "has_tests": d.has_tests,
        "has_docs": d.has_docs,
        "entry_points": [str(p) for p in d.entry_points],
        "config_files": [str(p) for p in d.config_files],
    }


def _suggest_docs(root: Path, detection: DetectionResult) -> list[str]:
    suggestions: list[str] = []
    if detection.has_tests and not (root / "docs/workflows/testing-strategy.md").exists():
        suggestions.append("docs/workflows/testing-strategy.md")
    if detection.frameworks and not (root / "docs/architecture/architecture-overview.md").exists():
        suggestions.append("docs/architecture/architecture-overview.md")
    if detection.ci_systems and not (root / "docs/workflows/deployment-workflow.md").exists():
        suggestions.append("docs/workflows/deployment-workflow.md")
    return suggestions


def adopt_project(root: Path, config: WorkspaceConfig, force: bool = False) -> AdoptionResult:
    """Adopt an existing project: detect, scaffold .ai/, populate context."""

    detection = detect_project(root)
    result = AdoptionResult(detection=detection)

    # Capture suggestion state BEFORE scaffold generation (files don't exist yet)
    suggested = _suggest_docs(root, detection)

    # Generate .ai/ scaffold first (force=True since adoption targets existing repos)
    created = generate_workspace(config, root, force=True)
    result.files_created.extend(created)

    # Write tech-detection.yaml (overwrite the template written by generator)
    tech_path = root / ".ai" / "generated" / "tech-detection.yaml"
    with tech_path.open("w", encoding="utf-8") as fh:
        yaml_writer.dump(_detection_to_dict(detection), fh)
    if tech_path not in result.files_created:
        result.files_created.append(tech_path)

    # Overwrite start-here.md with detection info
    start_here = root / ".ai" / "start-here.md"
    lang_summary = ", ".join(detection.languages) if detection.languages else "unknown"
    fw_summary = ", ".join(detection.frameworks) if detection.frameworks else "none detected"
    test_status = "yes" if detection.has_tests else "no"
    start_here.write_text(
        start_here.read_text(encoding="utf-8") + f"\n## Detected Stack\n\n"
        f"- Languages: {lang_summary}\n"
        f"- Frameworks: {fw_summary}\n"
        f"- Tests present: {test_status}\n",
        encoding="utf-8",
    )

    # Overwrite project-summary.md with detected technologies
    proj_summary = root / ".ai" / "project-summary.md"
    proj_summary.write_text(
        f"# Project Summary: {config.workspace.name}\n\n"
        f"## What This Project Is\n\n(Fill in a description)\n\n"
        f"## Tech Stack\n\n"
        f"- Languages: {lang_summary}\n"
        f"- Frameworks: {fw_summary}\n"
        f"- Package managers: {', '.join(detection.package_managers) or 'none'}\n"
        f"- CI: {', '.join(detection.ci_systems) or 'none'}\n\n"
        f"## Key Components\n\n(Fill in key components)\n",
        encoding="utf-8",
    )

    # Generate repo map
    repo_map_path = root / ".ai" / "generated" / "repo-map-generated.md"
    repo_map_path.write_text(_repo_map(root), encoding="utf-8")
    if repo_map_path not in result.files_created:
        result.files_created.append(repo_map_path)

    # Build initial indexes
    rebuild_all_indexes(root, config)

    result.suggested_docs = suggested
    return result
