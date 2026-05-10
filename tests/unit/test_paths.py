from __future__ import annotations

from pathlib import Path

import pytest

from ai_workspace.core.errors import SecurityError, WorkspaceNotFoundError
from ai_workspace.core.paths import (
    find_project_root,
    global_layer_path,
    safe_path,
    workspace_context_path,
)


def test_safe_path_allows_normal_relative_path(tmp_path: Path) -> None:
    resolved = safe_path(tmp_path, "docs/readme.md")

    assert resolved == (tmp_path / "docs/readme.md").resolve(strict=False)


@pytest.mark.parametrize("user_input", ["../../etc/passwd", "../sibling"])
def test_safe_path_blocks_traversal_attempts(tmp_path: Path, user_input: str) -> None:
    with pytest.raises(SecurityError):
        safe_path(tmp_path, user_input)


def test_safe_path_blocks_absolute_path_outside_base(tmp_path: Path) -> None:
    with pytest.raises(SecurityError):
        safe_path(tmp_path, "/etc/passwd")


def test_global_layer_path_returns_expected_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))

    path = global_layer_path()

    assert path == tmp_path / ".ai-workspace"
    assert path.is_dir()


def test_workspace_context_path_returns_dot_ai_path(tmp_path: Path) -> None:
    assert workspace_context_path(tmp_path) == tmp_path / ".ai"


def test_find_project_root_finds_workspace_yaml_two_levels_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    nested = project_root / "src" / "app"
    nested.mkdir(parents=True)
    (project_root / "workspace.yaml").write_text("workspace: {}\n", encoding="utf-8")

    monkeypatch.chdir(nested)

    assert find_project_root() == project_root.resolve(strict=False)


def test_find_project_root_raises_when_no_markers_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(WorkspaceNotFoundError):
        find_project_root()
