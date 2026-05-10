"""Documentation template path helpers."""

from __future__ import annotations

from pathlib import Path


def docs_template_root(global_root: Path) -> Path:
    """Return the root directory for built-in documentation templates."""

    return global_root / "templates" / "docs"
