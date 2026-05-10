from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from ai_workspace.cli.main import app
from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.workspace.generator import generate_workspace

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]


def copy_fixture(name: str, tmp_path: Path) -> Path:
    source = REPO_ROOT / "tests" / "fixtures" / name
    destination = tmp_path / name
    shutil.copytree(source, destination)
    return destination


def prepare_workspace(tmp_path: Path) -> Path:
    project_root = copy_fixture("python-api", tmp_path)
    config = load_workspace_yaml(project_root / "workspace.yaml")
    generate_workspace(config, project_root)
    return project_root


def test_index_rebuild_in_fixture_directory_exits_zero(tmp_path: Path, monkeypatch) -> None:
    project_root = prepare_workspace(tmp_path)
    monkeypatch.chdir(project_root)

    result = runner.invoke(app, ["index", "rebuild"], prog_name="ai-workspace")

    assert result.exit_code == 0


def test_index_rebuild_produces_rich_table_in_output(tmp_path: Path, monkeypatch) -> None:
    project_root = prepare_workspace(tmp_path)
    monkeypatch.chdir(project_root)

    result = runner.invoke(app, ["index", "rebuild"], prog_name="ai-workspace")

    assert "Index Rebuild Summary" in result.output
    assert "docs-index.yaml" in result.output


def test_index_rebuild_outside_workspace_exits_non_zero(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["index", "rebuild"], prog_name="ai-workspace")

    assert result.exit_code != 0
    assert "[ERROR]" in result.output
