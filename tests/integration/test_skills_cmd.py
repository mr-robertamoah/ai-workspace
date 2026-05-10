"""Integration tests for skills CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ai_workspace.cli.main import app
from ai_workspace.intelligence.skills import ensure_builtin_skills

runner = CliRunner()


def _global_root(tmp_path: Path) -> Path:
    ensure_builtin_skills(tmp_path)
    return tmp_path


def test_skills_list_exits_0_and_shows_builtins(tmp_path):
    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        ensure_builtin_skills(tmp_path)
        result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0, result.output
    assert "python-package" in result.output


def test_skills_search_terraform(tmp_path):
    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        ensure_builtin_skills(tmp_path)
        result = runner.invoke(app, ["skills", "search", "terraform"])
    assert result.exit_code == 0
    assert "terraform-module" in result.output


def test_skills_search_no_match(tmp_path):
    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        ensure_builtin_skills(tmp_path)
        result = runner.invoke(app, ["skills", "search", "zzznomatch"])
    assert result.exit_code == 0
    assert "No skills found" in result.output


def test_skills_show_python_package(tmp_path):
    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        ensure_builtin_skills(tmp_path)
        result = runner.invoke(app, ["skills", "show", "python-package"])
    assert result.exit_code == 0
    assert "python-package" in result.output


def test_skills_show_unknown_exits_nonzero(tmp_path):
    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        ensure_builtin_skills(tmp_path)
        result = runner.invoke(app, ["skills", "show", "ghost-skill"])
    assert result.exit_code != 0


def test_skills_list_shows_proposed_when_present(tmp_path):
    ensure_builtin_skills(tmp_path)
    proposed = tmp_path / "skills" / "my-skill-proposed"
    proposed.mkdir(parents=True)
    (proposed / "skill.yaml").write_text(
        "name: my-skill\nversion: '1.0.0'\ndescription: test\ntags: []\n"
    )
    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0
    assert "my-skill" in result.output
