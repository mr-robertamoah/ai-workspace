"""Standards resolution: global defaults + workspace-level overrides (append model)."""

from __future__ import annotations

from pathlib import Path

from ai_workspace.core.bundle import data_path

_BUILTIN = data_path("standards")
_GLOBAL_SUBDIR = "standards"
_WORKSPACE_SUBDIR = ".ai/standards"


def _global_root() -> Path:
    from ai_workspace.core.paths import global_layer_path

    return global_layer_path()


def list_standard_names(global_root: Path | None = None) -> list[str]:
    """Return names of all available standards (from global layer)."""
    root = global_root or _global_root()
    standards_dir = root / _GLOBAL_SUBDIR
    if not standards_dir.is_dir():
        return []
    return sorted(p.stem for p in standards_dir.glob("*.md"))


def get_standard(
    name: str, project_root: Path | None = None, global_root: Path | None = None
) -> str:
    """Return the effective standard content for *name*.

    Resolution order:
    1. Global standard (base)
    2. Workspace override appended (if .ai/standards/<name>.md exists)

    If neither exists, raises FileNotFoundError.
    """
    g_root = global_root or _global_root()
    global_file = g_root / _GLOBAL_SUBDIR / f"{name}.md"

    if not global_file.exists():
        raise FileNotFoundError(f"No standard named '{name}' found in global layer.")

    content = global_file.read_text(encoding="utf-8")

    if project_root:
        workspace_file = project_root / _WORKSPACE_SUBDIR / f"{name}.md"
        if workspace_file.exists():
            override = workspace_file.read_text(encoding="utf-8").strip()
            if override:
                content = content.rstrip() + "\n\n---\n\n## Project Overrides\n\n" + override + "\n"

    return content


def effective_standards(
    project_root: Path | None = None, global_root: Path | None = None
) -> list[dict]:
    """Return metadata for all standards, annotated with override status."""
    g_root = global_root or _global_root()
    results = []
    for name in list_standard_names(g_root):
        has_override = False
        if project_root:
            has_override = (project_root / _WORKSPACE_SUBDIR / f"{name}.md").exists()
        results.append({"name": name, "source": "global", "has_override": has_override})
    return results
