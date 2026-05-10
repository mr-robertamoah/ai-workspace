"""Static technology detection for existing repositories."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DetectionResult:
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    ci_systems: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_docs: bool = False
    entry_points: list[Path] = field(default_factory=list)
    config_files: list[Path] = field(default_factory=list)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def detect_project(root: Path) -> DetectionResult:
    """Detect technology stack via static file inspection only."""

    result = DetectionResult()

    # Language + package manager detection
    if (root / "pyproject.toml").exists():
        result.config_files.append(root / "pyproject.toml")
        if "python" not in result.languages:
            result.languages.append("python")
        if "pip" not in result.package_managers:
            result.package_managers.append("pip")
    if (root / "requirements.txt").exists():
        result.config_files.append(root / "requirements.txt")
        if "python" not in result.languages:
            result.languages.append("python")
        if "pip" not in result.package_managers:
            result.package_managers.append("pip")
    if (root / "package.json").exists():
        result.config_files.append(root / "package.json")
        if "nodejs" not in result.languages:
            result.languages.append("nodejs")
        pkg_text = _read_text(root / "package.json")
        if "yarn.lock" in os.listdir(root) if root.is_dir() else []:
            result.package_managers.append("yarn")
        else:
            result.package_managers.append("npm")
    if (root / "go.mod").exists():
        result.config_files.append(root / "go.mod")
        if "go" not in result.languages:
            result.languages.append("go")
        result.package_managers.append("go")
    if (root / "Cargo.toml").exists():
        result.config_files.append(root / "Cargo.toml")
        if "rust" not in result.languages:
            result.languages.append("rust")
    if (root / "pom.xml").exists() or (root / "build.gradle").exists():
        if "java" not in result.languages:
            result.languages.append("java")
    tf_files = list(root.glob("*.tf"))
    if tf_files:
        if "terraform" not in result.languages:
            result.languages.append("terraform")

    if not result.languages:
        result.languages.append("other")

    # Framework detection
    req_text = _read_text(root / "requirements.txt").lower()
    pyproject_text = _read_text(root / "pyproject.toml").lower()
    combined_python = req_text + pyproject_text
    if "fastapi" in combined_python:
        result.frameworks.append("fastapi")
    if "django" in combined_python:
        result.frameworks.append("django")
    if (root / "package.json").exists():
        pkg_text = _read_text(root / "package.json").lower()
        if '"express"' in pkg_text:
            result.frameworks.append("express")
        if '"next"' in pkg_text:
            result.frameworks.append("nextjs")
    if tf_files:
        for tf in tf_files:
            if "provider" in _read_text(tf).lower():
                if "terraform" not in result.frameworks:
                    result.frameworks.append("terraform")
                break

    # CI detection
    if (root / ".github" / "workflows").exists():
        result.ci_systems.append("github-actions")
    if (root / ".gitlab-ci.yml").exists():
        result.ci_systems.append("gitlab-ci")
    if (root / "Jenkinsfile").exists():
        result.ci_systems.append("jenkins")
    if (root / ".circleci").exists():
        result.ci_systems.append("circleci")

    # Test presence
    for name in ("tests", "test", "__tests__"):
        if (root / name).is_dir():
            result.has_tests = True
            break

    # Docs presence
    result.has_docs = (root / "docs").is_dir()

    # Entry points
    for candidate in ("src/main.py", "main.py", "app.py", "src/app.py", "index.js", "src/index.js"):
        p = root / candidate
        if p.exists():
            result.entry_points.append(p)

    return result
