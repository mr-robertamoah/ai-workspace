"""Filesystem helpers used across the workspace CLI."""

from __future__ import annotations

from pathlib import Path

from ai_workspace.core.errors import WorkspaceError


def ensure_directory(path: Path) -> None:
    """Create a directory tree if it does not already exist."""

    path.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str, overwrite: bool = False) -> None:
    """Write a file, protecting existing files unless overwrite is enabled."""

    if path.exists() and not overwrite:
        raise WorkspaceError(f"Refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_file(path: Path) -> str:
    """Read a file and convert missing-file errors into WorkspaceError."""

    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise WorkspaceError(f"File not found: {path}") from exc


def file_exists(path: Path) -> bool:
    """Return True when the path exists and is a file."""

    return path.is_file()


def directory_exists(path: Path) -> bool:
    """Return True when the path exists and is a directory."""

    return path.is_dir()
