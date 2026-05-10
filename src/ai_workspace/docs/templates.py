"""Built-in documentation templates and their output path resolution."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


_FRONT_MATTER = """\
---
title: "{title}"
created_at: "{ts}"
last_modified: "{ts}"
purpose: "{purpose}"
tags: {tags}
status: draft
---
"""

TEMPLATES: dict[str, dict] = {
    "architecture-overview": {
        "description": "System architecture overview document",
        "output": "docs/architecture/architecture-overview.md",
        "title": "Architecture Overview",
        "purpose": "Describe the system architecture for human and AI readers",
        "tags": "[architecture]",
        "body": "# Architecture Overview\n\n## Architecture Style\n\n## Key Decisions\n\n## Component Map\n",
    },
    "adr": {
        "description": "Architecture Decision Record",
        "output": "docs/decisions/ADR-{number:03d}-{slug}.md",
        "title": "ADR-{number:03d}: {title}",
        "purpose": "Record an architecture decision",
        "tags": "[adr, architecture]",
        "body": (
            "# ADR-{number:03d}: {title}\n\n"
            "## Context\n\n## Decision\n\n## Rationale\n\n## Consequences\n\n## Alternatives Considered\n"
        ),
    },
    "runbook": {
        "description": "Operational runbook",
        "output": "docs/runbooks/{slug}.md",
        "title": "{title}",
        "purpose": "Operational runbook",
        "tags": "[runbook, operations]",
        "body": "# {title}\n\n## Overview\n\n## Steps\n\n## Rollback\n",
    },
    "onboarding": {
        "description": "Onboarding guide",
        "output": "docs/onboarding/{slug}.md",
        "title": "{title}",
        "purpose": "Help new contributors get started",
        "tags": "[onboarding]",
        "body": "# {title}\n\n## Prerequisites\n\n## Setup\n\n## First Steps\n",
    },
    "api-reference": {
        "description": "API reference document",
        "output": "docs/api/{slug}.md",
        "title": "{title}",
        "purpose": "Document the API",
        "tags": "[api]",
        "body": "# {title}\n\n## Endpoints\n\n## Authentication\n\n## Examples\n",
    },
}


def _slug(text: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _next_adr_number(root: Path) -> int:
    decisions = root / "docs" / "decisions"
    if not decisions.is_dir():
        return 1
    existing = list(decisions.glob("ADR-*.md"))
    if not existing:
        return 1
    nums = []
    for f in existing:
        try:
            nums.append(int(f.name.split("-")[1]))
        except (IndexError, ValueError):
            pass
    return max(nums, default=0) + 1


def render_template(name: str, root: Path, title: str = "") -> tuple[str, Path]:
    """Return (content, output_path) for a named template."""
    tmpl = TEMPLATES[name]
    ts = _now()
    slug = _slug(title) if title else name

    if name == "adr":
        number = _next_adr_number(root)
        doc_title = tmpl["title"].format(number=number, title=title or "Untitled Decision")
        output_rel = tmpl["output"].format(number=number, slug=slug or "decision")
        body = tmpl["body"].format(number=number, title=title or "Untitled Decision")
    elif name == "architecture-overview":
        doc_title = tmpl["title"]
        output_rel = tmpl["output"]
        body = tmpl["body"]
    else:
        doc_title = tmpl["title"].format(title=title or name)
        output_rel = tmpl["output"].format(slug=slug or name)
        body = tmpl["body"].format(title=title or name)

    front = _FRONT_MATTER.format(title=doc_title, ts=ts, purpose=tmpl["purpose"], tags=tmpl["tags"])
    content = front + body
    return content, root / output_rel
