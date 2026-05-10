"""Workspace summarization: dependency summary, repo map, tech detection."""

from __future__ import annotations

import tomllib
from pathlib import Path

from ai_workspace.core.config import WorkspaceConfig
from ai_workspace.workspace.detector import detect_project

_NOISE = {".git", "__pycache__", "node_modules", ".ai", "dist", "build", ".egg-info"}

_DIR_ANNOTATIONS = {
    "src": "source code",
    "tests": "test suite",
    "test": "test suite",
    "docs": "documentation",
}


def generate_repo_map(root: Path, max_depth: int = 2) -> str:
    """Markdown directory tree, excluding noise, annotating known dirs."""

    lines = [f"# Repo Map: {root.name}\n"]

    def _walk(path: Path, depth: int, prefix: str) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return
        for entry in entries:
            if entry.name in _NOISE or entry.name.startswith("."):
                continue
            annotation = ""
            if entry.is_dir():
                note = _DIR_ANNOTATIONS.get(entry.name, "")
                if note:
                    annotation = f"  ← {note}"
                file_count = sum(1 for f in entry.iterdir() if f.is_file()) if depth == 1 else 0
                count_str = f" ({file_count} files)" if depth == 1 and file_count else ""
                lines.append(f"{prefix}- {entry.name}/{count_str}{annotation}")
                _walk(entry, depth + 1, prefix + "  ")
            else:
                lines.append(f"{prefix}- {entry.name}")

    _walk(root, 1, "")
    return "\n".join(lines) + "\n"


def generate_dependency_summary(root: Path) -> str:
    """Markdown summary of all detected dependencies."""

    sections: list[str] = ["# Dependency Summary\n"]

    # requirements.txt
    req = root / "requirements.txt"
    if req.exists():
        lines = [
            ln.strip()
            for ln in req.read_text().splitlines()
            if ln.strip() and not ln.startswith("#")
        ]
        sections.append("## requirements.txt\n")
        sections.extend(f"- `{ln}`" for ln in lines)
        sections.append("")

    # pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            data = tomllib.loads(pyproject.read_text())
            deps = data.get("project", {}).get("dependencies", [])
            dev_deps = data.get("project", {}).get("optional-dependencies", {}).get(
                "dev", []
            ) or data.get("tool", {}).get("poetry", {}).get("dev-dependencies", {})
            if deps:
                sections.append("## pyproject.toml — dependencies\n")
                sections.extend(f"- `{d}`" for d in deps)
                sections.append("")
            if dev_deps:
                sections.append("## pyproject.toml — dev dependencies\n")
                if isinstance(dev_deps, list):
                    sections.extend(f"- `{d}`" for d in dev_deps)
                else:
                    sections.extend(f"- `{k}`" for k in dev_deps)
                sections.append("")
        except Exception:
            pass

    # package.json
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            import json

            pkg = json.loads(pkg_json.read_text())
            prod = pkg.get("dependencies", {})
            dev = pkg.get("devDependencies", {})
            if prod:
                sections.append("## package.json — dependencies\n")
                sections.extend(f"- `{k}`: {v}" for k, v in prod.items())
                sections.append("")
            if dev:
                sections.append("## package.json — devDependencies\n")
                sections.extend(f"- `{k}`: {v}" for k, v in dev.items())
                sections.append("")
        except Exception:
            pass

    # go.mod
    go_mod = root / "go.mod"
    if go_mod.exists():
        lines = go_mod.read_text().splitlines()
        in_require = False
        requires: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("require ("):
                in_require = True
                continue
            if in_require and stripped == ")":
                in_require = False
                continue
            if in_require and stripped:
                requires.append(stripped)
            elif stripped.startswith("require ") and not stripped.endswith("("):
                requires.append(stripped[len("require ") :].strip())
        if requires:
            sections.append("## go.mod — require\n")
            sections.extend(f"- `{r}`" for r in requires)
            sections.append("")

    if len(sections) == 1:
        sections.append("No known dependency files detected.\n")

    return "\n".join(sections)


_HUMAN_OWNED = {"project-summary.md", "architecture-summary.md", "current-state.md"}


def summarize_workspace(root: Path, config: WorkspaceConfig) -> dict[str, Path]:
    """Generate summary files in .ai/generated/. Never touches human-owned files."""

    generated = root / ".ai" / "generated"
    generated.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    repo_map_path = generated / "repo-map-generated.md"
    repo_map_path.write_text(generate_repo_map(root), encoding="utf-8")
    written["repo-map-generated.md"] = repo_map_path

    dep_path = generated / "dependency-summary.md"
    dep_path.write_text(generate_dependency_summary(root), encoding="utf-8")
    written["dependency-summary.md"] = dep_path

    tech_path = generated / "tech-detection.yaml"
    if not tech_path.exists():
        from ruamel.yaml import YAML

        detection = detect_project(root)
        yaml = YAML()
        yaml.default_flow_style = False
        data = {
            "languages": detection.languages,
            "frameworks": detection.frameworks,
            "package_managers": detection.package_managers,
            "ci_systems": detection.ci_systems,
            "has_tests": detection.has_tests,
            "has_docs": detection.has_docs,
        }
        with tech_path.open("w", encoding="utf-8") as fh:
            yaml.dump(data, fh)
    written["tech-detection.yaml"] = tech_path

    # Verify we never wrote to human-owned files
    for name in _HUMAN_OWNED:
        assert not (generated / name).exists() or name not in written

    return written
