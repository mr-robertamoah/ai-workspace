"""Tests for the six review fixes."""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ai_workspace.cli.main import app
from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.intelligence.skills import ensure_builtin_skills, propose_skill, SkillMetadata
from ai_workspace.workspace.handoff import HandoffData, generate_handoff

runner = CliRunner()
GREENFIELD = Path(__file__).parent.parent / "fixtures" / "greenfield"
_DATA_STANDARDS = (
    Path(__file__).parent.parent.parent / "src" / "ai_workspace" / "data" / "standards"
)


def _init(tmp_path: Path) -> None:
    shutil.copytree(GREENFIELD, tmp_path, dirs_exist_ok=True)
    from ai_workspace.workspace.generator import generate_workspace

    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    generate_workspace(config, tmp_path)


# --- Fix 1: standards has sensible defaults ---


def test_workspace_yaml_without_standards_block_loads_ok(tmp_path):
    """workspace.yaml omitting standards should load with defaults, not raise."""
    (tmp_path / "workspace.yaml").write_text(
        "workspace:\n  name: test-app\n  type: single\nlanguage:\n  primary: python\n"
    )
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    assert config.standards.testing == "pytest"
    assert config.standards.formatting == "black"
    assert config.standards.linting == "ruff"


def test_workspace_yaml_without_architecture_block_loads_ok(tmp_path):
    """workspace.yaml omitting architecture should load with a default, not raise."""
    (tmp_path / "workspace.yaml").write_text(
        "workspace:\n  name: test-app\n  type: single\nlanguage:\n  primary: python\n"
    )
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    assert config.architecture is not None


# --- Fix 2: skills accept CLI command ---


def test_skills_accept_command_exists(tmp_path):
    """skills accept should rename <name>-proposed/ to <name>/."""
    ensure_builtin_skills(tmp_path)
    meta = SkillMetadata(name="my-test-skill", description="test", tags=[])
    propose_skill(tmp_path, meta)
    assert (tmp_path / "skills" / "my-test-skill-proposed").exists()

    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        result = runner.invoke(app, ["skills", "accept", "my-test-skill"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "skills" / "my-test-skill").exists()
    assert not (tmp_path / "skills" / "my-test-skill-proposed").exists()


def test_skills_accept_unknown_exits_nonzero(tmp_path):
    ensure_builtin_skills(tmp_path)
    with patch("ai_workspace.cli.skills_cmd.global_layer_path", return_value=tmp_path):
        result = runner.invoke(app, ["skills", "accept", "ghost-skill"])
    assert result.exit_code != 0


# --- Fix 3: _update_docs_index warns instead of silently failing ---


def test_docs_create_warns_on_corrupt_index(tmp_path):
    """If docs-index.yaml is corrupt, docs create should warn, not silently fail."""
    _init(tmp_path)
    (tmp_path / ".ai" / "indexes" / "docs-index.yaml").write_text("{{invalid yaml:")
    import os

    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["docs", "create", "adr", "--title", "Test Decision"])
    finally:
        os.chdir(old)
    # File should still be created
    assert result.exit_code == 0
    # Warning should appear in output
    assert "WARN" in result.output or "warn" in result.output.lower()


# --- Fix 4: standards callback no longer says "Not yet implemented" ---


def test_standards_callback_does_not_say_not_implemented(tmp_path):
    with patch("ai_workspace.cli.standards_cmd.global_layer_path", return_value=tmp_path):
        result = runner.invoke(app, ["standards"])
    assert "Not yet implemented" not in result.output
    assert result.exit_code == 0


# --- Fix 5: handoff includes files_modified and decisions_made ---


def test_handoff_includes_files_modified_and_decisions(tmp_path):
    _init(tmp_path)
    data = HandoffData(
        accomplished="Built feature X",
        current_state="Tests passing",
        blockers="None",
        next_steps="Deploy",
        tests_passing=True,
        files_modified="src/main.py, tests/test_main.py",
        decisions_made="Chose SQLite over PostgreSQL for local dev",
    )
    path = generate_handoff(tmp_path, data)
    content = path.read_text()
    assert "src/main.py" in content
    assert "SQLite" in content


def test_handoff_default_values_are_not_empty_placeholders(tmp_path):
    _init(tmp_path)
    data = HandoffData(
        accomplished="done",
        current_state="good",
        blockers="none",
        next_steps="next",
        tests_passing=True,
    )
    path = generate_handoff(tmp_path, data)
    content = path.read_text()
    # Should not have raw "(Fill in ...)" placeholders
    assert "(Fill in" not in content
