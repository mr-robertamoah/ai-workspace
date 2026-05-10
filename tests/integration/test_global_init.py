"""Integration tests for global layer auto-initialization."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ai_workspace.cli.main import app

runner = CliRunner()


def _invoke_with_home(fake_home: Path) -> None:
    """Invoke a command with a patched home directory."""
    fake_global = fake_home / ".ai-workspace"
    with (
        patch("ai_workspace.cli.main._home", side_effect=lambda: fake_home),
        patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=fake_global),
    ):
        runner.invoke(app, ["skills", "list"])


def test_global_layer_created_on_first_command(tmp_path):
    global_root = tmp_path / ".ai-workspace"
    assert not global_root.exists()
    _invoke_with_home(tmp_path)
    assert global_root.exists()


def test_builtin_skills_present_after_init(tmp_path):
    _invoke_with_home(tmp_path)
    skills = list((tmp_path / ".ai-workspace" / "skills").iterdir())
    assert len(skills) >= 5


def test_config_yaml_exists_after_init(tmp_path):
    _invoke_with_home(tmp_path)
    config = tmp_path / ".ai-workspace" / "config.yaml"
    assert config.exists()
    from ruamel.yaml import YAML

    data = YAML(typ="safe").load(config.read_text())
    assert "version" in data


def test_global_indexes_written_after_init(tmp_path):
    _invoke_with_home(tmp_path)
    index = tmp_path / ".ai-workspace" / "indexes" / "skills-index.yaml"
    assert index.exists()
    from ruamel.yaml import YAML

    data = YAML(typ="safe").load(index.read_text())
    assert "skills" in data
