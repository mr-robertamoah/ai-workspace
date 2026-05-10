"""Workspace index building hooks."""

from __future__ import annotations

from pathlib import Path


def workspace_index_root(project_root: Path) -> Path:
    """Return the directory where workspace indexes will live."""

    return project_root / ".ai" / "indexes"
