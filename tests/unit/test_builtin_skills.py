"""Unit tests for built-in skills."""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from ai_workspace.intelligence.skills import SkillMetadata

_BUILTIN = Path(__file__).parent.parent.parent / "src" / "ai_workspace" / "data" / "skills"
_yaml = YAML(typ="safe")

EXPECTED = ["python-package", "terraform-module", "docker-service", "api-endpoint", "adr-creation"]


def test_all_five_builtin_skills_present():
    names = [d.name for d in _BUILTIN.iterdir() if d.is_dir()]
    for expected in EXPECTED:
        assert expected in names


def test_each_builtin_has_skill_yaml():
    for name in EXPECTED:
        assert (_BUILTIN / name / "skill.yaml").exists()


def test_each_builtin_skill_yaml_validates():
    for name in EXPECTED:
        raw = _yaml.load((_BUILTIN / name / "skill.yaml").read_text()) or {}
        skill = SkillMetadata(**raw)
        assert skill.name == name
