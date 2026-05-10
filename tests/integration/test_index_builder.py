from __future__ import annotations

from pathlib import Path
import shutil

from ruamel.yaml import YAML

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.core.index_schemas import AdrIndex, DocsIndex, RepoIndex, TaskIndex, load_index
from ai_workspace.workspace.generator import generate_workspace
from ai_workspace.workspace.index_builder import rebuild_all_indexes

yaml = YAML(typ="safe")
REPO_ROOT = Path(__file__).resolve().parents[2]


def copy_fixture(name: str, tmp_path: Path) -> Path:
    source = REPO_ROOT / "tests" / "fixtures" / name
    destination = tmp_path / name
    shutil.copytree(source, destination)
    return destination


def prepare_python_api_workspace(tmp_path: Path) -> tuple[Path, object]:
    project_root = copy_fixture("python-api", tmp_path)
    config = load_workspace_yaml(project_root / "workspace.yaml")
    generate_workspace(config, project_root)
    (project_root / "docs" / "architecture" / "architecture-overview.md").write_text(
        "---\n"
        "title: Architecture Overview\n"
        "purpose: Describe the system architecture\n"
        "tags:\n"
        "  - architecture\n"
        "status: current\n"
        "---\n\n"
        "# Architecture Overview\n\n"
        "System architecture summary.\n",
        encoding="utf-8",
    )
    (project_root / "docs" / "quick-start.md").write_text(
        "# Quick Start\n\nA short onboarding guide.\n",
        encoding="utf-8",
    )
    (project_root / "docs" / "decisions" / "ADR-001-use-postgresql.md").write_text(
        "---\n"
        'title: "ADR-001: Use PostgreSQL"\n'
        'date: "2025-01-01"\n'
        "status: accepted\n"
        "superseded_by: null\n"
        "tags: [database]\n"
        "---\n\n"
        "# ADR-001: Use PostgreSQL\n",
        encoding="utf-8",
    )
    (project_root / ".ai" / "active-task" / "current-task.md").write_text(
        "# Implement authentication service\n\nGoal details.\n",
        encoding="utf-8",
    )
    return project_root, config


def test_rebuilding_python_api_fixture_produces_non_empty_docs_index(tmp_path: Path) -> None:
    project_root, config = prepare_python_api_workspace(tmp_path)

    counts = rebuild_all_indexes(project_root, config)

    docs_index = load_index(project_root / ".ai" / "indexes" / "docs-index.yaml", DocsIndex)
    assert counts["docs-index.yaml"] > 0
    assert docs_index.docs


def test_rebuilding_fixture_with_adr_files_produces_correct_adr_entries(tmp_path: Path) -> None:
    project_root, config = prepare_python_api_workspace(tmp_path)

    rebuild_all_indexes(project_root, config)

    adr_index = load_index(project_root / ".ai" / "indexes" / "adr-index.yaml", AdrIndex)
    assert adr_index.adrs[0].id == "ADR-001"
    assert adr_index.adrs[0].status == "accepted"


def test_rebuilding_with_empty_docs_produces_empty_valid_docs_index(tmp_path: Path) -> None:
    project_root = copy_fixture("no-docs", tmp_path)
    config = load_workspace_yaml(project_root / "workspace.yaml")
    generate_workspace(config, project_root)

    counts = rebuild_all_indexes(project_root, config)

    docs_index = load_index(project_root / ".ai" / "indexes" / "docs-index.yaml", DocsIndex)
    assert counts["docs-index.yaml"] == 0
    assert docs_index.docs == []


def test_front_matter_is_correctly_parsed_and_reflected_in_entries(tmp_path: Path) -> None:
    project_root, config = prepare_python_api_workspace(tmp_path)

    rebuild_all_indexes(project_root, config)

    docs_index = load_index(project_root / ".ai" / "indexes" / "docs-index.yaml", DocsIndex)
    architecture_doc = next(
        entry for entry in docs_index.docs if entry.id == "architecture-overview"
    )
    assert architecture_doc.title == "Architecture Overview"
    assert architecture_doc.purpose == "Describe the system architecture"
    assert architecture_doc.tags == ["architecture"]


def test_files_without_front_matter_are_indexed_with_derived_title(tmp_path: Path) -> None:
    project_root, config = prepare_python_api_workspace(tmp_path)

    rebuild_all_indexes(project_root, config)

    docs_index = load_index(project_root / ".ai" / "indexes" / "docs-index.yaml", DocsIndex)
    quick_start = next(entry for entry in docs_index.docs if entry.path == "docs/quick-start.md")
    assert quick_start.title == "Quick Start"


def test_repo_index_reflects_repositories_from_config(tmp_path: Path) -> None:
    project_root = copy_fixture("monorepo", tmp_path)
    config = load_workspace_yaml(project_root / "workspace.yaml")
    generate_workspace(config, project_root)
    api_dir = project_root / "apps" / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "pyproject.toml").write_text(
        "[project]\nname='api'\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    (project_root / "apps" / "api" / "src").mkdir()
    (project_root / "apps" / "api" / "tests").mkdir()
    (project_root / "apps" / "api" / "src" / "main.py").write_text(
        "print('hi')\n", encoding="utf-8"
    )

    counts = rebuild_all_indexes(project_root, config)

    repo_index = load_index(project_root / ".ai" / "indexes" / "repo-index.yaml", RepoIndex)
    assert counts["repo-index.yaml"] == 2
    assert repo_index.repositories[0].name == "api"


def test_return_dict_contains_correct_counts(tmp_path: Path) -> None:
    project_root, config = prepare_python_api_workspace(tmp_path)

    counts = rebuild_all_indexes(project_root, config)

    assert set(counts) == {
        "docs-index.yaml",
        "adr-index.yaml",
        "task-index.yaml",
        "repo-index.yaml",
    }
    assert counts["task-index.yaml"] == 1


def test_all_written_index_files_parse_as_valid_yaml(tmp_path: Path) -> None:
    project_root, config = prepare_python_api_workspace(tmp_path)

    rebuild_all_indexes(project_root, config)

    for name in ["docs-index.yaml", "adr-index.yaml", "task-index.yaml", "repo-index.yaml"]:
        with (project_root / ".ai" / "indexes" / name).open(encoding="utf-8") as handle:
            assert yaml.load(handle) is not None
        assert load_index(
            project_root / ".ai" / "indexes" / name,
            (
                DocsIndex
                if name == "docs-index.yaml"
                else (
                    AdrIndex
                    if name == "adr-index.yaml"
                    else TaskIndex if name == "task-index.yaml" else RepoIndex
                )
            ),
        )
