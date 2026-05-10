"""Unit tests for the skills manager."""

from __future__ import annotations


import pytest

from ai_workspace.core.errors import SkillError
from ai_workspace.intelligence.skills import (
    SkillMetadata,
    accept_skill,
    ensure_builtin_skills,
    get_skill,
    list_proposed_skills,
    list_skills,
    propose_skill,
    rebuild_skills_index,
    search_skills,
)


@pytest.fixture()
def global_root(tmp_path):
    ensure_builtin_skills(tmp_path)
    return tmp_path


def test_list_skills_returns_builtins(global_root):
    skills = list_skills(global_root)
    assert len(skills) >= 5
    names = [s.name for s in skills]
    assert "python-package" in names
    assert "terraform-module" in names


def test_list_skills_excludes_proposed(global_root):
    # create a proposed skill
    (global_root / "skills" / "my-skill-proposed").mkdir(parents=True)
    (global_root / "skills" / "my-skill-proposed" / "skill.yaml").write_text(
        "name: my-skill\nversion: '1.0.0'\ndescription: test\ntags: []\n"
    )
    skills = list_skills(global_root)
    assert all(not s.name.endswith("-proposed") for s in skills)


def test_list_proposed_returns_only_proposed(global_root):
    (global_root / "skills" / "my-skill-proposed").mkdir(parents=True)
    (global_root / "skills" / "my-skill-proposed" / "skill.yaml").write_text(
        "name: my-skill\nversion: '1.0.0'\ndescription: test\ntags: []\n"
    )
    proposed = list_proposed_skills(global_root)
    assert len(proposed) == 1
    assert proposed[0].name == "my-skill"


def test_get_skill_returns_correct_skill(global_root):
    skill = get_skill(global_root, "python-package")
    assert skill.name == "python-package"


def test_get_skill_raises_for_unknown(global_root):
    with pytest.raises(SkillError):
        get_skill(global_root, "nonexistent-skill")


def test_search_skills_by_name(global_root):
    results = search_skills(global_root, "python")
    assert any(s.name == "python-package" for s in results)


def test_search_skills_by_tag(global_root):
    results = search_skills(global_root, "terraform")
    assert any(s.name == "terraform-module" for s in results)


def test_search_skills_case_insensitive(global_root):
    results = search_skills(global_root, "DOCKER")
    assert any(s.name == "docker-service" for s in results)


def test_search_skills_no_match_returns_empty(global_root):
    results = search_skills(global_root, "zzznomatch")
    assert results == []


def test_propose_skill_creates_proposed_dir(global_root):
    meta = SkillMetadata(name="my-new-skill", description="A test skill", tags=["test"])
    path = propose_skill(global_root, meta)
    assert path.name == "my-new-skill-proposed"
    assert (path / "skill.yaml").exists()


def test_propose_skill_raises_if_already_exists(global_root):
    meta = SkillMetadata(name="dup-skill", description="dup", tags=[])
    propose_skill(global_root, meta)
    with pytest.raises(SkillError):
        propose_skill(global_root, meta)


def test_accept_skill_renames_proposed(global_root):
    meta = SkillMetadata(name="accept-me", description="test", tags=[])
    propose_skill(global_root, meta)
    target = accept_skill(global_root, "accept-me")
    assert target.name == "accept-me"
    assert target.exists()
    assert not (global_root / "skills" / "accept-me-proposed").exists()


def test_accept_skill_raises_if_no_proposed(global_root):
    with pytest.raises(SkillError):
        accept_skill(global_root, "ghost-skill")


def test_rebuild_skills_index_returns_count(global_root):
    count = rebuild_skills_index(global_root)
    assert count >= 5


def test_rebuild_skills_index_writes_valid_yaml(global_root):
    rebuild_skills_index(global_root)
    index = global_root / "indexes" / "skills-index.yaml"
    assert index.exists()
    from ruamel.yaml import YAML

    data = YAML(typ="safe").load(index.read_text())
    assert "skills" in data
