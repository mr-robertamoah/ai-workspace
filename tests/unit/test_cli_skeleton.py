from __future__ import annotations

import pytest
from typer.testing import CliRunner

from ai_workspace.cli.main import app

runner = CliRunner()


@pytest.mark.parametrize(
    "args",
    [
        ["validate"],
        ["validate", "security"],
        ["docs", "templates"],
        ["docs", "create"],
        ["handoff", "generate"],
    ],
)
def test_registered_commands_exit_successfully_and_print_output(args: list[str]) -> None:
    result = runner.invoke(app, args, prog_name="ai-workspace")

    assert result.exit_code == 0
    assert result.output.strip()
    assert "Not yet implemented" in result.output


def test_adopt_command_registered_and_prints_output() -> None:
    """adopt is fully implemented; without workspace.yaml it exits non-zero with an error."""
    result = runner.invoke(app, ["adopt"], prog_name="ai-workspace")
    assert result.output.strip()


def test_summarize_command_registered_and_prints_output() -> None:
    """summarize is fully implemented; outside a workspace it exits non-zero with an error."""
    result = runner.invoke(app, ["summarize"], prog_name="ai-workspace")
    assert result.output.strip()


def test_skills_commands_registered_and_print_output() -> None:
    """skills commands are fully implemented; they produce output."""
    for args in [["skills", "list"], ["skills", "search", "python"]]:
        result = runner.invoke(app, args, prog_name="ai-workspace")
        assert result.output.strip(), f"No output for {args}"


def test_root_help_exits_zero_and_contains_program_name() -> None:
    result = runner.invoke(app, ["--help"], prog_name="ai-workspace")

    assert result.exit_code == 0
    assert "ai-workspace" in result.output


def test_init_help_exits_zero() -> None:
    result = runner.invoke(app, ["init", "--help"], prog_name="ai-workspace")

    assert result.exit_code == 0


@pytest.mark.parametrize(
    "args",
    [
        ["validate", "--help"],
        ["index", "--help"],
        ["skills", "--help"],
        ["docs", "--help"],
        ["handoff", "--help"],
    ],
)
def test_subcommand_group_help_exits_zero(args: list[str]) -> None:
    result = runner.invoke(app, args, prog_name="ai-workspace")

    assert result.exit_code == 0
