"""Workspace summarization hooks."""

from __future__ import annotations

from pathlib import Path


def summary_output_path(project_root: Path) -> Path:
    """Return the default path for a generated project summary."""

    return project_root / ".ai" / "summaries" / "project-summary.md"
