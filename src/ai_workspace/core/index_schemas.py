"""Pydantic models and helpers for workspace index files."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ai_workspace.core.errors import IndexError

yaml = YAML(typ="safe")
yaml_writer = YAML()
yaml_writer.default_flow_style = False

IndexModelT = TypeVar("IndexModelT", bound="IndexDocument")


def current_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for index generation."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class StrictModel(BaseModel):
    """Base model that forbids undeclared fields."""

    model_config = ConfigDict(extra="forbid")


class DocsIndexEntry(StrictModel):
    id: str
    title: str
    path: str
    tags: list[str] = Field(default_factory=list)
    purpose: str
    last_modified: str
    summary: str = ""


class DocsIndex(StrictModel):
    generated_at: str
    docs: list[DocsIndexEntry] = Field(default_factory=list)


class AdrIndexEntry(StrictModel):
    id: str
    title: str
    path: str
    status: str
    date: str
    tags: list[str] = Field(default_factory=list)
    superseded_by: str | None = None


class AdrIndex(StrictModel):
    generated_at: str
    adrs: list[AdrIndexEntry] = Field(default_factory=list)


class TaskIndexEntry(StrictModel):
    id: str
    title: str
    status: str
    started_at: str
    completed_at: str | None = None
    path: str
    tags: list[str] = Field(default_factory=list)


class TaskIndex(StrictModel):
    generated_at: str
    tasks: list[TaskIndexEntry] = Field(default_factory=list)


class RepoKeyDirectoryEntry(StrictModel):
    path: str
    purpose: str


class RepoIndexEntry(StrictModel):
    name: str
    path: str
    language: str
    purpose: str
    entry_points: list[str] = Field(default_factory=list)
    key_directories: list[RepoKeyDirectoryEntry] = Field(default_factory=list)


class RepoIndex(StrictModel):
    generated_at: str
    repositories: list[RepoIndexEntry] = Field(default_factory=list)


IndexDocument = DocsIndex | AdrIndex | TaskIndex | RepoIndex


def load_index(path: Path, model: type[IndexModelT]) -> IndexModelT:
    """Load an index YAML file and validate it against the requested model."""

    try:
        data = yaml.load(path.read_text(encoding="utf-8"))
        if data is None:
            data = {}
        return model.model_validate(data)
    except FileNotFoundError as exc:
        raise IndexError(f"Index file not found: {path}") from exc
    except (ValidationError, YAMLError) as exc:
        raise IndexError(f"Failed to load index {path}: {exc}") from exc


def write_index(path: Path, index: IndexDocument) -> None:
    """Write an index model to YAML, refreshing generated_at on each write."""

    refreshed = index.model_copy(update={"generated_at": current_timestamp()})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml_writer.dump(refreshed.model_dump(mode="python", exclude_none=False), handle)
