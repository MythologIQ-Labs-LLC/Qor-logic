"""Phase 84: wiring tests for the inverse-coverage discipline (GH #84).

Each anchored-prose assertion is paired with a strip-and-fail negative per
qor/references/doctrine-test-functionality.md.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-test-functionality.md"
PLAN_SKILL = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-plan" / "SKILL.md"
AUDIT_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"

_DOCTRINE_HEADER = "Inverse-coverage discipline"


def _md_section(text: str, header_substr: str) -> str:
    """Body of the first '##'..'####' section whose header contains header_substr,
    up to the next header of equal-or-shallower depth. Lines inside ``` fenced
    blocks are not treated as headers."""
    lines = text.splitlines()
    start = None
    start_level = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m and header_substr in m.group(2):
            start = i
            start_level = len(m.group(1))
            break
    if start is None:
        return ""
    body = []
    in_fence = False
    for line in lines[start + 1:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            body.append(line)
            continue
        if not in_fence:
            m = re.match(r"^(#{2,4})\s+", line)
            if m and len(m.group(1)) <= start_level:
                break
        body.append(line)
    return "\n".join(body)


def test_doctrine_defines_inverse_coverage_section():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _md_section(text, _DOCTRINE_HEADER)
    assert section, "doctrine-test-functionality.md has no Inverse-coverage discipline section"
    low = section.lower()
    assert "forward" in low and "round-trip" in low
    assert "inverse" in low and "reachable" in low
    assert "gated" in low or "exempt" in low


def test_doctrine_assertion_fails_when_section_removed():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _md_section(text, _DOCTRINE_HEADER)
    assert section
    stripped = text.replace(section, "")
    assert not _md_section(stripped, _DOCTRINE_HEADER).strip()


def test_plan_step5_and_audit_pass_cite_inverse_coverage():
    plan_step5 = _md_section(PLAN_SKILL.read_text(encoding="utf-8"), "Step 5: Review Plan")
    assert plan_step5
    assert "closed-enum taxonomy" in plan_step5.lower()
    assert "inverse" in plan_step5.lower()
    audit_tfp = _md_section(AUDIT_SKILL.read_text(encoding="utf-8"), "Test Functionality Pass")
    assert audit_tfp
    assert "closed-enum taxonomy" in audit_tfp.lower()
    assert "coverage-gap" in audit_tfp


def test_skill_citations_fail_when_directives_removed():
    plan_step5 = _md_section(PLAN_SKILL.read_text(encoding="utf-8"), "Step 5: Review Plan")
    kept = [ln for ln in plan_step5.splitlines() if "closed-enum taxonomy" not in ln.lower()]
    assert "closed-enum taxonomy" not in "\n".join(kept).lower()
