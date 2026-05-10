"""Documentation creation hooks."""

from __future__ import annotations

from pathlib import Path


def docs_root(project_root: Path) -> Path:
    """Return the project documentation root."""

    return project_root / "docs"
