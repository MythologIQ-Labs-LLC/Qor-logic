"""Phase 29 Phase 1: /qor-audit Step Z writes a schema-valid audit.json.

The audit skill previously lacked Step Z; downstream phases (/qor-implement)
had to fall back to gate overrides or hand-written artifacts. These tests
lock in the contract that audit.json is now produced via
gate_chain.write_gate_artifact with fields matching qor/gates/schema/audit.schema.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import pytest


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "gates" / "schema" / "audit.schema.json"
)


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _base_payload(**overrides):
    payload = {
        "phase": "audit",
        "ts": "2026-04-18T12:00:00Z",
        "session_id": "sess-12345",
        "target": "docs/plan-qor-phaseXX.md",
        "verdict": "PASS",
    }
    payload.update(overrides)
    return payload


def _write_via_gate_chain(tmp_path, monkeypatch, payload):
    from qor.scripts import validate_gate_artifact as vga
    from qor.scripts import gate_chain
    monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")
    gate_chain.write_gate_artifact("audit", payload, session_id="sess-12345")
    return json.loads(
        (tmp_path / ".qor" / "gates" / "sess-12345" / "audit.json").read_text(encoding="utf-8")
    )


def test_audit_step_z_writes_pass_verdict(tmp_path, monkeypatch):
    payload = _base_payload(
        target="docs/plan-qor-phase29-audit-stepZ-and-contributing.md",
        verdict="PASS",
        risk_grade="L2",
        report_path=".agent/staging/AUDIT_REPORT.md",
    )
    written = _write_via_gate_chain(tmp_path, monkeypatch, payload)
    assert written["verdict"] == "PASS"
    assert written["risk_grade"] == "L2"
    assert written["target"].endswith("plan-qor-phase29-audit-stepZ-and-contributing.md")
    # Round-trip schema check.
    jsonschema.validate(written, _schema())


def test_audit_step_z_writes_veto_verdict_with_risk_grade(tmp_path, monkeypatch):
    payload = _base_payload(
        target="docs/plan-qor-phaseXX.md",
        verdict="VETO",
        risk_grade="L2",
        report_path=".agent/staging/AUDIT_REPORT.md",
    )
    written = _write_via_gate_chain(tmp_path, monkeypatch, payload)
    assert written["verdict"] == "VETO"
    assert written["risk_grade"] == "L2"
    jsonschema.validate(written, _schema())


def test_audit_step_z_rejects_missing_required_fields():
    """Schema requires phase, ts, session_id, target, verdict."""
    missing_target = _base_payload()
    del missing_target["target"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(missing_target, _schema())


def test_audit_step_z_rejects_bogus_verdict():
    """Verdict must be PASS or VETO (enum)."""
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_payload(verdict="MAYBE"), _schema())


def test_downstream_phases_can_read_audit_json(tmp_path, monkeypatch):
    """After /qor-audit Step Z writes audit.json, /qor-implement's Step 0
    check_prior_artifact('implement') must return found=True, valid=True.
    This is the missing-link gap that Phase 29 closes."""
    from qor.scripts import validate_gate_artifact as vga
    from qor.scripts import gate_chain
    # Both modules carry their own GATES_DIR constant; patch both.
    monkeypatch.setattr(vga, "GATES_DIR", tmp_path / ".qor" / "gates")
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path / ".qor" / "gates")

    payload = _base_payload(verdict="PASS", risk_grade="L2")
    gate_chain.write_gate_artifact("audit", payload, session_id="sess-12345")

    result = gate_chain.check_prior_artifact("implement", session_id="sess-12345")
    assert result.found is True
    assert result.valid is True
    assert result.errors == []
