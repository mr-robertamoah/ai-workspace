"""Index-building placeholders for the global intelligence layer."""

from __future__ import annotations


def index_filenames() -> list[str]:
    """Return the expected index filenames for the global layer."""

    return [
        "skills-index.yaml",
        "standards-index.yaml",
        "templates-index.yaml",
        "tags-index.yaml",
    ]
