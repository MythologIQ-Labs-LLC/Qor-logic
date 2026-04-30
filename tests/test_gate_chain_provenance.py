"""Phase 52: gate_chain.write_gate_artifact provenance binding (G-root).

Tests the QOR_SKILL_ACTIVE env-var enforcement on write_gate_artifact.
Each test invokes the helper directly and asserts on returned value or
raised exception per Phase 46 doctrine (functionality test, not
presence-only).
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, "qor/scripts")
import gate_chain  # noqa: E402  (sys.path adjustment required for direct import)


# Minimal valid plan payload (matches qor/gates/schema/plan.schema.json).
def _valid_plan_payload(sid: str) -> dict:
    return {
        "phase": "plan",
        "session_id": sid,
        "ts": "2026-04-30T00:00:00Z",
        "plan_path": "docs/plan-qor-phase52-test.md",
        "phases": ["Phase 1: test"],
        "ci_commands": ["pytest"],
    }


def test_provenance_error_class_exists_and_inherits_exception():
    """ProvenanceError must be importable and subclass Exception."""
    assert hasattr(gate_chain, "ProvenanceError")
    assert issubclass(gate_chain.ProvenanceError, Exception)


def test_write_gate_artifact_refuses_without_qor_skill_active(tmp_path, monkeypatch):
    """With env clean, write_gate_artifact raises ProvenanceError."""
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    monkeypatch.delenv("QOR_GATE_PROVENANCE_OPTIONAL", raising=False)
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path)
    sid = "2026-04-30T0000-test01"
    with pytest.raises(gate_chain.ProvenanceError) as exc_info:
        gate_chain.write_gate_artifact(
            phase="plan",
            payload=_valid_plan_payload(sid),
            session_id=sid,
        )
    assert "QOR_SKILL_ACTIVE" in str(exc_info.value)


def test_write_gate_artifact_refuses_when_qor_skill_active_mismatches(tmp_path, monkeypatch):
    """QOR_SKILL_ACTIVE=audit but write called with phase=plan -> raises."""
    monkeypatch.setenv("QOR_SKILL_ACTIVE", "audit")
    monkeypatch.delenv("QOR_GATE_PROVENANCE_OPTIONAL", raising=False)
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path)
    sid = "2026-04-30T0000-test02"
    with pytest.raises(gate_chain.ProvenanceError) as exc_info:
        gate_chain.write_gate_artifact(
            phase="plan",
            payload=_valid_plan_payload(sid),
            session_id=sid,
        )
    msg = str(exc_info.value)
    assert "audit" in msg and "plan" in msg


def test_write_gate_artifact_succeeds_when_qor_skill_active_matches(tmp_path, monkeypatch):
    """QOR_SKILL_ACTIVE=plan with phase=plan -> write succeeds."""
    monkeypatch.setenv("QOR_SKILL_ACTIVE", "plan")
    monkeypatch.delenv("QOR_GATE_PROVENANCE_OPTIONAL", raising=False)
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path)
    sid = "2026-04-30T0000-test03"
    path = gate_chain.write_gate_artifact(
        phase="plan",
        payload=_valid_plan_payload(sid),
        session_id=sid,
    )
    assert path.is_file()
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["phase"] == "plan"
    assert written["session_id"] == sid


def test_qor_gate_provenance_optional_bypasses_check(tmp_path, monkeypatch):
    """QOR_GATE_PROVENANCE_OPTIONAL=1 with no QOR_SKILL_ACTIVE -> succeeds."""
    monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path)
    sid = "2026-04-30T0000-test04"
    path = gate_chain.write_gate_artifact(
        phase="plan",
        payload=_valid_plan_payload(sid),
        session_id=sid,
    )
    assert path.is_file()


def test_provenance_check_does_not_consume_payload_dict(tmp_path, monkeypatch):
    """Caller's payload dict must be unmodified after raise."""
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    monkeypatch.delenv("QOR_GATE_PROVENANCE_OPTIONAL", raising=False)
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path)
    sid = "2026-04-30T0000-test05"
    payload = _valid_plan_payload(sid)
    snapshot = dict(payload)
    with pytest.raises(gate_chain.ProvenanceError):
        gate_chain.write_gate_artifact(phase="plan", payload=payload, session_id=sid)
    assert payload == snapshot, "payload dict mutated by failed call"
