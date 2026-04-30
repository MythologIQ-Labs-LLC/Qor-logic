"""Phase 46 doctrine — negative-path tests (companion to test_doctrine_test_functionality.py).

Split from the parent file in Phase 52 to satisfy Section 4 Razor (250-line cap).
Each negative-path test mutates a section in-memory and asserts the corresponding
positive proximity-anchor test would fail under that mutation.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests._helpers import proximity as _proximity, strip_section as _strip_section

REPO_ROOT = Path(__file__).resolve().parent.parent

DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-test-functionality.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
QOR_PLAN = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-plan" / "SKILL.md"
QOR_AUDIT = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
QOR_IMPLEMENT = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-implement" / "SKILL.md"
QOR_SUBSTANTIATE = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# /qor-audit section header constants (used by audit-pass negative-paths)
RAZOR_HEADER = r"^#### Section 4 Razor Pass\b"
TEST_FUNC_HEADER = r"^#### Test Functionality Pass\b"
DEP_HEADER = r"^#### Dependency Audit\b"


# -------- Doctrine file --------

REQUIRED_DOCTRINE_SECTIONS = (
    r"^## Principle\b",
    r"^## Definitions\b",
    r"^## Rule\b",
    r"^## Anti-patterns\b",
    r"^## Verification mechanisms\b",
    r"^## Update protocol\b",
)



def test_doctrine_required_sections_negative_path():
    """Drop the Principle header and prove the section assertion fails."""
    body = _read(DOCTRINE)
    mutated = re.sub(r"^## Principle\b", "## DROPPED", body, count=1, flags=re.MULTILINE)
    assert not re.search(r"^## Principle\b", mutated, re.MULTILINE), (
        "strip mutation failed; negative-path test cannot run"
    )
def test_doctrine_anti_patterns_proximity_anchor_negative_path():
    body = _read(DOCTRINE)
    mutated = _strip_section(body, r"^## Anti-patterns")
    assert not _proximity(mutated, r"^## Anti-patterns\b", r"SG-035", span=2000), (
        "After stripping Anti-patterns body, proximity check must fail"
    )


# -------- CLAUDE.md Authority --------
def test_claude_md_authority_negative_path():
    body = _read(CLAUDE_MD)
    mutated = _strip_section(body, r"^## Authority")
    assert not _proximity(mutated, r"^## Authority\b", r"doctrine-test-functionality\.md", span=1000)


# -------- /qor-plan --------
def test_qor_audit_test_functionality_pass_position_negative_path():
    body = _read(QOR_AUDIT)
    mutated = _strip_section(body, TEST_FUNC_HEADER)
    # Header line itself remains under _strip_section semantics; remove it explicitly:
    mutated = re.sub(TEST_FUNC_HEADER + r".*?\n", "", mutated, count=1, flags=re.MULTILINE)
    assert not re.search(TEST_FUNC_HEADER, mutated, re.MULTILINE), (
        "negative-path: Test Functionality Pass header successfully stripped"
    )
def test_qor_audit_test_functionality_pass_veto_negative_path():
    body = _read(QOR_AUDIT)
    mutated = _strip_section(body, TEST_FUNC_HEADER)
    assert not _proximity(mutated, TEST_FUNC_HEADER, r"VETO", span=2000)


# -------- /qor-implement --------
def test_qor_substantiate_seal_gate_negative_path():
    body = _read(QOR_SUBSTANTIATE)
    mutated = _strip_section(body, r"^#### Test Audit")
    assert not _proximity(
        mutated,
        r"^#### Test Audit\b",
        r"presence-only",
        span=2500,
    )

def test_qor_plan_step4_negative_path():
    body = _read(QOR_PLAN)
    mutated = _strip_section(body, r"^### Step 4: Avoid Common Pitfalls")
    assert not _proximity(
        mutated,
        r"^### Step 4: Avoid Common Pitfalls\b",
        r"tests that only assert presence",
        span=2000,
    )

def test_qor_plan_step5_negative_path():
    body = _read(QOR_PLAN)
    mutated = _strip_section(body, r"^### Step 5: Review Plan")
    assert not _proximity(
        mutated,
        r"^### Step 5: Review Plan\b",
        r"names the behavior it confirms",
        span=2000,
    )


# -------- /qor-audit --------

RAZOR_HEADER = r"^#### Section 4 Razor Pass\b"
TEST_FUNC_HEADER = r"^#### Test Functionality Pass\b"
DEP_HEADER = r"^#### Dependency Audit\b"

def test_qor_implement_step5_negative_path():
    body = _read(QOR_IMPLEMENT)
    mutated = _strip_section(body, r"^### Step 5: TDD-Light")
    assert not _proximity(
        mutated,
        r"^### Step 5: TDD-Light\b",
        r"invoke the unit under test",
        span=2000,
    )

def test_qor_implement_step9_negative_path():
    body = _read(QOR_IMPLEMENT)
    mutated = _strip_section(body, r"^### Step 9: Complexity Self-Check")
    assert not _proximity(
        mutated,
        r"^### Step 9: Complexity Self-Check\b",
        r"presence-only",
        span=2000,
    )


# -------- /qor-substantiate --------
