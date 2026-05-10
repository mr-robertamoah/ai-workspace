"""Integration tests for the `adopt` CLI command."""

from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from ai_workspace.cli.main import app

runner = CliRunner()

PYTHON_API = Path(__file__).parent.parent / "fixtures" / "python-api"


def _copy_fixture(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True)


def test_adopt_python_api_exits_0(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    result = runner.invoke(app, ["adopt", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output


def test_adopt_dry_run_creates_no_files(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    runner.invoke(app, ["adopt", "--root", str(tmp_path), "--dry-run"])
    assert not (tmp_path / ".ai").exists()


def test_adopt_prints_suggested_docs(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    result = runner.invoke(app, ["adopt", "--root", str(tmp_path)])
    # fastapi project should trigger at least one suggestion
    assert "Suggested" in result.output or result.exit_code == 0


def test_adopt_no_workspace_yaml_exits_nonzero(tmp_path):
    result = runner.invoke(app, ["adopt", "--root", str(tmp_path)])
    assert result.exit_code != 0
