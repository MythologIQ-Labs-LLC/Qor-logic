"""Phase 67 (#45): qor-audit short-circuits on unchanged plan re-invocation.

When the operator invokes `/qor-audit` after a VETO without amending the
plan, the audit detects byte-equality between current plan content and
the prior audit's recorded `target_content_hash`, and recommends
amendment instead of consuming a new audit cycle.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from qor.scripts import validate_gate_artifact as vga
from qor.scripts.qor_audit_runtime import (
    ShortCircuitResult,
    check_unchanged_plan_short_circuit,
)


@pytest.fixture
def isolate_gates_dir(tmp_path, monkeypatch):
    """Re-point gate_chain's GATES_DIR at tmp_path so test fixtures live in isolation."""
    monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")
    yield


def _write_plan(tmp: Path, content: str) -> Path:
    """Create a plan file under tmp; returns its path."""
    plan = tmp / "docs" / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text(content, encoding="utf-8")
    return plan


def _write_prior_audit(
    tmp: Path,
    session_id: str,
    verdict: str,
    target_content_hash: str | None,
) -> Path:
    """Create a synthetic audit.json under .qor/gates/<session>/."""
    gate_dir = tmp / ".qor" / "gates" / session_id
    gate_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": "audit",
        "ts": "2026-05-14T17:00:00Z",
        "session_id": session_id,
        "target": "docs/plan.md",
        "verdict": verdict,
        "report_path": ".agent/staging/AUDIT_REPORT.md",
        "risk_grade": "L1",
    }
    if target_content_hash is not None:
        payload["target_content_hash"] = target_content_hash
    (gate_dir / "audit.json").write_text(json.dumps(payload), encoding="utf-8")
    return gate_dir / "audit.json"


def test_short_circuit_when_plan_content_hash_matches_prior_audit(tmp_path, monkeypatch, isolate_gates_dir):
    monkeypatch.chdir(tmp_path)
    sid = "2026-05-14T1234-fixture"
    plan_text = "# Plan: unchanged content"
    plan = _write_plan(tmp_path, plan_text)
    plan_hash = hashlib.sha256(plan_text.encode("utf-8")).hexdigest()
    _write_prior_audit(tmp_path, sid, verdict="VETO", target_content_hash=plan_hash)
    result = check_unchanged_plan_short_circuit(plan, sid)
    assert isinstance(result, ShortCircuitResult)
    assert result.should_skip is True
    assert result.prior_verdict == "VETO"
    assert result.plan_content_hash == plan_hash


def test_no_short_circuit_when_plan_content_diverges(tmp_path, monkeypatch, isolate_gates_dir):
    monkeypatch.chdir(tmp_path)
    sid = "2026-05-14T1234-divergent"
    plan = _write_plan(tmp_path, "# Plan: amended content")
    old_hash = hashlib.sha256(b"# Plan: prior content").hexdigest()
    _write_prior_audit(tmp_path, sid, verdict="VETO", target_content_hash=old_hash)
    result = check_unchanged_plan_short_circuit(plan, sid)
    assert result.should_skip is False


def test_no_short_circuit_when_no_prior_audit_exists(tmp_path, monkeypatch, isolate_gates_dir):
    monkeypatch.chdir(tmp_path)
    sid = "2026-05-14T1234-noprior"
    plan = _write_plan(tmp_path, "# Plan: first audit")
    # No prior audit.json written.
    result = check_unchanged_plan_short_circuit(plan, sid)
    assert result.should_skip is False


def test_no_short_circuit_when_prior_audit_lacks_target_content_hash(tmp_path, monkeypatch, isolate_gates_dir):
    """Pre-Phase-67 audit artifacts lack the new field; behavior must be backward compatible."""
    monkeypatch.chdir(tmp_path)
    sid = "2026-05-14T1234-pre67"
    plan = _write_plan(tmp_path, "# Plan: legacy session")
    _write_prior_audit(tmp_path, sid, verdict="PASS", target_content_hash=None)
    result = check_unchanged_plan_short_circuit(plan, sid)
    assert result.should_skip is False


def test_skill_prose_documents_short_circuit_behavior():
    """qor-audit SKILL.md Step 0 region must document the short-circuit path."""
    skill = Path("qor/skills/governance/qor-audit/SKILL.md").read_text(encoding="utf-8")
    # Find the Step 0 block (between Step 0 heading and next Step heading).
    start = skill.find("### Step 0:")
    assert start >= 0
    end = skill.find("### Step 0.5", start + 10)
    if end < 0:
        end = skill.find("### Step 0.6", start + 10)
    block = skill[start:end] if end > 0 else skill[start:]
    # The block (or its successor sub-step) must reference short-circuit or unchanged plan.
    # Allow the wiring to land at Step 0, 0.5, or a new Step 0.7.
    full_step0_region = skill[start:skill.find("### Step 1:", start)]
    assert "unchanged plan" in full_step0_region.lower() or "short-circuit" in full_step0_region.lower(), (
        "qor-audit Step 0 region must document the unchanged-plan short-circuit "
        "(Phase 67; GH #45)"
    )
    assert "check_unchanged_plan_short_circuit" in full_step0_region or "target_content_hash" in full_step0_region, (
        "Step 0 region must name the helper or the gate-artifact field used"
    )
