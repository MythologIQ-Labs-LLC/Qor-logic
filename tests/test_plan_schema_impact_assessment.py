"""Phase 54: plan schema accepts impact_assessment + high_risk_target."""
from __future__ import annotations

from copy import deepcopy

import pytest

from qor.scripts import validate_gate_artifact as vga


def _base_plan() -> dict:
    return {
        "phase": "plan",
        "ts": "2026-04-30T18:00:00Z",
        "session_id": "test-impact",
        "plan_path": "docs/plan-foo.md",
        "phases": ["Phase 1"],
        "ci_commands": ["pytest"],
    }


def _impact_block() -> dict:
    return {
        "purpose": "Support development of a downstream high-risk AI system.",
        "affected_stakeholders": ["operators", "deployers", "end users"],
        "identified_risks": ["risk-1", "risk-2"],
        "mitigations": ["mitigation-1", "mitigation-2"],
        "residual_risks": ["residual-1"],
    }


def test_schema_accepts_plan_with_impact_assessment():
    plan = _base_plan()
    plan["high_risk_target"] = True
    plan["impact_assessment"] = _impact_block()
    errs = vga._validate_data("plan", plan)
    assert errs == [], f"valid plan with impact assessment must validate: {errs}"


def test_schema_accepts_plan_without_impact_assessment():
    plan = _base_plan()
    errs = vga._validate_data("plan", plan)
    assert errs == [], f"plan without impact_assessment must validate: {errs}"


def test_schema_accepts_high_risk_target_false_without_impact_assessment():
    plan = _base_plan()
    plan["high_risk_target"] = False
    errs = vga._validate_data("plan", plan)
    assert errs == [], f"plan with high_risk_target false must validate: {errs}"


def test_schema_rejects_high_risk_target_without_impact_assessment():
    plan = _base_plan()
    plan["high_risk_target"] = True
    errs = vga._validate_data("plan", plan)
    assert errs, "high_risk_target=true must require impact_assessment block"


@pytest.mark.parametrize("missing", [
    "purpose", "affected_stakeholders", "identified_risks",
    "mitigations", "residual_risks",
])
def test_impact_assessment_required_subfields(missing: str):
    plan = _base_plan()
    plan["high_risk_target"] = True
    block = _impact_block()
    block.pop(missing)
    plan["impact_assessment"] = block
    errs = vga._validate_data("plan", plan)
    assert errs, f"impact_assessment must require {missing!r} subfield"
