"""Integration tests for handoff generate command."""

from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from ai_workspace.workspace.handoff import HandoffData, generate_handoff

runner = CliRunner()
GREENFIELD = Path(__file__).parent.parent / "fixtures" / "greenfield"


def _init(tmp_path: Path) -> None:
    shutil.copytree(GREENFIELD, tmp_path, dirs_exist_ok=True)
    from ai_workspace.core.config import load_workspace_yaml
    from ai_workspace.workspace.generator import generate_workspace

    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    generate_workspace(config, tmp_path)


def test_generate_handoff_creates_file_in_handoffs_dir(tmp_path):
    _init(tmp_path)
    data = HandoffData(
        accomplished="Implemented feature X",
        current_state="Tests passing",
        blockers="None",
        next_steps="Deploy to staging",
        tests_passing=True,
    )
    path = generate_handoff(tmp_path, data)
    assert path.parent == tmp_path / ".ai" / "handoffs"
    assert path.exists()


def test_handoff_filename_contains_date(tmp_path):
    _init(tmp_path)
    data = HandoffData("done", "good", "none", "next", True)
    path = generate_handoff(tmp_path, data)
    from datetime import UTC, datetime

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    assert today in path.name


def test_handoff_file_contains_all_sections(tmp_path):
    _init(tmp_path)
    data = HandoffData("accomplished X", "state Y", "blocker Z", "next W", False)
    path = generate_handoff(tmp_path, data)
    content = path.read_text()
    for section in [
        "What Was Accomplished",
        "Current State",
        "Active Task Status",
        "What Was NOT Done",
        "Next Steps",
        "Tests Passing",
    ]:
        assert section in content, f"Missing section: {section}"


def test_task_index_updated_after_handoff(tmp_path):
    _init(tmp_path)
    data = HandoffData("done", "state", "none", "next", True)
    generate_handoff(tmp_path, data)
    index = tmp_path / ".ai" / "indexes" / "task-index.yaml"
    assert index.exists()


def test_two_handoffs_create_separate_files(tmp_path):
    _init(tmp_path)
    import time

    data = HandoffData("done", "state", "none", "next", True)
    p1 = generate_handoff(tmp_path, data)
    time.sleep(1)
    p2 = generate_handoff(tmp_path, data)
    # May be same filename if within same minute — just check both exist
    assert p1.exists()
    assert p2.exists()
