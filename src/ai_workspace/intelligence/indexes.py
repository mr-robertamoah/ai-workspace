"""Global index management for the intelligence layer."""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML(typ="safe")
yaml_writer = YAML()
yaml_writer.default_flow_style = False


def index_filenames() -> list[str]:
    """Return the expected index filenames for the global layer."""

    return [
        "skills-index.yaml",
        "standards-index.yaml",
        "templates-index.yaml",
        "tags-index.yaml",
    ]


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml_writer.dump(data, handle)


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.load(path.read_text(encoding="utf-8")) or {}


def rebuild_global_indexes(global_root: Path) -> None:
    """Scan the global intelligence layer and rebuild its index files."""

    indexes_root = global_root / "indexes"
    skills_root = global_root / "skills"
    standards_root = global_root / "standards"
    templates_root = global_root / "templates"

    indexes_root.mkdir(parents=True, exist_ok=True)
    skills_root.mkdir(parents=True, exist_ok=True)
    standards_root.mkdir(parents=True, exist_ok=True)
    templates_root.mkdir(parents=True, exist_ok=True)

    skills: list[dict] = []
    tags: dict[str, list[str]] = {}
    for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        skill_yaml = skill_dir / "skill.yaml"
        if not skill_yaml.exists():
            continue
        metadata = _load_yaml(skill_yaml)
        entry = {
            "name": metadata.get("name", skill_dir.name),
            "description": metadata.get("description", ""),
            "tags": [str(tag) for tag in metadata.get("tags", [])],
            "status": metadata.get("status", "draft"),
            "path": str(skill_dir.relative_to(global_root)),
        }
        skills.append(entry)
        for tag in entry["tags"]:
            tags.setdefault(tag, []).append(entry["name"])

    standards = [
        {"name": path.stem, "path": str(path.relative_to(global_root))}
        for path in sorted(standards_root.glob("*.md"))
    ]
    templates = [
        {"name": path.stem, "path": str(path.relative_to(global_root))}
        for path in sorted(templates_root.rglob("*"))
        if path.is_file()
    ]

    _write_yaml(indexes_root / "skills-index.yaml", {"skills": skills})
    _write_yaml(indexes_root / "standards-index.yaml", {"standards": standards})
    _write_yaml(indexes_root / "templates-index.yaml", {"templates": templates})
    _write_yaml(indexes_root / "tags-index.yaml", {"tags": tags})


def get_skills_index(global_root: Path) -> list[dict]:
    """Return all skill entries from the global skills index."""

    data = _load_yaml(global_root / "indexes" / "skills-index.yaml")
    return list(data.get("skills", []))


def search_skills_index(global_root: Path, query: str) -> list[dict]:
    """Perform a case-insensitive substring search across skill metadata."""

    needle = query.casefold()
    matches: list[dict] = []
    for entry in get_skills_index(global_root):
        haystacks = [
            str(entry.get("name", "")),
            str(entry.get("description", "")),
            " ".join(str(tag) for tag in entry.get("tags", [])),
        ]
        if any(needle in haystack.casefold() for haystack in haystacks):
            matches.append(entry)
    return matches
