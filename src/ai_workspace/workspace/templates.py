"""Template registry for generated workspace files."""

from __future__ import annotations

from typing import Any

DOC_METADATA_HEADER = """---
title: {{doc.title}}
created_at: "{{timestamp}}"
last_modified: "{{timestamp}}"
purpose: {{doc.purpose}}
tags:
{{doc.tags_yaml}}
used_by:
{{doc.used_by_yaml}}
status: draft
---
"""

START_HERE_TEMPLATE = """# Start Here

Generated: {{timestamp}}
Project: {{workspace.name}}
Type: {{workspace.type}}

## What This Project Is

{{project_summary_one_liner}}

## Before You Do Anything

1. Read `project-summary.md`
2. Read `architecture-summary.md`
3. Check `active-task/current-task.md` for in-progress work
4. Query `indexes/` before scanning any directories
5. Check `handoffs/` for the most recent handoff

## Active Task

{{active_task_summary_or_none}}

## Key Architecture Decisions

See `architecture-summary.md` and `indexes/adr-index.yaml`.

## Index Locations

- ADRs: `indexes/adr-index.yaml`
- Docs: `indexes/docs-index.yaml`
- Tasks: `indexes/task-index.yaml`
- Repo: `indexes/repo-index.yaml`

## Mandatory Workflow

Do NOT skip these steps:
1. Read context (this file + summaries)
2. Query indexes
3. Clarify ambiguities before implementing
4. Plan before coding
5. Implement incrementally
6. Validate (tests + lint + security)
7. Update summaries and handoffs
8. Prepare PR summary - do NOT merge
"""

PROJECT_SUMMARY_TEMPLATE = """# What This Project Is

Document the purpose, users, and core business value of `{{workspace.name}}`.

## Tech Stack

- Primary language: {{language.primary}}
- Secondary languages: {{language.secondary_summary}}

## Key Components

- Add the main subsystems or repositories here.
"""

ARCHITECTURE_SUMMARY_TEMPLATE = """# Architecture Style

{{architecture.style}}

## Key Decisions

- Capture major design choices here.

## Component Map

- List the important components and how they relate.
"""

REPO_MAP_TEMPLATE = """# Repo Map

Run `ai-workspace summarize` to populate.
"""

CURRENT_STATE_TEMPLATE = """# Current Phase

Initialization

## What Works

- Workspace scaffold generation is complete.

## What Doesn't

- Project-specific implementation details have not been documented yet.

## Known Issues

- Update this file as work begins.
"""

CURRENT_TASK_TEMPLATE = """# Task

No active task recorded.

## Goal

Describe the current objective here.

## Acceptance Criteria

- Add measurable acceptance criteria here.

## Steps

1. Capture the task.
2. Plan the work.
3. Execute and validate.
"""

CURRENT_PLAN_TEMPLATE = """# Current Plan

1. Read the current task.
2. Query indexes.
3. Write the implementation plan here before coding.
"""

BLOCKERS_TEMPLATE = """# Blockers

- None recorded.
"""

NEXT_STEPS_TEMPLATE = """# Next Steps

1. Review the active task.
2. Confirm the current plan.
3. Continue the next validated step.
"""

GENERATED_REPO_MAP_TEMPLATE = """---
managed_by: system
regeneration: allowed
---
# Generated Repo Map

Auto-generated placeholder. Run `ai-workspace summarize` to refresh.
"""

DEPENDENCY_SUMMARY_TEMPLATE = """---
managed_by: system
regeneration: allowed
---
# Dependency Summary

Auto-generated placeholder. Run `ai-workspace summarize` to refresh.
"""

TECH_DETECTION_TEMPLATE = """generated_at: "{{timestamp}}"
primary_language: {{language.primary}}
detected_frameworks: []
ci_systems: []
notes:
  - Generated during init. Run ai-workspace summarize to refresh.
"""

ADR_TEMPLATE = """---
title: "ADR-001: Use PostgreSQL as primary database"
date: YYYY-MM-DD
status: proposed | accepted | deprecated | superseded
superseded_by: null
tags: [database, infrastructure]
---

# ADR-001: Use PostgreSQL as primary database

## Context

What is the problem or situation that requires a decision?

## Decision

What was decided?

## Rationale

Why was this decision made over alternatives?

## Consequences

What are the positive and negative consequences of this decision?

## Alternatives Considered

- Alternative A: why it was not chosen
- Alternative B: why it was not chosen
"""

ARCHITECTURE_OVERVIEW_TEMPLATE = DOC_METADATA_HEADER + """
# Architecture Overview

Describe the architecture of `{{workspace.name}}` here.
"""

GETTING_STARTED_TEMPLATE = DOC_METADATA_HEADER + """
# Getting Started

Explain how a new contributor should begin working on `{{workspace.name}}`.
"""


def _flatten_context(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    flattened: dict[str, str] = {}
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(_flatten_context(value, path))
        else:
            flattened[path] = str(value)
    return flattened


def render(template: str, context: dict[str, Any]) -> str:
    """Render a template using simple placeholder replacement."""

    rendered = template
    for key, value in _flatten_context(context).items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered
