"""Workspace index rebuilding."""

from __future__ import annotations

import re
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ai_workspace.core.config import WorkspaceConfig
from ai_workspace.core.index_schemas import (
    AdrIndex,
    AdrIndexEntry,
    DocsIndex,
    DocsIndexEntry,
    RepoIndex,
    RepoIndexEntry,
    RepoKeyDirectoryEntry,
    TaskIndex,
    TaskIndexEntry,
    load_index,
    write_index,
)

yaml = YAML(typ="safe")


def workspace_index_root(project_root: Path) -> Path:
    """Return the directory where workspace indexes will live."""

    return project_root / ".ai" / "indexes"


def _iso_mtime(path: Path) -> str:
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_front_matter(path: Path) -> tuple[dict[str, object], str]:
    text = _read_text(path)
    if not text.startswith("---\n"):
        return {}, text

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text

    try:
        front_matter = yaml.load(parts[1]) or {}
    except YAMLError:
        front_matter = {}
    return front_matter, parts[2]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _title_from_filename(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").title()


def _summary_from_body(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _doc_id(path: Path) -> str:
    return _slug(path.stem)


def _detect_language(repo_root: Path) -> str:
    if (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
        return "python"
    if (repo_root / "package.json").exists():
        return "typescript"
    if (repo_root / "go.mod").exists():
        return "go"
    if (repo_root / "Cargo.toml").exists():
        return "rust"
    if (repo_root / "pom.xml").exists() or (repo_root / "build.gradle").exists():
        return "java"
    if list(repo_root.rglob("*.tf")):
        return "other"
    return "other"


def _entry_points(project_root: Path, repo_root: Path) -> list[str]:
    candidates = [
        repo_root / "src" / "main.py",
        repo_root / "main.py",
        repo_root / "src" / "main.ts",
        repo_root / "main.ts",
        repo_root / "cmd" / "main.go",
        repo_root / "main.go",
    ]
    return [str(path.relative_to(project_root)) for path in candidates if path.exists()]


def _key_directories(project_root: Path, repo_root: Path) -> list[RepoKeyDirectoryEntry]:
    purposes = {
        "src": "Application source",
        "tests": "Test suite",
        "test": "Test suite",
        "docs": "Project documentation",
    }
    entries: list[RepoKeyDirectoryEntry] = []
    for name, purpose in purposes.items():
        path = repo_root / name
        if path.is_dir():
            entries.append(
                RepoKeyDirectoryEntry(path=str(path.relative_to(project_root)), purpose=purpose)
            )
    return entries


def _repo_purpose(repo_root: Path) -> str:
    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            project_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            description = project_data.get("project", {}).get("description")
            if description:
                return str(description)
        except tomllib.TOMLDecodeError:
            pass
    return f"Repository at {repo_root.name}"


def _build_docs_index(project_root: Path) -> int:
    docs_root = project_root / "docs"
    entries: list[DocsIndexEntry] = []
    if docs_root.exists():
        for path in sorted(docs_root.rglob("*.md")):
            front_matter, body = _parse_front_matter(path)
            relative_path = str(path.relative_to(project_root))
            entry = DocsIndexEntry(
                id=_doc_id(path.relative_to(docs_root)),
                title=str(front_matter.get("title") or _title_from_filename(path)),
                path=relative_path,
                tags=[str(tag) for tag in front_matter.get("tags", [])],
                purpose=str(front_matter.get("purpose") or "Project documentation"),
                last_modified=_iso_mtime(path),
                summary=str(front_matter.get("summary") or _summary_from_body(body)),
            )
            entries.append(entry)

    write_index(
        workspace_index_root(project_root) / "docs-index.yaml",
        DocsIndex(generated_at="", docs=entries),
    )
    return len(entries)


def _build_adr_index(project_root: Path) -> int:
    decisions_root = project_root / "docs" / "decisions"
    entries: list[AdrIndexEntry] = []
    if decisions_root.exists():
        for path in sorted(decisions_root.glob("ADR-*.md")):
            front_matter, _body = _parse_front_matter(path)
            adr_id = path.stem.split("-", 2)
            entry = AdrIndexEntry(
                id="-".join(adr_id[:2]) if len(adr_id) >= 2 else path.stem,
                title=str(front_matter.get("title") or _title_from_filename(path)),
                path=str(path.relative_to(project_root)),
                status=str(front_matter.get("status") or "proposed"),
                date=str(front_matter.get("date") or ""),
                tags=[str(tag) for tag in front_matter.get("tags", [])],
                superseded_by=(
                    str(front_matter["superseded_by"])
                    if front_matter.get("superseded_by") is not None
                    else None
                ),
            )
            entries.append(entry)

    write_index(
        workspace_index_root(project_root) / "adr-index.yaml",
        AdrIndex(generated_at="", adrs=entries),
    )
    return len(entries)


def _build_task_index(project_root: Path) -> int:
    task_path = project_root / ".ai" / "active-task" / "current-task.md"
    entries: list[TaskIndexEntry] = []
    if task_path.exists():
        text = _read_text(task_path).strip()
        if text:
            title = "Current Task"
            for line in text.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            entries.append(
                TaskIndexEntry(
                    id="TASK-001",
                    title=title,
                    status="active",
                    started_at=_iso_mtime(task_path),
                    completed_at=None,
                    path=str(task_path.relative_to(project_root)),
                    tags=[],
                )
            )

    write_index(
        workspace_index_root(project_root) / "task-index.yaml",
        TaskIndex(generated_at="", tasks=entries),
    )
    return len(entries)


def _build_repo_index(project_root: Path, config: WorkspaceConfig) -> int:
    entries: list[RepoIndexEntry] = []
    for repository in config.repositories:
        repo_root = project_root / repository.path
        entries.append(
            RepoIndexEntry(
                name=repository.name,
                path=repository.path,
                language=_detect_language(repo_root),
                purpose=_repo_purpose(repo_root),
                entry_points=_entry_points(project_root, repo_root),
                key_directories=_key_directories(project_root, repo_root),
            )
        )

    write_index(
        workspace_index_root(project_root) / "repo-index.yaml",
        RepoIndex(generated_at="", repositories=entries),
    )
    return len(entries)


def rebuild_all_indexes(project_root: Path, config: WorkspaceConfig) -> dict[str, int]:
    """Rebuild all local workspace indexes and return entry counts."""

    counts = {
        "docs-index.yaml": _build_docs_index(project_root),
        "adr-index.yaml": _build_adr_index(project_root),
        "task-index.yaml": _build_task_index(project_root),
        "repo-index.yaml": _build_repo_index(project_root, config),
    }

    # Validate that each written file is readable after the rebuild.
    load_index(workspace_index_root(project_root) / "docs-index.yaml", DocsIndex)
    load_index(workspace_index_root(project_root) / "adr-index.yaml", AdrIndex)
    load_index(workspace_index_root(project_root) / "task-index.yaml", TaskIndex)
    load_index(workspace_index_root(project_root) / "repo-index.yaml", RepoIndex)
    return counts
