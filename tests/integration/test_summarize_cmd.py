"""Integration tests for the `summarize` CLI command."""

from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from ai_workspace.cli.main import app

runner = CliRunner()

PYTHON_API = Path(__file__).parent.parent / "fixtures" / "python-api"


def _setup(tmp_path: Path) -> None:
    shutil.copytree(PYTHON_API, tmp_path, dirs_exist_ok=True)
    # Need .ai/ to exist for find_project_root
    (tmp_path / ".ai").mkdir(exist_ok=True)
    (tmp_path / ".ai" / "generated").mkdir(exist_ok=True)


def test_summarize_exits_0_and_produces_files(tmp_path):
    _setup(tmp_path)
    result = runner.invoke(
        app, ["summarize", "--root" if False else "summarize"], catch_exceptions=False
    )
    # invoke from tmp_path via env
    import os

    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["summarize"], catch_exceptions=False)
    finally:
        os.chdir(old)
    assert result.exit_code == 0, result.output
    assert (tmp_path / ".ai" / "generated" / "repo-map-generated.md").exists()


def test_summarize_dry_run_creates_no_files(tmp_path):
    _setup(tmp_path)
    import os

    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["summarize", "--dry-run"], catch_exceptions=False)
    finally:
        os.chdir(old)
    assert result.exit_code == 0
    assert not (tmp_path / ".ai" / "generated" / "repo-map-generated.md").exists()


def test_summarize_outside_workspace_exits_nonzero(tmp_path):
    import os

    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["summarize"])
    finally:
        os.chdir(old)
    assert result.exit_code != 0


def test_summarize_output_lists_generated_paths(tmp_path):
    _setup(tmp_path)
    import os

    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(app, ["summarize"], catch_exceptions=False)
    finally:
        os.chdir(old)
    assert result.exit_code == 0
    assert "repo-map-generated.md" in result.output or "generated" in result.output
