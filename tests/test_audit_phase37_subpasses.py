"""Wiring + procedure-content tests for the Phase 37 Infrastructure Alignment
sub-passes (Phase 83, GH #83 + GH #87).

The consumer-trace sub-check (GH #83) is an LLM-executed prose procedure with
no code unit; the strongest available coverage asserts the audit skill is
wired to invoke it and the procedure file documents the procedure completely.
Repo precedent for marker/wiring tests on prose:
test_audit_drift_auto_invoked.py::test_audit_template_has_drift_marker.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "qor/skills/governance/qor-audit/SKILL.md"
SUBPASSES = REPO_ROOT / "qor/skills/governance/qor-audit/references/phase37-subpasses.md"
DOCTRINE = REPO_ROOT / "qor/references/doctrine-shadow-genome-countermeasures.md"


def test_skill_step3_points_to_consumer_trace_subpass():
    text = SKILL.read_text(encoding="utf-8")
    assert "phase37-subpasses.md" in text, "Step 3 must reference the sub-passes file"
    assert "consumer-trace" in text, "Step 3 must name the consumer-trace sub-check"


def test_consumer_trace_procedure_documented():
    text = SUBPASSES.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "consumer-trace" in lowered
    assert "entry point" in lowered or "entry-point" in lowered
    assert "infrastructure-mismatch" in text, (
        "the procedure must map an unreachable citation to the finding category"
    )


def test_skill_step0_6_runs_delivery_branch_lint():
    text = SKILL.read_text(encoding="utf-8")
    assert "qor.scripts.delivery_branch_lint" in text, (
        "Step 0.6 must invoke the delivery_branch_lint pre-audit lint"
    )


def test_delivery_branch_procedure_documented():
    text = SUBPASSES.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "delivery-branch" in lowered or "delivery branch" in lowered
    assert "pr_target" in text
    assert "open" in lowered and "operator" in lowered, (
        "the procedure must name the operator open/closed confirmation"
    )


def test_sg_delivery_branch_drift_entry_present():
    text = DOCTRINE.read_text(encoding="utf-8")
    assert "SG-DeliveryBranchDrift-A" in text
    idx = text.index("SG-DeliveryBranchDrift-A")
    entry = text[idx:idx + 3000]
    assert "**Pattern**" in entry
    assert "**Countermeasure**" in entry
    assert "**Cross-reference**" in entry
