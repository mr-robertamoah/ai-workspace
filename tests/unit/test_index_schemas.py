from __future__ import annotations

import time
from pathlib import Path

import pytest

from ai_workspace.core.errors import IndexError
from ai_workspace.core.index_schemas import (
    AdrIndex,
    DocsIndex,
    RepoIndex,
    TaskIndex,
    load_index,
    write_index,
)


def test_each_index_model_loads_from_valid_yaml_fixture(tmp_path: Path) -> None:
    docs_path = tmp_path / "docs-index.yaml"
    docs_path.write_text(
        'generated_at: "2025-01-01T00:00:00Z"\n'
        "docs:\n"
        "  - id: arch-overview\n"
        "    title: Architecture Overview\n"
        "    path: docs/architecture/architecture-overview.md\n"
        "    tags: [architecture]\n"
        "    purpose: Describe architecture\n"
        '    last_modified: "2025-01-01T00:00:00Z"\n'
        '    summary: "Overview."\n',
        encoding="utf-8",
    )
    adr_path = tmp_path / "adr-index.yaml"
    adr_path.write_text(
        'generated_at: "2025-01-01T00:00:00Z"\n'
        "adrs:\n"
        "  - id: ADR-001\n"
        '    title: "Use PostgreSQL"\n'
        "    path: docs/decisions/ADR-001-use-postgresql.md\n"
        "    status: accepted\n"
        '    date: "2025-01-01"\n'
        "    tags: [database]\n"
        "    superseded_by: null\n",
        encoding="utf-8",
    )
    task_path = tmp_path / "task-index.yaml"
    task_path.write_text(
        'generated_at: "2025-01-01T00:00:00Z"\n'
        "tasks:\n"
        "  - id: TASK-001\n"
        "    title: Implement auth\n"
        "    status: active\n"
        '    started_at: "2025-01-01T00:00:00Z"\n'
        "    completed_at: null\n"
        "    path: .ai/active-task/current-task.md\n"
        "    tags: [auth]\n",
        encoding="utf-8",
    )
    repo_path = tmp_path / "repo-index.yaml"
    repo_path.write_text(
        'generated_at: "2025-01-01T00:00:00Z"\n'
        "repositories:\n"
        "  - name: api\n"
        "    path: apps/api\n"
        "    language: python\n"
        '    purpose: "Backend API"\n'
        "    entry_points:\n"
        "      - apps/api/src/main.py\n"
        "    key_directories:\n"
        "      - path: apps/api/src\n"
        "        purpose: Application source\n",
        encoding="utf-8",
    )

    assert load_index(docs_path, DocsIndex).docs[0].id == "arch-overview"
    assert load_index(adr_path, AdrIndex).adrs[0].id == "ADR-001"
    assert load_index(task_path, TaskIndex).tasks[0].id == "TASK-001"
    assert load_index(repo_path, RepoIndex).repositories[0].name == "api"


@pytest.mark.parametrize(
    ("model", "content"),
    [
        (DocsIndex, "generated_at: x\ndocs:\n  - title: missing-id\n"),
        (AdrIndex, "generated_at: x\nadrs:\n  - id: ADR-001\n"),
        (TaskIndex, "generated_at: x\ntasks:\n  - id: TASK-001\n"),
        (RepoIndex, "generated_at: x\nrepositories:\n  - name: api\n"),
    ],
)
def test_index_models_raise_on_missing_required_fields(
    tmp_path: Path, model: type, content: str
) -> None:
    path = tmp_path / "index.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(IndexError):
        load_index(path, model)


def test_write_then_load_round_trips_without_data_loss(tmp_path: Path) -> None:
    path = tmp_path / "docs-index.yaml"
    original = DocsIndex(
        generated_at="2025-01-01T00:00:00Z",
        docs=[],
    )

    write_index(path, original)
    loaded = load_index(path, DocsIndex)

    assert loaded.docs == []


def test_generated_at_is_updated_on_write(tmp_path: Path) -> None:
    path = tmp_path / "docs-index.yaml"
    original = DocsIndex(generated_at="2000-01-01T00:00:00Z", docs=[])

    time.sleep(1)
    write_index(path, original)
    loaded = load_index(path, DocsIndex)

    assert loaded.generated_at != "2000-01-01T00:00:00Z"
