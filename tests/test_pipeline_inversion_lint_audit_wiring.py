"""Phase 70 (#47): pipeline_inversion_lint wired into qor-audit Step 0.6.

The Phase 49 `pipeline_inversion_lint.py` heuristic detects filter-stage
ordering inversions in Python source. Phase 70 wires it as a fourth
pre-audit lint alongside plan_test_lint, plan_grep_lint, and
plan_text_consistency_lint. WARN-only at audit time; Judge confirms
inversions at Step 3.
"""
from __future__ import annotations

from pathlib import Path

QOR_AUDIT_SKILL = Path("qor/skills/governance/qor-audit/SKILL.md")
DOCTRINE_PATH = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _step_0_6_block(text: str) -> str:
    start = text.find("### Step 0.6:")
    assert start >= 0, "Step 0.6 heading missing"
    end = text.find("### Step 1:", start + 10)
    if end < 0:
        end = text.find("### Step", start + 12)
    return text[start:end] if end > 0 else text[start:]


def test_qor_audit_step_0_6_invokes_pipeline_inversion_lint():
    body = QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    block = _step_0_6_block(body)
    assert "pipeline_inversion_lint" in block, (
        "Step 0.6 must invoke pipeline_inversion_lint (Phase 70; GH #47)"
    )
    # Pre-existing three lints must still be present (no regression).
    assert "plan_test_lint" in block
    assert "plan_grep_lint" in block
    assert "plan_text_consistency_lint" in block


def test_doctrine_sg_filter_stage_inversion_documented():
    body = DOCTRINE_PATH.read_text(encoding="utf-8")
    assert "SG-FilterStageInversion-A" in body, (
        "Doctrine must catalogue SG-FilterStageInversion-A (Phase 70; GH #47)"
    )
    sg_start = body.find("SG-FilterStageInversion-A")
    sg_section = body[sg_start:sg_start + 2500]
    assert "pipeline_inversion_lint" in sg_section
    # Cite the originating pattern (COREFORGE Skill-Forge dispatcher).
    assert (
        "dispatcher" in sg_section.lower()
        or "skill-forge" in sg_section.lower()
        or "filter" in sg_section.lower()
    ), "SG entry must reference originating filter-pipeline pattern"


def test_step_0_6_lints_use_consistent_warn_pattern():
    """All four lint invocations in Step 0.6 should match the `|| true`
    WARN-only pattern (no accidental fail-closed wiring on a lint that's
    meant to be advisory)."""
    body = QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    block = _step_0_6_block(body)
    lines = [
        ln for ln in block.splitlines()
        if "python -m qor.scripts" in ln
        and ("plan_test_lint" in ln or "plan_grep_lint" in ln
             or "plan_text_consistency_lint" in ln or "pipeline_inversion_lint" in ln)
    ]
    assert len(lines) >= 4, (
        f"expected 4 lint invocations in Step 0.6 block; got {len(lines)}: {lines}"
    )
    for ln in lines:
        assert "|| true" in ln, (
            f"lint invocation should be WARN-only (`|| true` trailer): {ln!r}"
        )
