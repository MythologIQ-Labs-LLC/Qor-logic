"""Phase 67 (#42): plan_text_consistency_lint wired into qor-audit + qor-plan.

Locks the wiring contract so the COREFORGE-class drift pattern (same
operation specified differently at multiple plan sites) is caught at
pre-audit lint time, before the binding Infrastructure Alignment Pass
consumes an audit cycle.
"""
from __future__ import annotations

from pathlib import Path

QOR_AUDIT_SKILL = Path("qor/skills/governance/qor-audit/SKILL.md")
QOR_PLAN_SKILL = Path("qor/skills/sdlc/qor-plan/SKILL.md")
DOCTRINE_PATH = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_qor_audit_step_0_6_invokes_plan_text_consistency_lint():
    """Step 0.6 must invoke plan_text_consistency_lint alongside plan_test_lint + plan_grep_lint."""
    body = _read(QOR_AUDIT_SKILL)
    # Locate Step 0.6 block; it starts at "### Step 0.6:" and ends at the next "### Step"
    start = body.find("### Step 0.6:")
    assert start >= 0, "Step 0.6 heading missing"
    end = body.find("### Step", start + 10)
    block = body[start:end] if end > 0 else body[start:]
    assert "plan_text_consistency_lint" in block, (
        "Step 0.6 must invoke plan_text_consistency_lint (Phase 67 wiring; GH #42)"
    )
    # And the existing two lints must still be present (no regression).
    assert "plan_test_lint" in block
    assert "plan_grep_lint" in block


def test_qor_plan_step_5_names_consistency_lint_discipline():
    """qor-plan Step 5 review checklist must name the discipline + tooling reference."""
    body = _read(QOR_PLAN_SKILL)
    start = body.find("### Step 5:")
    assert start >= 0, "Step 5 heading missing"
    end = body.find("### Step", start + 10)
    block = body[start:end] if end > 0 else body[start:]
    # Discipline statement: prose mentions "same" + "identically" pattern, or names the lint by module.
    assert "plan_text_consistency_lint" in block, (
        "Step 5 must reference plan_text_consistency_lint by name as a "
        "discipline-verification step (Phase 67; GH #42)"
    )


def test_doctrine_sg_plan_text_drift_a_documented():
    """SG-PlanTextDrift-A catalogues prose-boundary precision drift pattern."""
    body = _read(DOCTRINE_PATH)
    assert "SG-PlanTextDrift-A" in body, (
        "Doctrine must catalogue SG-PlanTextDrift-A (Phase 67; GH #42)"
    )
    # Cite the countermeasure surfaces in the SG entry body.
    sg_start = body.find("SG-PlanTextDrift-A")
    sg_section = body[sg_start:sg_start + 2000]  # bounded read
    assert "plan_text_consistency_lint" in sg_section
