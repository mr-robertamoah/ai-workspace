from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from ai_workspace.core.config import load_workspace_yaml
from ai_workspace.core.errors import WorkspaceValidationError


def write_workspace(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "workspace.yaml"
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    return path


def test_valid_minimal_yaml_loads_without_error(tmp_path: Path) -> None:
    path = write_workspace(
        tmp_path,
        """
        workspace:
          name: sample-app
          type: single
        language:
          primary: python
        architecture:
          style: monolith
        standards:
          testing: pytest
          formatting: black
          linting: ruff
        """,
    )

    config = load_workspace_yaml(path)

    assert config.workspace.name == "sample-app"
    assert config.ai.enabled is True


def test_valid_full_yaml_loads_without_error(tmp_path: Path) -> None:
    path = write_workspace(
        tmp_path,
        """
        workspace:
          name: full-app
          type: multi
        repositories:
          - name: backend
            path: services/backend
        language:
          primary: python
          secondary:
            - typescript
            - other
        architecture:
          style: modular-monolith
        ai:
          enabled: true
          adr: false
          handoffs: true
          tasks: false
          agents:
            - codex
            - claude
        documentation:
          enabled: true
          structure: full
        security:
          enabled: true
          dependency_scanning: true
          bandit: false
        standards:
          testing: pytest
          formatting: black
          linting: ruff
        """,
    )

    config = load_workspace_yaml(path)

    assert config.workspace.type == "multi"
    assert config.repositories[0].path == "services/backend"
    assert config.documentation.structure == "full"


@pytest.mark.parametrize(
    ("workspace_name", "expected_text"),
    [
        ("Uppercase", "workspace.name"),
        ("contains spaces", "workspace.name"),
        ("a" * 65, "workspace.name"),
    ],
)
def test_invalid_workspace_names_raise_validation_error(
    tmp_path: Path, workspace_name: str, expected_text: str
) -> None:
    path = write_workspace(
        tmp_path,
        f"""
        workspace:
          name: {workspace_name}
          type: single
        language:
          primary: python
        architecture:
          style: monolith
        standards:
          testing: pytest
          formatting: black
          linting: ruff
        """,
    )

    with pytest.raises(WorkspaceValidationError, match=expected_text):
        load_workspace_yaml(path)


def test_absolute_repository_path_raises_validation_error(tmp_path: Path) -> None:
    path = write_workspace(
        tmp_path,
        """
        workspace:
          name: invalid-repo-path
          type: monorepo
        repositories:
          - name: api
            path: /srv/api
        language:
          primary: python
        architecture:
          style: microservices
        standards:
          testing: pytest
          formatting: black
          linting: ruff
        """,
    )

    with pytest.raises(WorkspaceValidationError, match="repositories.0.path"):
        load_workspace_yaml(path)


def test_unknown_top_level_key_raises_validation_error(tmp_path: Path) -> None:
    path = write_workspace(
        tmp_path,
        """
        workspace:
          name: invalid-extra
          type: single
        language:
          primary: python
        architecture:
          style: monolith
        standards:
          testing: pytest
          formatting: black
          linting: ruff
        unknown: true
        """,
    )

    with pytest.raises(WorkspaceValidationError, match="unknown"):
        load_workspace_yaml(path)


@pytest.mark.parametrize("field_name", ["name", "type"])
def test_missing_required_workspace_fields_raise_validation_error(
    tmp_path: Path, field_name: str
) -> None:
    workspace_lines = ["workspace:"]
    if field_name != "name":
        workspace_lines.append("  name: sample-app")
    if field_name != "type":
        workspace_lines.append("  type: single")

    path = write_workspace(
        tmp_path,
        "\n".join(
            workspace_lines
            + [
                "language:",
                "  primary: python",
                "architecture:",
                "  style: monolith",
                "standards:",
                "  testing: pytest",
                "  formatting: black",
                "  linting: ruff",
            ]
        ),
    )

    with pytest.raises(WorkspaceValidationError, match=f"workspace.{field_name}"):
        load_workspace_yaml(path)


def test_invalid_workspace_type_raises_validation_error(tmp_path: Path) -> None:
    path = write_workspace(
        tmp_path,
        """
        workspace:
          name: invalid-type
          type: unsupported
        language:
          primary: python
        architecture:
          style: monolith
        standards:
          testing: pytest
          formatting: black
          linting: ruff
        """,
    )

    with pytest.raises(WorkspaceValidationError, match="workspace.type"):
        load_workspace_yaml(path)


@pytest.mark.parametrize(
    "fixture_path",
    [
        "tests/fixtures/greenfield/workspace.yaml",
        "tests/fixtures/python-api/workspace.yaml",
        "tests/fixtures/monorepo/workspace.yaml",
    ],
)
def test_workspace_fixtures_load_successfully(fixture_path: str) -> None:
    config = load_workspace_yaml(Path(fixture_path))

    assert config.workspace.name
