"""Skill discovery, search, and governance."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator
from ruamel.yaml import YAML

from ai_workspace.core.errors import SkillError
from ai_workspace.intelligence.indexes import rebuild_global_indexes

_yaml = YAML(typ="safe")
_yaml_w = YAML()
_yaml_w.default_flow_style = False

_BUILTIN_SKILLS = Path(__file__).parent.parent / "data" / "skills"


class SkillMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    version: str = "1.0.0"
    description: str = ""
    tags: list[str] = []
    author: str = "human"
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    validation: list[str] = []
    related_skills: list[str] = []

    @field_validator("name")
    @classmethod
    def name_kebab(cls, v: str) -> str:
        return v.strip()


def _load_skill(skill_dir: Path) -> SkillMetadata:
    skill_yaml = skill_dir / "skill.yaml"
    if not skill_yaml.exists():
        raise SkillError(f"No skill.yaml in {skill_dir}")
    raw = _yaml.load(skill_yaml.read_text(encoding="utf-8")) or {}
    return SkillMetadata(**raw)


def _skills_root(global_root: Path) -> Path:
    return global_root / "skills"


def ensure_builtin_skills(global_root: Path) -> None:
    """Copy bundled skills to global layer if not already present."""
    skills_root = _skills_root(global_root)
    skills_root.mkdir(parents=True, exist_ok=True)
    for src in _BUILTIN_SKILLS.iterdir():
        if src.is_dir():
            dst = skills_root / src.name
            if not dst.exists():
                shutil.copytree(src, dst)


def list_skills(global_root: Path) -> list[SkillMetadata]:
    """Return all active (non-proposed) skills."""
    skills_root = _skills_root(global_root)
    if not skills_root.exists():
        return []
    result = []
    for d in sorted(skills_root.iterdir()):
        if d.is_dir() and not d.name.endswith("-proposed") and (d / "skill.yaml").exists():
            result.append(_load_skill(d))
    return result


def list_proposed_skills(global_root: Path) -> list[SkillMetadata]:
    """Return all proposed skills."""
    skills_root = _skills_root(global_root)
    if not skills_root.exists():
        return []
    result = []
    for d in sorted(skills_root.iterdir()):
        if d.is_dir() and d.name.endswith("-proposed") and (d / "skill.yaml").exists():
            result.append(_load_skill(d))
    return result


def get_skill(global_root: Path, name: str) -> SkillMetadata:
    """Return a skill by name. Raises SkillError if not found."""
    skill_dir = _skills_root(global_root) / name
    if not skill_dir.exists() or not (skill_dir / "skill.yaml").exists():
        raise SkillError(f"Skill '{name}' not found.")
    return _load_skill(skill_dir)


def search_skills(global_root: Path, query: str) -> list[SkillMetadata]:
    """Case-insensitive search across name, description, tags."""
    needle = query.casefold()
    return [
        s
        for s in list_skills(global_root)
        if needle in s.name.casefold()
        or needle in s.description.casefold()
        or any(needle in t.casefold() for t in s.tags)
    ]


def propose_skill(global_root: Path, metadata: SkillMetadata) -> Path:
    """Write a proposed skill to <name>-proposed/."""
    proposed_dir = _skills_root(global_root) / f"{metadata.name}-proposed"
    if proposed_dir.exists():
        raise SkillError(f"Proposed skill '{metadata.name}' already exists.")
    proposed_dir.mkdir(parents=True)
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    data = metadata.model_dump()
    data.setdefault("created_at", now)
    data["updated_at"] = now
    data["author"] = "ai-proposed"
    with (proposed_dir / "skill.yaml").open("w", encoding="utf-8") as fh:
        _yaml_w.dump(data, fh)
    (proposed_dir / "notes.md").write_text(f"# Notes: {metadata.name}\n\n", encoding="utf-8")
    rebuild_skills_index(global_root)
    return proposed_dir


def accept_skill(global_root: Path, name: str) -> Path:
    """Rename <name>-proposed/ to <name>/."""
    proposed_dir = _skills_root(global_root) / f"{name}-proposed"
    if not proposed_dir.exists():
        raise SkillError(f"No proposed skill '{name}' found.")
    target = _skills_root(global_root) / name
    proposed_dir.rename(target)
    rebuild_skills_index(global_root)
    return target


def rebuild_skills_index(global_root: Path) -> int:
    """Rebuild skills-index.yaml. Returns count of active skills."""
    rebuild_global_indexes(global_root)
    return len(list_skills(global_root))
