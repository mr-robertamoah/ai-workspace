"""Security scanning hooks."""

from __future__ import annotations


def dependency_audit_command() -> list[str]:
    """Return the dependency audit command planned for later phases."""

    return ["pip-audit"]
