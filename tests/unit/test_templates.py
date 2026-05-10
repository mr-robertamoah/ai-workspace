from __future__ import annotations

from ai_workspace.workspace.templates import ADR_TEMPLATE, START_HERE_TEMPLATE, render


def test_render_replaces_nested_workspace_name() -> None:
    rendered = render("Project: {{workspace.name}}", {"workspace": {"name": "demo-app"}})

    assert rendered == "Project: demo-app"


def test_render_leaves_missing_placeholder_unchanged() -> None:
    rendered = render("Project: {{workspace.name}}", {"workspace": {}})

    assert rendered == "Project: {{workspace.name}}"


def test_render_with_empty_context_returns_template_unchanged() -> None:
    template = "Hello {{workspace.name}}"

    assert render(template, {}) == template


def test_start_here_template_contains_required_sections() -> None:
    assert "Start Here" in START_HERE_TEMPLATE
    assert "Before You Do Anything" in START_HERE_TEMPLATE
    assert "Mandatory Workflow" in START_HERE_TEMPLATE


def test_adr_template_contains_required_sections() -> None:
    assert "Context" in ADR_TEMPLATE
    assert "Decision" in ADR_TEMPLATE
    assert "Rationale" in ADR_TEMPLATE
    assert "Consequences" in ADR_TEMPLATE
