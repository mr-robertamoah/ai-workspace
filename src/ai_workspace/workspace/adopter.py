"""Existing-project adoption hooks."""

from __future__ import annotations

from pathlib import Path


def adoption_report_path(project_root: Path) -> Path:
    """Return the default path for an adoption report artifact."""

    return project_root / ".ai" / "adoption-report.md"
