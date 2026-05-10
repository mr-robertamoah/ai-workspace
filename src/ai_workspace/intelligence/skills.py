"""Skill discovery and governance hooks."""

from __future__ import annotations

from pathlib import Path


def proposed_skill_path(global_root: Path, skill_name: str) -> Path:
    """Return the path where an AI-proposed skill would be created."""

    return global_root / "skills" / f"{skill_name}-proposed"
