"""Validation hooks for workspace security checks."""

from __future__ import annotations


def configured_security_checks() -> list[str]:
    """Return the security checks named in the implementation spec."""

    return ["dependency_scanning", "bandit"]
