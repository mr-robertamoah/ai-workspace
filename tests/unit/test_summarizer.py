"""Unit tests for the workspace summarizer."""

from __future__ import annotations

import shutil
from pathlib import Path

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.workspace.summarizer import (
    generate_dependency_summary,
    generate_repo_map,
    summarize_workspace,
)

PYTHON_API = Path(__file__).parent.parent / "fixtures" / "python-api"
MONOREPO = Path(__file__).parent.parent / "fixtures" / "monorepo"


def test_dependency_summary_contains_packages_from_requirements():
    summary = generate_dependency_summary(PYTHON_API)
    assert "fastapi" in summary
    assert "uvicorn" in summary


def test_dependency_summary_no_known_files(tmp_path):
    summary = generate_dependency_summary(tmp_path)
    assert "No known dependency files detected" in summary


def test_dependency_summary_reads_pyproject_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname="x"\ndependencies = ["requests>=2"]\n'
    )
    summary = generate_dependency_summary(tmp_path)
    assert "requests" in summary


def test_dependency_summary_reads_package_json(tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4"}}')
    summary = generate_dependency_summary(tmp_path)
    assert "express" in summary


def test_dependency_summary_reads_go_mod(tmp_path):
    (tmp_path / "go.mod").write_text(
        "module example.com/app\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.0\n)\n"
    )
    summary = generate_dependency_summary(tmp_path)
    assert "gin" in summary


def test_repo_map_contains_directory_names():
    repo_map = generate_repo_map(PYTHON_API)
    assert "src" in repo_map


def test_repo_map_excludes_noise(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / "src").mkdir()
    repo_map = generate_repo_map(tmp_path)
    assert "__pycache__" not in repo_map
    assert ".git" not in repo_map
    assert "src" in repo_map


def test_repo_map_annotates_tests_dir(tmp_path):
    (tmp_path / "tests").mkdir()
    repo_map = generate_repo_map(tmp_path)
    assert "test suite" in repo_map


def test_summarize_workspace_does_not_write_project_summary(tmp_path):
    shutil.copytree(PYTHON_API, tmp_path, dirs_exist_ok=True)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    (tmp_path / ".ai" / "generated").mkdir(parents=True, exist_ok=True)
    summarize_workspace(tmp_path, config)
    assert not (tmp_path / ".ai" / "generated" / "project-summary.md").exists()


def test_summarize_workspace_writes_all_three_files(tmp_path):
    shutil.copytree(PYTHON_API, tmp_path, dirs_exist_ok=True)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    written = summarize_workspace(tmp_path, config)
    assert "repo-map-generated.md" in written
    assert "dependency-summary.md" in written
    assert "tech-detection.yaml" in written
    for path in written.values():
        assert path.exists()


def test_all_written_files_are_valid_markdown_or_yaml(tmp_path):
    shutil.copytree(PYTHON_API, tmp_path, dirs_exist_ok=True)
    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    written = summarize_workspace(tmp_path, config)
    for name, path in written.items():
        content = path.read_text()
        assert content.strip(), f"{name} is empty"
        if name.endswith(".md"):
            assert "#" in content, f"{name} has no headings"
