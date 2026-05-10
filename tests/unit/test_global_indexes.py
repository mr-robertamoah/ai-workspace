from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from ai_workspace.intelligence.indexes import (
    get_skills_index,
    rebuild_global_indexes,
    search_skills_index,
)

yaml = YAML(typ="safe")


def test_rebuild_global_indexes_on_empty_layer_produces_valid_empty_index_files(
    tmp_path: Path,
) -> None:
    rebuild_global_indexes(tmp_path)

    for name in [
        "skills-index.yaml",
        "standards-index.yaml",
        "templates-index.yaml",
        "tags-index.yaml",
    ]:
        path = tmp_path / "indexes" / name
        assert path.is_file()
        with path.open(encoding="utf-8") as handle:
            assert yaml.load(handle) is not None


def test_search_skills_index_finds_skills_matching_a_tag(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "terraform-module"
    skill_dir.mkdir(parents=True)
    (skill_dir / "skill.yaml").write_text(
        "name: terraform-module\n"
        "description: Terraform workflow\n"
        "tags:\n"
        "  - terraform\n"
        "  - infrastructure\n",
        encoding="utf-8",
    )
    rebuild_global_indexes(tmp_path)

    matches = search_skills_index(tmp_path, "terraform")

    assert matches[0]["name"] == "terraform-module"


def test_search_skills_index_is_case_insensitive(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skills" / "python-package"
    skill_dir.mkdir(parents=True)
    (skill_dir / "skill.yaml").write_text(
        "name: python-package\n"
        "description: FastAPI service template\n"
        "tags:\n"
        "  - backend\n",
        encoding="utf-8",
    )
    rebuild_global_indexes(tmp_path)

    matches = search_skills_index(tmp_path, "fastapi")

    assert matches[0]["name"] == "python-package"


def test_search_skills_index_with_no_matches_returns_empty_list(tmp_path: Path) -> None:
    rebuild_global_indexes(tmp_path)

    assert search_skills_index(tmp_path, "kubernetes") == []
    assert get_skills_index(tmp_path) == []
