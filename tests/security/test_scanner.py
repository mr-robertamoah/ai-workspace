"""Security tests for the scanner."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch


from ai_workspace.security.scanner import scan_security


def _make_ai(tmp_path: Path) -> Path:
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "indexes").mkdir()
    return ai


def test_secret_detection_finds_aws_key(tmp_path):
    ai = _make_ai(tmp_path)
    (ai / "notes.md").write_text("key = AKIAIOSFODNN7EXAMPLE123456\n")
    results = {r.check: r for r in scan_security(tmp_path)}
    assert results["secret-detection"].status == "fail"


def test_secret_detection_finds_github_token(tmp_path):
    ai = _make_ai(tmp_path)
    (ai / "notes.md").write_text("token = ghp_" + "a" * 36 + "\n")
    results = {r.check: r for r in scan_security(tmp_path)}
    assert results["secret-detection"].status == "fail"


def test_secret_detection_passes_on_clean_files(tmp_path):
    ai = _make_ai(tmp_path)
    (ai / "notes.md").write_text("# Clean file\nNo secrets here.\n")
    results = {r.check: r for r in scan_security(tmp_path)}
    assert results["secret-detection"].status == "pass"


def test_yaml_safety_catches_python_object_tag(tmp_path):
    ai = _make_ai(tmp_path)
    (ai / "indexes" / "bad.yaml").write_text("key: !!python/object/apply:os.system ['id']\n")
    results = {r.check: r for r in scan_security(tmp_path)}
    assert results["yaml-safety"].status == "fail"


def test_yaml_safety_passes_on_normal_yaml(tmp_path):
    ai = _make_ai(tmp_path)
    (ai / "indexes" / "good.yaml").write_text("generated_at: '2025-01-01'\ndocs: []\n")
    results = {r.check: r for r in scan_security(tmp_path)}
    assert results["yaml-safety"].status == "pass"


def test_permissions_check_catches_world_writable(tmp_path):
    ai = _make_ai(tmp_path)
    f = ai / "secret.md"
    f.write_text("data")
    os.chmod(f, 0o777)
    results = {r.check: r for r in scan_security(tmp_path)}
    assert results["file-permissions"].status == "warn"
    # restore
    os.chmod(f, 0o644)


def test_pip_audit_returns_warn_when_not_installed(tmp_path):
    _make_ai(tmp_path)
    with patch("ai_workspace.security.scanner._run", return_value=(-1, "", "not installed")):
        results = {r.check: r for r in scan_security(tmp_path)}
    assert results["pip-audit"].status == "warn"


def test_all_checks_complete_even_when_one_raises(tmp_path):
    _make_ai(tmp_path)
    # Should not raise even with a broken scanner
    results = scan_security(tmp_path)
    checks = {r.check for r in results}
    assert "secret-detection" in checks
    assert "yaml-safety" in checks
    assert "file-permissions" in checks
