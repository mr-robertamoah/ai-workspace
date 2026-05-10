from __future__ import annotations

from pathlib import Path

import pytest

from ai_workspace.core.errors import WorkspaceError
from ai_workspace.core.filesystem import (
    directory_exists,
    ensure_directory,
    file_exists,
    read_file,
    write_file,
)


def test_ensure_directory_creates_nested_parents(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "path"

    ensure_directory(target)

    assert target.is_dir()


def test_ensure_directory_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "repeat"

    ensure_directory(target)
    ensure_directory(target)

    assert target.is_dir()


def test_write_file_creates_file_with_content(tmp_path: Path) -> None:
    target = tmp_path / "notes.txt"

    write_file(target, "hello")

    assert target.read_text(encoding="utf-8") == "hello"
    assert file_exists(target) is True


def test_write_file_raises_when_file_exists_and_overwrite_is_false(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("original", encoding="utf-8")

    with pytest.raises(WorkspaceError):
        write_file(target, "new")


def test_write_file_overwrites_when_enabled(tmp_path: Path) -> None:
    target = tmp_path / "existing.txt"
    target.write_text("original", encoding="utf-8")

    write_file(target, "updated", overwrite=True)

    assert target.read_text(encoding="utf-8") == "updated"


def test_read_file_returns_content(tmp_path: Path) -> None:
    target = tmp_path / "data.txt"
    target.write_text("payload", encoding="utf-8")

    assert read_file(target) == "payload"


def test_read_file_raises_clean_error_when_missing(tmp_path: Path) -> None:
    target = tmp_path / "missing.txt"

    with pytest.raises(WorkspaceError, match=str(target)):
        read_file(target)


def test_directory_exists_returns_true_for_existing_directory(tmp_path: Path) -> None:
    target = tmp_path / "folder"
    target.mkdir()

    assert directory_exists(target) is True
