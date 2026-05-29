"""Phase 23 Track B: OWASP governance integration tests."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE_PATH = REPO_ROOT / "qor" / "references" / "doctrine-owasp-governance.md"
AUDIT_SKILL_PATH = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
CEDAR_PATH = REPO_ROOT / "qor" / "policies" / "owasp_enforcement.cedar"


def test_owasp_doctrine_exists():
    assert DOCTRINE_PATH.exists(), f"Missing {DOCTRINE_PATH}"
    body = DOCTRINE_PATH.read_text(encoding="utf-8")
    assert len(body) > 200


def test_owasp_doctrine_has_categories():
    body = DOCTRINE_PATH.read_text(encoding="utf-8")
    for cat in ("A03", "A04", "A05", "A08"):
        assert cat in body, f"Missing OWASP category {cat}"


def test_audit_skill_has_owasp_pass():
    body = AUDIT_SKILL_PATH.read_text(encoding="utf-8")
    assert "OWASP Top 10 Pass" in body  # prose-lint: ok=prompt-contract: named prompt pass


def test_cedar_policies_exist():
    assert CEDAR_PATH.exists()


def test_cedar_forbid_shell_true():
    body = CEDAR_PATH.read_text(encoding="utf-8")
    assert "has_shell_true" in body


def test_cedar_forbid_unsafe_deserialization():
    body = CEDAR_PATH.read_text(encoding="utf-8")
    assert "has_unsafe_deserialization" in body


def test_no_shell_true_in_production():
    """Static grep: no shell=True in production Python files."""
    qor_dir = REPO_ROOT / "qor"
    violations = []
    for py in qor_dir.rglob("*.py"):
        if "test" in py.name.lower():
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if "shell=True" in line and not line.strip().startswith("#"):
                violations.append(f"{py.relative_to(REPO_ROOT)}:{i}")
    assert not violations, f"shell=True found: {violations}"


def test_no_unsafe_deserialization_in_production():
    """Static grep: no pickle.load/eval/exec/yaml.load without SafeLoader."""
    qor_dir = REPO_ROOT / "qor"
    unsafe = re.compile(r"\b(pickle\.loads?|eval\(|exec\(|yaml\.load\()")
    violations = []
    for py in qor_dir.rglob("*.py"):
        if "test" in py.name.lower():
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if unsafe.search(line) and not line.strip().startswith("#"):
                # Allow yaml.safe_load
                if "yaml.load(" in line and "SafeLoader" not in line:
                    violations.append(f"{py.relative_to(REPO_ROOT)}:{i}")
                elif "yaml.load(" not in line:
                    violations.append(f"{py.relative_to(REPO_ROOT)}:{i}")
    assert not violations, f"Unsafe deserialization found: {violations}"
