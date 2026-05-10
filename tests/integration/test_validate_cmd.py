"""Integration tests for validate and validate security commands."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ai_workspace.cli.main import app

runner = CliRunner()
GREENFIELD = Path(__file__).parent.parent / "fixtures" / "greenfield"


def _init(tmp_path: Path) -> None:
    shutil.copytree(GREENFIELD, tmp_path, dirs_exist_ok=True)
    from ai_workspace.core.config import load_workspace_yaml
    from ai_workspace.workspace.generator import generate_workspace

    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    generate_workspace(config, tmp_path)


def _run_in(args: list[str], cwd: Path):
    old = os.getcwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, args)
    finally:
        os.chdir(old)


def test_validate_on_valid_workspace_exits_0(tmp_path):
    _init(tmp_path)
    result = _run_in(["validate"], tmp_path)
    assert result.exit_code == 0, result.output


def test_validate_missing_start_here_exits_1(tmp_path):
    _init(tmp_path)
    (tmp_path / ".ai" / "start-here.md").unlink()
    result = _run_in(["validate"], tmp_path)
    assert result.exit_code == 1


def test_validate_security_on_clean_workspace_exits_0(tmp_path):
    _init(tmp_path)
    result = _run_in(["validate", "security"], tmp_path)
    assert result.exit_code == 0, result.output


def test_validate_security_with_secret_exits_1(tmp_path):
    _init(tmp_path)
    (tmp_path / ".ai" / "notes.md").write_text("key = AKIAIOSFODNN7EXAMPLE123456\n")
    result = _run_in(["validate", "security"], tmp_path)
    assert result.exit_code == 1


def test_validate_prints_rich_table(tmp_path):
    _init(tmp_path)
    result = _run_in(["validate"], tmp_path)
    assert "workspace.yaml" in result.output


def test_validate_security_prints_rich_table(tmp_path):
    _init(tmp_path)
    result = _run_in(["validate", "security"], tmp_path)
    assert "passed" in result.output or "Security" in result.output


def test_validate_security_exits_0_when_external_tools_absent(tmp_path):
    _init(tmp_path)
    with patch("ai_workspace.security.scanner._run", return_value=(-1, "", "not installed")):
        result = _run_in(["validate", "security"], tmp_path)
    assert result.exit_code == 0, result.output
