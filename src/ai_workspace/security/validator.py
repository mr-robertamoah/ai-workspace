"""Workspace health validation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from ruamel.yaml import YAML

_yaml = YAML(typ="safe")


class ValidationResult(BaseModel):
    check: str
    status: Literal["pass", "warn", "fail"]
    message: str


def _load_yaml_safe(path: Path) -> tuple[dict | None, str | None]:
    """Return (data, error_message). error_message is None on success."""
    try:
        text = path.read_text(encoding="utf-8")
        if "!!python/object" in text:
            return None, "Contains unsafe !!python/object tag"
        data = _yaml.load(text)
        return data or {}, None
    except Exception as exc:
        return None, str(exc)


CURRENT_SCHEMA_VERSION = 1


def validate_workspace(root: Path) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    # 0. Version check
    version_file = root / ".ai" / "version.yaml"
    if version_file.exists():
        data, err = _load_yaml_safe(version_file)
        if err:
            results.append(
                ValidationResult(
                    check="version", status="warn", message=f"Could not read version.yaml: {err}"
                )
            )
        else:
            schema_ver = (data or {}).get("schema_version", 1)
            if schema_ver < CURRENT_SCHEMA_VERSION:
                results.append(
                    ValidationResult(
                        check="version",
                        status="warn",
                        message=f"Workspace schema v{schema_ver} is older than current v{CURRENT_SCHEMA_VERSION}. Run `ai-workspace init --force` to upgrade.",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check="version", status="pass", message=f"Schema v{schema_ver} is current"
                    )
                )
    else:
        results.append(
            ValidationResult(
                check="version",
                status="warn",
                message=".ai/version.yaml not found — workspace predates versioning",
            )
        )

    # 1. workspace.yaml exists and loads
    ws_yaml = root / "workspace.yaml"
    if not ws_yaml.exists():
        results.append(
            ValidationResult(
                check="workspace.yaml", status="fail", message="workspace.yaml not found"
            )
        )
    else:
        try:
            from ai_workspace.core.config import load_workspace_yaml

            load_workspace_yaml(ws_yaml)
            results.append(ValidationResult(check="workspace.yaml", status="pass", message="Valid"))
        except Exception as exc:
            results.append(
                ValidationResult(check="workspace.yaml", status="fail", message=str(exc))
            )

    # 2. .ai/ directory exists
    ai_dir = root / ".ai"
    if ai_dir.is_dir():
        results.append(ValidationResult(check=".ai/ directory", status="pass", message="Present"))
    else:
        results.append(
            ValidationResult(
                check=".ai/ directory", status="fail", message=".ai/ directory not found"
            )
        )

    # 3. start-here.md exists and non-empty
    start_here = ai_dir / "start-here.md"
    if start_here.exists() and start_here.stat().st_size > 0:
        results.append(
            ValidationResult(check="start-here.md", status="pass", message="Present and non-empty")
        )
    else:
        results.append(
            ValidationResult(
                check="start-here.md", status="fail", message="start-here.md missing or empty"
            )
        )

    # 4 & 5. Index files exist and parse as valid YAML
    index_names = ["adr-index.yaml", "task-index.yaml", "docs-index.yaml", "repo-index.yaml"]
    for name in index_names:
        path = ai_dir / "indexes" / name
        if not path.exists():
            results.append(
                ValidationResult(check=f"index:{name}", status="fail", message=f"{name} not found")
            )
            continue
        data, err = _load_yaml_safe(path)
        if err:
            results.append(
                ValidationResult(
                    check=f"index:{name}", status="fail", message=f"Invalid YAML: {err}"
                )
            )
        else:
            results.append(
                ValidationResult(check=f"index:{name}", status="pass", message="Valid YAML")
            )

    # 6. Index entries reference existing paths (warn only)
    docs_index = ai_dir / "indexes" / "docs-index.yaml"
    if docs_index.exists():
        data, _ = _load_yaml_safe(docs_index)
        if data:
            for entry in data.get("docs", []):
                p = root / entry.get("path", "")
                if not p.exists():
                    results.append(
                        ValidationResult(
                            check="index:path-check",
                            status="warn",
                            message=f"Referenced path not found: {entry.get('path')}",
                        )
                    )
                    break
            else:
                results.append(
                    ValidationResult(
                        check="index:path-check",
                        status="pass",
                        message="All referenced paths exist",
                    )
                )

    # 7. Stale handoffs (>30 days, no newer one) — warn only
    handoffs_dir = ai_dir / "handoffs"
    if handoffs_dir.is_dir():
        handoff_files = sorted(handoffs_dir.glob("*.md"))
        if handoff_files:
            newest = max(f.stat().st_mtime for f in handoff_files)
            age = datetime.now(UTC) - datetime.fromtimestamp(newest, tz=UTC)
            if age > timedelta(days=30):
                results.append(
                    ValidationResult(
                        check="handoffs",
                        status="warn",
                        message=f"Most recent handoff is {age.days} days old",
                    )
                )
            else:
                results.append(
                    ValidationResult(check="handoffs", status="pass", message="Handoffs are recent")
                )

    # 8. Active task file populated if ai.tasks enabled
    try:
        if ws_yaml.exists():
            from ai_workspace.core.config import load_workspace_yaml

            config = load_workspace_yaml(ws_yaml)
            if config.ai.tasks:
                task_file = ai_dir / "active-task" / "current-task.md"
                if task_file.exists() and task_file.stat().st_size > 0:
                    results.append(
                        ValidationResult(
                            check="active-task",
                            status="pass",
                            message="current-task.md is populated",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            check="active-task",
                            status="warn",
                            message="current-task.md is missing or empty",
                        )
                    )
    except Exception:
        pass

    # 9. Ownership check — warn if system-managed content found outside .ai/generated/
    human_dirs = [ai_dir / d for d in ("active-task", "handoffs", "context", "templates")]
    human_dirs.append(ai_dir)  # top-level .ai/ files
    for check_dir in human_dirs:
        if not check_dir.is_dir():
            continue
        for path in check_dir.glob("*.md"):
            try:
                if "managed_by: system" in path.read_text(encoding="utf-8", errors="ignore"):
                    results.append(
                        ValidationResult(
                            check="ownership",
                            status="warn",
                            message=f"System-managed file found outside generated/: {path.relative_to(ai_dir)}",
                        )
                    )
                    break
            except OSError:
                continue
        else:
            continue
        break
    else:
        results.append(
            ValidationResult(check="ownership", status="pass", message="No ownership violations")
        )

    return results
