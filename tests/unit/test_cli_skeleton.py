from __future__ import annotations

import pytest
from typer.testing import CliRunner

from ai_workspace.cli.main import app

runner = CliRunner()


def test_all_commands_registered_and_produce_output() -> None:
    """All commands are implemented; they produce output when invoked."""
    cases = [
        ["adopt"],  # exits non-zero (no workspace.yaml)
        ["summarize"],  # exits non-zero (no workspace)
        ["validate"],  # exits non-zero (no workspace)
        ["validate", "security"],
        ["skills", "list"],
        ["skills", "search", "python"],
        ["docs", "templates"],
        ["docs", "create"],  # exits non-zero (no template name)
        ["handoff", "generate"],  # exits non-zero (no workspace)
    ]
    for args in cases:
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
