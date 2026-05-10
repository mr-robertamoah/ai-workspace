"""Tests for the standards resolution system."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from ai_workspace.cli.main import app
from ai_workspace.intelligence.standards import (
    effective_standards,
    get_standard,
    list_standard_names,
)

runner = CliRunner()
GREENFIELD = Path(__file__).parent.parent / "fixtures" / "greenfield"
_DATA_STANDARDS = (
    Path(__file__).parent.parent.parent / "src" / "ai_workspace" / "data" / "standards"
)


@pytest.fixture()
def global_root(tmp_path):
    g = tmp_path / "global"
    g.mkdir()
    (g / "standards").mkdir()
    for src in _DATA_STANDARDS.glob("*.md"):
        shutil.copy2(src, g / "standards" / src.name)
    return g


@pytest.fixture()
def project_root(tmp_path):
    p = tmp_path / "project"
    shutil.copytree(GREENFIELD, p, dirs_exist_ok=True)
    from ai_workspace.core.config import load_workspace_yaml
    from ai_workspace.workspace.generator import generate_workspace

    config = load_workspace_yaml(p / "workspace.yaml")
    generate_workspace(config, p)
    return p


# --- Unit tests ---


def test_list_standard_names_returns_five(global_root):
    names = list_standard_names(global_root)
    assert len(names) == 5
    assert "python" in names


def test_get_standard_returns_content(global_root):
    content = get_standard("python", global_root=global_root)
    assert "# Python" in content or "python" in content.lower()


def test_get_standard_raises_for_unknown(global_root):
    with pytest.raises(FileNotFoundError):
        get_standard("nonexistent", global_root=global_root)


def test_get_standard_appends_workspace_override(global_root, project_root):
    override_dir = project_root / ".ai" / "standards"
    override_dir.mkdir(parents=True, exist_ok=True)
    (override_dir / "python.md").write_text("## Custom Rule\n\nAlways use walrus operator.\n")

    content = get_standard("python", project_root=project_root, global_root=global_root)
    assert "Project Overrides" in content
    assert "walrus operator" in content


def test_get_standard_without_override_returns_global_only(global_root, project_root):
    content = get_standard("python", project_root=project_root, global_root=global_root)
    assert "Project Overrides" not in content


def test_effective_standards_shows_override_flag(global_root, project_root):
    override_dir = project_root / ".ai" / "standards"
    override_dir.mkdir(parents=True, exist_ok=True)
    (override_dir / "python.md").write_text("## Custom\n\nRule.\n")

    rows = effective_standards(project_root=project_root, global_root=global_root)
    python_row = next(r for r in rows if r["name"] == "python")
    assert python_row["has_override"] is True

    terraform_row = next(r for r in rows if r["name"] == "terraform")
    assert terraform_row["has_override"] is False


# --- CLI integration tests ---


def test_standards_list_exits_0(global_root):
    with patch("ai_workspace.cli.standards_cmd.global_layer_path", return_value=global_root):
        result = runner.invoke(app, ["standards", "list"])
    assert result.exit_code == 0, result.output
    assert "python" in result.output


def test_standards_show_exits_0(global_root):
    with patch("ai_workspace.cli.standards_cmd.global_layer_path", return_value=global_root):
        result = runner.invoke(app, ["standards", "show", "python"])
    assert result.exit_code == 0
    assert "python" in result.output.lower()


def test_standards_show_unknown_exits_nonzero(global_root):
    with patch("ai_workspace.cli.standards_cmd.global_layer_path", return_value=global_root):
        result = runner.invoke(app, ["standards", "show", "nonexistent"])
    assert result.exit_code != 0


def test_standards_override_creates_file(global_root, project_root):
    import os

    old = os.getcwd()
    os.chdir(project_root)
    try:
        with patch("ai_workspace.cli.standards_cmd.global_layer_path", return_value=global_root):
            result = runner.invoke(app, ["standards", "override", "python"])
    finally:
        os.chdir(old)
    assert result.exit_code == 0
    assert (project_root / ".ai" / "standards" / "python.md").exists()


def test_standards_show_includes_override_content(global_root, project_root):
    override_dir = project_root / ".ai" / "standards"
    override_dir.mkdir(parents=True, exist_ok=True)
    (override_dir / "python.md").write_text("## Custom\n\nAlways use walrus operator.\n")

    # Test the merge logic directly (unit level)
    from ai_workspace.intelligence.standards import get_standard as gs

    content = gs("python", project_root=project_root, global_root=global_root)
    assert "walrus operator" in content
    assert "Project Overrides" in content


def test_ai_standards_dir_created_by_init(tmp_path):
    shutil.copytree(GREENFIELD, tmp_path, dirs_exist_ok=True)
    from ai_workspace.core.config import load_workspace_yaml
    from ai_workspace.workspace.generator import generate_workspace

    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    generate_workspace(config, tmp_path)
    assert (tmp_path / ".ai" / "standards").is_dir()
