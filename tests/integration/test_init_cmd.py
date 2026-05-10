from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from ai_workspace.cli.main import app

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]


def fixture_path(path: str) -> str:
    return str(REPO_ROOT / path)


def test_init_file_greenfield_creates_scaffold(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "--file", fixture_path("tests/fixtures/greenfield/workspace.yaml")],
        prog_name="ai-workspace",
    )

    assert result.exit_code == 0
    assert (tmp_path / ".ai").is_dir()


def test_init_file_monorepo_creates_correct_structure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "--file", fixture_path("tests/fixtures/monorepo/workspace.yaml")],
        prog_name="ai-workspace",
    )

    assert result.exit_code == 0
    assert (tmp_path / ".ai" / "start-here.md").is_file()
    assert (tmp_path / "docs" / "architecture").is_dir()


def test_init_dry_run_prints_paths_and_creates_nothing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "init",
            "--file",
            fixture_path("tests/fixtures/greenfield/workspace.yaml"),
            "--dry-run",
        ],
        prog_name="ai-workspace",
    )

    assert result.exit_code == 0
    assert "workspace.yaml" in result.output
    assert not (tmp_path / ".ai").exists()
    assert not (tmp_path / "workspace.yaml").exists()


def test_init_twice_without_force_fails_with_useful_message(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    args = ["init", "--file", fixture_path("tests/fixtures/greenfield/workspace.yaml")]

    first = runner.invoke(app, args, prog_name="ai-workspace")
    second = runner.invoke(app, args, prog_name="ai-workspace")

    assert first.exit_code == 0
    assert second.exit_code != 0
    assert "--force" in second.output


def test_init_twice_with_force_succeeds_both_times(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    first_args = ["init", "--file", fixture_path("tests/fixtures/greenfield/workspace.yaml")]
    second_args = [
        "init",
        "--file",
        fixture_path("tests/fixtures/greenfield/workspace.yaml"),
        "--force",
    ]

    first = runner.invoke(app, first_args, prog_name="ai-workspace")
    second = runner.invoke(app, second_args, prog_name="ai-workspace")

    assert first.exit_code == 0
    assert second.exit_code == 0


def test_init_invalid_yaml_exits_non_zero_with_validation_error(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "--file", fixture_path("tests/fixtures/invalid/workspace.yaml")],
        prog_name="ai-workspace",
    )

    assert result.exit_code != 0
    assert "[ERROR]" in result.output


def test_init_success_summary_mentions_workspace_yaml(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "--file", fixture_path("tests/fixtures/python-api/workspace.yaml")],
        prog_name="ai-workspace",
    )

    assert result.exit_code == 0
    assert "workspace.yaml" in result.output
