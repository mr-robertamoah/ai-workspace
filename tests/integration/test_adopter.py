"""Integration tests for the adoption workflow."""

from __future__ import annotations

import shutil
from pathlib import Path

from ruamel.yaml import YAML

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.workspace.adopter import adopt_project

yaml = YAML()

PYTHON_API = Path(__file__).parent.parent / "fixtures" / "python-api"
NO_DOCS = Path(__file__).parent.parent / "fixtures" / "no-docs"


def _copy_fixture(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True)


def test_adopt_python_api_creates_ai_dir(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    adopt_project(tmp_path, config)
    assert (tmp_path / ".ai").is_dir()
    assert (tmp_path / ".ai" / "generated" / "tech-detection.yaml").exists()


def test_tech_detection_yaml_contains_python(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    adopt_project(tmp_path, config)
    with (tmp_path / ".ai" / "generated" / "tech-detection.yaml").open() as fh:
        data = yaml.load(fh)
    assert "python" in data["languages"]
    assert "fastapi" in data["frameworks"]


def test_start_here_mentions_detected_language(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    adopt_project(tmp_path, config)
    content = (tmp_path / ".ai" / "start-here.md").read_text()
    assert "python" in content.lower()


def test_suggested_docs_for_framework_project(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    result = adopt_project(tmp_path, config)
    # fastapi detected → architecture-overview.md should be suggested
    assert any("architecture-overview" in s for s in result.suggested_docs)


def test_adopt_no_docs_fixture_no_errors(tmp_path):
    _copy_fixture(NO_DOCS, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    result = adopt_project(tmp_path, config)
    assert result is not None


def test_adoption_idempotent_with_force(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    adopt_project(tmp_path, config)
    adopt_project(tmp_path, config, force=True)  # must not raise


def test_no_files_outside_ai_created(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    result = adopt_project(tmp_path, config)
    for p in result.files_created:
        rel = p.relative_to(tmp_path)
        parts = rel.parts
        assert parts[0] in (".ai", "docs"), f"Unexpected file outside .ai/docs: {p}"


def test_repo_map_generated(tmp_path):
    _copy_fixture(PYTHON_API, tmp_path)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    adopt_project(tmp_path, config)
    repo_map = tmp_path / ".ai" / "generated" / "repo-map-generated.md"
    assert repo_map.exists()
    content = repo_map.read_text()
    assert "src" in content or "requirements" in content
