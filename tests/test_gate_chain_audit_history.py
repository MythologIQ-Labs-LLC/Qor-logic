"""Tests for gate_chain integration with audit_history (Phase 37 Phase 1)."""
from __future__ import annotations

import unittest.mock as mock

import pytest

from qor.scripts import gate_chain, audit_history


AUDIT_PAYLOAD = {
    "phase": "audit",
    "ts": "2026-04-20T12:00:00Z",
    "session_id": "s-gc-hist",
    "target": "docs/plan.md",
    "verdict": "PASS",
}


def test_audit_write_updates_singleton_and_history(tmp_path):
    with mock.patch("qor.scripts.validate_gate_artifact.GATES_DIR", tmp_path), \
         mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        gate_chain.write_gate_artifact(phase="audit", payload=AUDIT_PAYLOAD, session_id="s-gc-hist")
    singleton = tmp_path / "s-gc-hist" / "audit.json"
    history = tmp_path / "s-gc-hist" / "audit_history.jsonl"
    assert singleton.exists()
    assert history.exists()
    history_records = audit_history.read("s-gc-hist")
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        history_records = audit_history.read("s-gc-hist")
    assert len(history_records) == 1
    assert history_records[0]["verdict"] == "PASS"


def test_non_audit_write_does_not_create_history(tmp_path):
    plan_payload = {
        "phase": "plan",
        "ts": "2026-04-20T12:00:00Z",
        "session_id": "s-gc-plan",
        "plan_path": "docs/plan.md",
        "phases": ["Phase 1: thing"],
        "ci_commands": ["pytest"],
    }
    with mock.patch("qor.scripts.validate_gate_artifact.GATES_DIR", tmp_path), \
         mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        gate_chain.write_gate_artifact(phase="plan", payload=plan_payload, session_id="s-gc-plan")
    history = tmp_path / "s-gc-plan" / "audit_history.jsonl"
    assert not history.exists()


def test_invalid_audit_payload_writes_neither_singleton_nor_history(tmp_path):
    bad_payload = {
        "phase": "audit",
        "ts": "2026-04-20T12:00:00Z",
        "session_id": "s-bad-gc",
        # missing required: target, verdict
    }
    with mock.patch("qor.scripts.validate_gate_artifact.GATES_DIR", tmp_path), \
         mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        with pytest.raises(Exception):
            gate_chain.write_gate_artifact(phase="audit", payload=bad_payload, session_id="s-bad-gc")
    assert not (tmp_path / "s-bad-gc" / "audit.json").exists()
    assert not (tmp_path / "s-bad-gc" / "audit_history.jsonl").exists()
