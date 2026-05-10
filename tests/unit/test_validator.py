"""Unit tests for workspace validator."""

from __future__ import annotations

import shutil
from pathlib import Path

from ai_workspace.security.validator import validate_workspace

GREENFIELD = Path(__file__).parent.parent / "fixtures" / "greenfield"
PYTHON_API = Path(__file__).parent.parent / "fixtures" / "python-api"


def _init_workspace(tmp_path: Path) -> None:
    """Copy fixture and run init to produce a valid workspace."""
    shutil.copytree(GREENFIELD, tmp_path, dirs_exist_ok=True)
    from ai_workspace.core.config import load_workspace_yaml
    from ai_workspace.workspace.generator import generate_workspace

    config = load_workspace_yaml(tmp_path / "workspace.yaml")
    generate_workspace(config, tmp_path)


def test_all_checks_pass_on_valid_workspace(tmp_path):
    _init_workspace(tmp_path)
    results = validate_workspace(tmp_path)
    failures = [r for r in results if r.status == "fail"]
    assert failures == [], [r.message for r in failures]


def test_missing_workspace_yaml_produces_fail(tmp_path):
    results = validate_workspace(tmp_path)
    checks = {r.check: r for r in results}
    assert checks["workspace.yaml"].status == "fail"


def test_missing_ai_dir_produces_fail(tmp_path):
    shutil.copytree(GREENFIELD, tmp_path, dirs_exist_ok=True)
    results = validate_workspace(tmp_path)
    checks = {r.check: r for r in results}
    assert checks[".ai/ directory"].status == "fail"


def test_missing_start_here_produces_fail(tmp_path):
    _init_workspace(tmp_path)
    (tmp_path / ".ai" / "start-here.md").unlink()
    results = validate_workspace(tmp_path)
    checks = {r.check: r for r in results}
    assert checks["start-here.md"].status == "fail"


def test_broken_index_yaml_produces_fail(tmp_path):
    _init_workspace(tmp_path)
    (tmp_path / ".ai" / "indexes" / "docs-index.yaml").write_text("{{invalid: yaml: :")
    results = validate_workspace(tmp_path)
    fails = [r for r in results if r.check == "index:docs-index.yaml" and r.status == "fail"]
    assert fails


def test_stale_handoff_produces_warn(tmp_path):
    _init_workspace(tmp_path)
    handoff = tmp_path / ".ai" / "handoffs" / "2020-01-01-00-00-old-task.md"
    handoff.write_text("# Old handoff")
    import os

    old_time = 0  # epoch — definitely > 30 days ago
    os.utime(handoff, (old_time, old_time))
    results = validate_workspace(tmp_path)
    warns = [r for r in results if r.check == "handoffs" and r.status == "warn"]
    assert warns


def test_result_count_matches_number_of_checks(tmp_path):
    _init_workspace(tmp_path)
    results = validate_workspace(tmp_path)
    # At minimum: workspace.yaml, .ai/, start-here.md, 4 indexes
    assert len(results) >= 7
