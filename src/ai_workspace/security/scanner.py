"""Security scanning: pip-audit, bandit, secret detection, YAML safety, permissions."""

from __future__ import annotations

import json
import re
import stat
import subprocess
from pathlib import Path

from ai_workspace.security.validator import ValidationResult

SECRET_PATTERNS = [
    r'password\s*=\s*["\'][^"\']{4,}["\']',
    r'api_key\s*=\s*["\'][^"\']{8,}["\']',
    r'secret\s*=\s*["\'][^"\']{8,}["\']',
    r'token\s*=\s*["\'][^"\']{16,}["\']',
    r"AKIA[0-9A-Z]{16}",
    r"ghp_[a-zA-Z0-9]{36}",
]
_SECRET_RE = re.compile("|".join(SECRET_PATTERNS), re.IGNORECASE)


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=cwd)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return -1, "", "not installed"
    except subprocess.TimeoutExpired:
        return -2, "", "timed out"
    except Exception as exc:
        return -3, "", str(exc)


def _scan_secrets(root: Path) -> ValidationResult:
    scan_dirs = [root / ".ai", root / "docs"]
    for scan_dir in scan_dirs:
        if not scan_dir.is_dir():
            continue
        for path in scan_dir.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if _SECRET_RE.search(text):
                    return ValidationResult(
                        check="secret-detection",
                        status="fail",
                        message=f"Potential secret found in {path.relative_to(root)}",
                    )
            except OSError:
                continue
    return ValidationResult(check="secret-detection", status="pass", message="No secrets detected")


def _scan_yaml_safety(root: Path) -> ValidationResult:
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return ValidationResult(check="yaml-safety", status="pass", message="No .ai/ to scan")
    for path in ai_dir.rglob("*.yaml"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "!!python/object" in text:
                return ValidationResult(
                    check="yaml-safety",
                    status="fail",
                    message=f"Unsafe YAML tag in {path.relative_to(root)}",
                )
        except OSError:
            continue
    return ValidationResult(check="yaml-safety", status="pass", message="All YAML files are safe")


def _scan_permissions(root: Path) -> ValidationResult:
    ai_dir = root / ".ai"
    if not ai_dir.is_dir():
        return ValidationResult(check="file-permissions", status="pass", message="No .ai/ to check")
    for path in ai_dir.rglob("*"):
        if path.is_file():
            try:
                mode = path.stat().st_mode
                if mode & stat.S_IWOTH:
                    return ValidationResult(
                        check="file-permissions",
                        status="warn",
                        message=f"World-writable file: {path.relative_to(root)}",
                    )
            except OSError:
                continue
    return ValidationResult(
        check="file-permissions", status="pass", message="No world-writable files"
    )


def scan_security(root: Path) -> list[ValidationResult]:
    results: list[ValidationResult] = []

    # 1. pip-audit
    rc, stdout, stderr = _run(["pip-audit", "--format=json"], root)
    if rc == -1:
        results.append(
            ValidationResult(check="pip-audit", status="warn", message="pip-audit not installed")
        )
    elif rc == -2:
        results.append(
            ValidationResult(check="pip-audit", status="warn", message="pip-audit timed out")
        )
    elif rc != 0:
        try:
            data = json.loads(stdout)
            vulns = [d for d in data.get("dependencies", []) if d.get("vulns")]
            count = sum(len(d["vulns"]) for d in vulns)
            results.append(
                ValidationResult(check="pip-audit", status="fail", message=f"{count} CVE(s) found")
            )
        except Exception:
            results.append(
                ValidationResult(check="pip-audit", status="warn", message=f"pip-audit exited {rc}")
            )
    else:
        results.append(
            ValidationResult(check="pip-audit", status="pass", message="No known vulnerabilities")
        )

    # 2. bandit
    src_dir = root / "src"
    if src_dir.is_dir():
        rc, stdout, stderr = _run(["bandit", "-r", str(src_dir), "-f", "json", "-q"], root)
        if rc == -1:
            results.append(
                ValidationResult(check="bandit", status="warn", message="bandit not installed")
            )
        elif rc == -2:
            results.append(
                ValidationResult(check="bandit", status="warn", message="bandit timed out")
            )
        else:
            try:
                data = json.loads(stdout)
                high = [r for r in data.get("results", []) if r.get("issue_severity") == "HIGH"]
                if high:
                    results.append(
                        ValidationResult(
                            check="bandit",
                            status="fail",
                            message=f"{len(high)} HIGH severity finding(s)",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            check="bandit", status="pass", message="No HIGH severity findings"
                        )
                    )
            except Exception:
                results.append(
                    ValidationResult(check="bandit", status="pass", message="bandit completed")
                )
    else:
        results.append(
            ValidationResult(check="bandit", status="pass", message="No src/ directory to scan")
        )

    # 3. Secret detection
    try:
        results.append(_scan_secrets(root))
    except Exception as exc:
        results.append(
            ValidationResult(
                check="secret-detection", status="warn", message=f"Scanner error: {exc}"
            )
        )

    # 4. YAML safety
    try:
        results.append(_scan_yaml_safety(root))
    except Exception as exc:
        results.append(
            ValidationResult(check="yaml-safety", status="warn", message=f"Scanner error: {exc}")
        )

    # 5. File permissions
    try:
        results.append(_scan_permissions(root))
    except Exception as exc:
        results.append(
            ValidationResult(
                check="file-permissions", status="warn", message=f"Scanner error: {exc}"
            )
        )

    return results
