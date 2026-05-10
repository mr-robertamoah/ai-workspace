"""Path helpers with traversal protection."""

from __future__ import annotations

from pathlib import Path

from ai_workspace.core.errors import SecurityError, WorkspaceNotFoundError


def safe_path(base: Path, user_input: str) -> Path:
    """Resolve a user-supplied path under a trusted base directory."""

    base_resolved = base.resolve(strict=False)
    candidate = Path(user_input).expanduser()
    if not candidate.is_absolute():
        candidate = base_resolved / candidate

    resolved = candidate.resolve(strict=False)
    if not resolved.is_relative_to(base_resolved):
        raise SecurityError(
            f"Path '{user_input}' escapes the allowed base directory '{base_resolved}'."
        )
    return resolved


def global_layer_path() -> Path:
    """Return the global intelligence layer path, creating it when missing."""

    path = Path.home() / ".ai-workspace"
    path.mkdir(parents=True, exist_ok=True)
    return path


def workspace_context_path(project_root: Path) -> Path:
    """Return the workspace context path for a project root."""

    return project_root / ".ai"


def find_project_root() -> Path:
    """Find the nearest ancestor directory containing a workspace marker."""

    current = Path.cwd().resolve(strict=False)
    for candidate in (current, *current.parents):
        if (candidate / "workspace.yaml").exists() or (candidate / ".ai").exists():
            return candidate

    raise WorkspaceNotFoundError(f"No workspace markers found from '{current}' upward.")
