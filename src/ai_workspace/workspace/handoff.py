"""Workspace handoff generation hooks."""

from __future__ import annotations

from pathlib import Path


def handoff_output_path(project_root: Path) -> Path:
    """Return the default path for a generated handoff document."""

    return project_root / ".ai" / "handoffs" / "latest.md"
