"""Unit tests for the static technology detector."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


from ai_workspace.workspace.detector import detect_project

PYTHON_API = Path(__file__).parent.parent / "fixtures" / "python-api"
MONOREPO = Path(__file__).parent.parent / "fixtures" / "monorepo"
NO_DOCS = Path(__file__).parent.parent / "fixtures" / "no-docs"


def test_detects_python_from_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    result = detect_project(tmp_path)
    assert "python" in result.languages


def test_detects_python_from_requirements(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n")
    result = detect_project(tmp_path)
    assert "python" in result.languages


def test_detects_fastapi_framework():
    result = detect_project(PYTHON_API)
    assert "python" in result.languages
    assert "fastapi" in result.frameworks


def test_detects_nodejs_from_package_json(tmp_path):
    (tmp_path / "package.json").write_text('{"name": "app", "dependencies": {"express": "^4"}}')
    result = detect_project(tmp_path)
    assert "nodejs" in result.languages


def test_detects_monorepo_structure():
    result = detect_project(MONOREPO)
    assert result.languages  # at least something detected


def test_has_tests_true_when_tests_dir_exists():
    result = detect_project(PYTHON_API)
    assert result.has_tests is True


def test_has_docs_false_when_no_docs_dir():
    result = detect_project(NO_DOCS)
    assert result.has_docs is False


def test_empty_directory_does_not_crash(tmp_path):
    result = detect_project(tmp_path)
    assert result is not None
    assert result.languages == ["other"]


def test_no_subprocess_calls(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    with patch("subprocess.run") as mock_run:
        detect_project(tmp_path)
        mock_run.assert_not_called()
