"""Phase 68 (#50): qor-audit Step 1.a Option B independent reviewer codification.

The independent-adversarial-reviewer pattern was operational only
(SG-007 narrative reference); Phase 68 codifies it in the skill prompt
itself so the pattern is portable, enforceable, and operator-visible.
"""
from __future__ import annotations

from pathlib import Path

SKILL_PATH = Path("qor/skills/governance/qor-audit/SKILL.md")


def _text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _step_1a_region(text: str) -> str:
    """Return the body of Step 1.a up to Step 2."""
    start = text.find("**Step 1.a")
    if start < 0:
        start = text.find("### Step 1.a")
    assert start >= 0, "Step 1.a anchor missing"
    end = text.find("### Step 2:", start + 10)
    return text[start:end] if end > 0 else text[start:]


def test_skill_prose_names_option_b_independent_reviewer():
    body = _step_1a_region(_text())
    assert "Option B" in body, (
        "Step 1.a must name 'Option B' alongside the existing Option A "
        "(Phase 68; GH #50)"
    )
    assert "independent" in body.lower() and "reviewer" in body.lower(), (
        "Option B prose must describe the independent reviewer pattern"
    )


def test_skill_prose_cites_sg_007_origin():
    body = _step_1a_region(_text())
    cites_sg007 = "SG-007" in body or "SG-AuthorAuditMomentum" in body
    cites_pattern = (
        "self-audit" in body.lower()
        or "verification scope bias" in body.lower()
        or "author-audit momentum" in body.lower()
    )
    assert cites_sg007 or cites_pattern, (
        "Option B prose must cite SG-007 origin or the pattern name "
        "(self-audit verification scope bias / author-audit momentum)"
    )


def test_skill_prose_names_dispatch_protocol_options():
    """Option B prose must enumerate at least 2 of:
    - fresh-context audit (new session clears author-context)
    - architect-reviewer subagent
    - second operator
    """
    body = _step_1a_region(_text())
    options_found = 0
    if "fresh" in body.lower() and ("session" in body.lower() or "context" in body.lower()):
        options_found += 1
    if "architect-reviewer" in body.lower() or "subagent" in body.lower():
        options_found += 1
    if "second operator" in body.lower() or "another operator" in body.lower() or "separate operator" in body.lower():
        options_found += 1
    assert options_found >= 2, (
        f"Option B prose must enumerate at least 2 dispatch options "
        f"(fresh-context, architect-reviewer subagent, second operator); "
        f"found {options_found}"
    )
