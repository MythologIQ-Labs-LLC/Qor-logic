"""Phase 69 (#43): skill prose wires check_session_total alongside check.

Validates that /qor-plan Step 2c and /qor-audit Step 0.5 invoke the new
session-total mode in parallel with the existing consecutive-streak
check, and that the doctrine section documents both modes.
"""
from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_qor_plan_step_2c_invokes_check_session_total():
    body = _read("qor/skills/sdlc/qor-plan/SKILL.md")
    start = body.find("### Step 2c")
    assert start >= 0, "Step 2c heading missing"
    end = body.find("### Step", start + 10)
    block = body[start:end] if end > 0 else body[start:]
    assert "check_session_total" in block, (
        "qor-plan Step 2c must invoke cycle_count_escalator.check_session_total "
        "alongside the existing cce.check (Phase 69; GH #43)"
    )
    assert "session-total" in block, (
        "Step 2c prose must name the session-total mode by its escalation_reason"
    )


def test_qor_audit_step_0_5_invokes_check_session_total():
    body = _read("qor/skills/governance/qor-audit/SKILL.md")
    start = body.find("### Step 0.5")
    assert start >= 0, "Step 0.5 heading missing"
    end = body.find("### Step 0.6", start + 10)
    block = body[start:end] if end > 0 else body[start:]
    assert "check_session_total" in block, (
        "qor-audit Step 0.5 must invoke cycle_count_escalator.check_session_total "
        "alongside the existing cce.check (Phase 69; GH #43)"
    )


def test_doctrine_documents_session_total_mode():
    body = _read("qor/references/doctrine-governance-enforcement.md")
    # Find §10.4 region; must mention session-total mode alongside consecutive
    start = body.find("10.4")
    assert start >= 0, "doctrine §10.4 missing"
    region = body[start:start + 3000]
    assert "session-total" in region, (
        "doctrine §10.4 must document the session-total mode (Phase 69; GH #43)"
    )
    assert "consecutive" in region.lower(), (
        "doctrine §10.4 must still document the original consecutive-streak mode"
    )
