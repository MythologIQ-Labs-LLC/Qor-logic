"""Phase 68 (#44): qor-audit Step 3.5 Self-Application Sub-Pass.

When the plan declares `originating_remediation`, the auditor manually
performs the discipline the plan introduces against the plan itself.
Closes the SG-007 self-audit verification scope bias for the case where
the very plan introducing a discipline exhibits the pattern the
discipline targets (e.g., a plan authoring a plan-text-drift lint that
itself drifts in plan text).
"""
from __future__ import annotations

from pathlib import Path

SKILL_PATH = Path("qor/skills/governance/qor-audit/SKILL.md")


def _text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _step_3_region(text: str) -> str:
    """Return the body of Step 3 (Adversarial Audit) up to Step 4."""
    start = text.find("### Step 3:")
    assert start >= 0, "Step 3 heading missing"
    end = text.find("### Step 4:", start + 10)
    return text[start:end] if end > 0 else text[start:]


def test_skill_prose_declares_self_application_subpass():
    body = _step_3_region(_text())
    assert "Self-Application" in body or "self-application" in body, (
        "Step 3 must declare a Self-Application sub-pass (Phase 68; GH #44)"
    )
    assert "originating_remediation" in body, (
        "Sub-pass prose must reference the originating_remediation plan field"
    )


def test_skill_prose_cites_originating_pattern():
    body = _step_3_region(_text())
    cites_sg007 = "SG-007" in body or "SG-AuthorAuditMomentum" in body
    cites_pattern_name = (
        "verification scope bias" in body.lower()
        or "author-audit momentum" in body.lower()
        or "self-audit" in body.lower()
    )
    assert cites_sg007 or cites_pattern_name, (
        "Self-Application sub-pass must cite SG-007 or name the pattern "
        "(self-audit verification scope bias / author-audit momentum)"
    )


def test_skill_prose_names_veto_category():
    body = _step_3_region(_text())
    assert "specification-drift" in body, (
        "Self-Application sub-pass must name `specification-drift` as the "
        "VETO findings_categories value when self-application detects the pattern"
    )
