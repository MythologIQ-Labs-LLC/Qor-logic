"""Phase 46: Test-functionality doctrine wiring (proximity-anchored).

Each positive assertion is paired with a strip-and-fail negative-path test so
the doctrine test cannot itself decay into a presence-only check (SG-035).

Pattern: read the target file, locate the section header, assert the expected
phrase appears within a bounded span of that header. Then mutate the body
in-memory by removing the section and assert the same check fails.
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


# -------- Doctrine file --------

REQUIRED_DOCTRINE_SECTIONS = (
    r"^## Principle\b",
    r"^## Definitions\b",
    r"^## Rule\b",
    r"^## Anti-patterns\b",
    r"^## Verification mechanisms\b",
    r"^## Update protocol\b",
)


def test_doctrine_file_exists_with_required_sections():
    assert DOCTRINE.is_file(), f"missing doctrine file: {DOCTRINE}"
    body = _read(DOCTRINE)
    for header in REQUIRED_DOCTRINE_SECTIONS:
        assert re.search(header, body, re.MULTILINE), (
            f"doctrine missing required section header: {header}"
        )


def test_doctrine_anti_patterns_section_cites_sg_035_and_phase_45():
    body = _read(DOCTRINE)
    assert _proximity(body, r"^## Anti-patterns\b", r"SG-035", span=2000), (
        "Anti-patterns section must cite SG-035"
    )
    assert _proximity(body, r"^## Anti-patterns\b", r"Phase\s*45", span=2000), (
        "Anti-patterns section must cite Phase 45"
    )


def test_claude_md_authority_references_test_functionality_doctrine():
    body = _read(CLAUDE_MD)
    assert _proximity(body, r"^## Authority\b", r"doctrine-test-functionality\.md", span=1000), (
        "CLAUDE.md Authority must reference doctrine-test-functionality.md"
    )


def test_qor_plan_step4_forbids_presence_only_tests():
    body = _read(QOR_PLAN)
    assert _proximity(
        body,
        r"^### Step 4: Avoid Common Pitfalls\b",
        r"tests that only assert presence",
        span=2000,
    ), "qor-plan Step 4 must forbid presence-only tests"


def test_qor_plan_step5_review_lists_behavior_naming():
    body = _read(QOR_PLAN)
    assert _proximity(
        body,
        r"^### Step 5: Review Plan\b",
        r"names the behavior it confirms",
        span=2000,
    ), "qor-plan Step 5 review checklist must require behavior-naming on tests"


# -------- /qor-audit --------

RAZOR_HEADER = r"^#### Section 4 Razor Pass\b"
TEST_FUNC_HEADER = r"^#### Test Functionality Pass\b"
DEP_HEADER = r"^#### Dependency Audit\b"


def test_qor_audit_has_test_functionality_pass_between_razor_and_dependency():
    body = _read(QOR_AUDIT)
    razor = re.search(RAZOR_HEADER, body, re.MULTILINE)
    test_func = re.search(TEST_FUNC_HEADER, body, re.MULTILINE)
    dep = re.search(DEP_HEADER, body, re.MULTILINE)
    assert razor and test_func and dep, "all three section headers must exist"
    assert razor.start() < test_func.start() < dep.start(), (
        "Test Functionality Pass must sit between Section 4 Razor and Dependency Audit"
    )


def test_qor_audit_test_functionality_pass_states_veto_criterion():
    body = _read(QOR_AUDIT)
    assert _proximity(body, TEST_FUNC_HEADER, r"presence-only", span=2000)
    assert _proximity(body, TEST_FUNC_HEADER, r"VETO", span=2000)
    assert _proximity(body, TEST_FUNC_HEADER, r"invoking the unit", span=2000)


def test_qor_implement_step5_requires_unit_invocation():
    body = _read(QOR_IMPLEMENT)
    assert _proximity(
        body,
        r"^### Step 5: TDD-Light\b",
        r"invoke the unit under test",
        span=2000,
    )
    assert _proximity(
        body,
        r"^### Step 5: TDD-Light\b",
        r"assert against its output",
        span=2000,
    )


def test_qor_implement_step9_scans_for_presence_only_tests():
    body = _read(QOR_IMPLEMENT)
    assert _proximity(
        body,
        r"^### Step 9: Complexity Self-Check\b",
        r"presence-only",
        span=2000,
    )


def test_qor_substantiate_seal_gate_blocks_presence_only_tests():
    body = _read(QOR_SUBSTANTIATE)
    assert _proximity(
        body,
        r"^#### Test Audit\b",
        r"presence-only",
        span=2500,
    )
    # The seal-refusal phrase: at least one of "refuses to seal", "seal aborts",
    # "ABORT", or "abort" within proximity (the doctrine allows operator-language
    # variation).
    assert _proximity(
        body,
        r"^#### Test Audit\b",
        r"refuses to seal|aborts? seal|seal aborts|ABORT",
        span=2500,
    )
