"""Handoff document generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class HandoffData:
    accomplished: str
    current_state: str
    blockers: str
    next_steps: str
    tests_passing: bool


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def _current_task_title(root: Path) -> str:
    task_file = root / ".ai" / "active-task" / "current-task.md"
    if task_file.exists():
        for line in task_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return "untitled-task"


def generate_handoff(root: Path, data: HandoffData) -> Path:
    """Write a timestamped handoff document to .ai/handoffs/."""
    now = datetime.now(UTC)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    filename_ts = now.strftime("%Y-%m-%d-%H-%M")
    task_title = _current_task_title(root)
    filename = f"{filename_ts}-{_slug(task_title)}.md"

    handoffs_dir = root / ".ai" / "handoffs"
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    path = handoffs_dir / filename

    content = f"""# Handoff — {_slug(task_title)}

Generated: {timestamp}
Agent: human
Session duration: unknown

## What Was Accomplished

{data.accomplished}

## Current State

{data.current_state}

## Active Task Status

- Task: {task_title}
- Blockers: {data.blockers}

## What Was NOT Done

(Fill in incomplete work)

## Next Steps

{data.next_steps}

## Tests Passing

{"yes" if data.tests_passing else "no"}

## Files Modified

(Fill in modified files)

## Decisions Made

(Fill in decisions)

## References

(Fill in references)
"""
    path.write_text(content, encoding="utf-8")
    _update_task_index(root, timestamp)
    return path


def _update_task_index(root: Path, timestamp: str) -> None:
    from ruamel.yaml import YAML

    index_path = root / ".ai" / "indexes" / "task-index.yaml"
    if not index_path.exists():
        return
    yaml = YAML()
    yaml.default_flow_style = False
    try:
        data = yaml.load(index_path.read_text(encoding="utf-8")) or {}
        data["generated_at"] = timestamp
        with index_path.open("w", encoding="utf-8") as fh:
            yaml.dump(data, fh)
    except Exception:
        pass
