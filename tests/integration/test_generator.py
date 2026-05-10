from __future__ import annotations

from pathlib import Path

import pytest
from ruamel.yaml import YAML

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.core.errors import WorkspaceError
from ai_workspace.workspace.generator import generate_workspace

yaml = YAML(typ="safe")
REPO_ROOT = Path(__file__).resolve().parents[2]


def fixture_config(path: str) -> Path:
    return REPO_ROOT / path


def test_generating_into_empty_directory_creates_expected_structure(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))

    generate_workspace(config, tmp_path)

    assert (tmp_path / ".ai").is_dir()
    assert (tmp_path / ".ai" / "active-task").is_dir()
    assert (tmp_path / ".ai" / "indexes").is_dir()
    assert (tmp_path / "docs" / "architecture").is_dir()
    assert (tmp_path / "docs" / "decisions").is_dir()


def test_generating_creates_start_here_with_workspace_name(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))

    generate_workspace(config, tmp_path)

    content = (tmp_path / ".ai" / "start-here.md").read_text(encoding="utf-8")
    assert "greenfield-app" in content


def test_generating_creates_all_index_files(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))

    generate_workspace(config, tmp_path)

    for name in ["adr-index.yaml", "task-index.yaml", "docs-index.yaml", "repo-index.yaml"]:
        assert (tmp_path / ".ai" / "indexes" / name).is_file()


def test_minimal_documentation_creates_only_two_directories(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))
    config.documentation.structure = "minimal"

    generate_workspace(config, tmp_path)

    docs_dirs = sorted(path.name for path in (tmp_path / "docs").iterdir() if path.is_dir())
    assert docs_dirs == ["architecture", "decisions"]


def test_full_documentation_creates_all_eight_directories(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))
    config.documentation.structure = "full"

    generate_workspace(config, tmp_path)

    docs_dirs = sorted(path.name for path in (tmp_path / "docs").iterdir() if path.is_dir())
    assert docs_dirs == [
        "api",
        "architecture",
        "decisions",
        "infrastructure",
        "onboarding",
        "product",
        "runbooks",
        "workflows",
    ]


def test_generating_without_force_into_existing_ai_raises(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))
    (tmp_path / ".ai").mkdir()

    with pytest.raises(WorkspaceError, match="--force"):
        generate_workspace(config, tmp_path, force=False)


def test_generating_with_force_into_existing_ai_overwrites(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))

    generate_workspace(config, tmp_path)
    generate_workspace(config, tmp_path, force=True)

    assert (tmp_path / ".ai" / "start-here.md").is_file()


def test_all_created_index_files_are_valid_yaml(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))

    generate_workspace(config, tmp_path)

    for name in ["adr-index.yaml", "task-index.yaml", "docs-index.yaml", "repo-index.yaml"]:
        with (tmp_path / ".ai" / "indexes" / name).open(encoding="utf-8") as handle:
            assert yaml.load(handle) is not None


def test_start_here_contains_mandatory_sections(tmp_path: Path) -> None:
    config = load_workspace_yaml(fixture_config("tests/fixtures/greenfield/workspace.yaml"))

    generate_workspace(config, tmp_path)

    content = (tmp_path / ".ai" / "start-here.md").read_text(encoding="utf-8")
    assert "Start Here" in content
    assert "Before You Do Anything" in content
    assert "Mandatory Workflow" in content
