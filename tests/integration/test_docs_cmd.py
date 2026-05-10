"""Integration tests for docs templates and docs create commands."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

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


def _run(args, cwd):
    old = os.getcwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old)


def test_docs_templates_exits_0_and_lists_five(tmp_path):
    _init(tmp_path)
    result = _run(["docs", "templates"], tmp_path)
    assert result.exit_code == 0
    for name in ["architecture-overview", "adr", "runbook", "onboarding", "api-reference"]:
        assert name in result.output


def test_docs_create_architecture_overview(tmp_path):
    _init(tmp_path)
    # generator already creates architecture-overview.md, so use --force
    result = _run(["docs", "create", "architecture-overview", "--force"], tmp_path)
    assert result.exit_code == 0
    assert (tmp_path / "docs" / "architecture" / "architecture-overview.md").exists()


def test_docs_create_adr_auto_increments(tmp_path):
    _init(tmp_path)
    result = _run(["docs", "create", "adr", "--title", "Use PostgreSQL"], tmp_path)
    assert result.exit_code == 0
    decisions = list((tmp_path / "docs" / "decisions").glob("ADR-001-*.md"))
    assert decisions

    result2 = _run(["docs", "create", "adr", "--title", "Use Redis"], tmp_path)
    assert result2.exit_code == 0
    decisions2 = list((tmp_path / "docs" / "decisions").glob("ADR-002-*.md"))
    assert decisions2


def test_docs_create_twice_without_force_exits_nonzero(tmp_path):
    _init(tmp_path)
    # architecture-overview already exists from init; creating without --force should fail
    result = _run(["docs", "create", "architecture-overview"], tmp_path)
    assert result.exit_code != 0


def test_created_files_contain_valid_yaml_front_matter(tmp_path):
    _init(tmp_path)
    _run(["docs", "create", "architecture-overview"], tmp_path)
    content = (tmp_path / "docs" / "architecture" / "architecture-overview.md").read_text()
    assert content.startswith("---")
    assert "title:" in content


def test_docs_index_updated_after_create(tmp_path):
    _init(tmp_path)
    _run(["docs", "create", "architecture-overview", "--force"], tmp_path)
    from ruamel.yaml import YAML

    index = YAML(typ="safe").load((tmp_path / ".ai" / "indexes" / "docs-index.yaml").read_text())
    paths = [d["path"] for d in index.get("docs", [])]
    assert any("architecture-overview" in p for p in paths)
