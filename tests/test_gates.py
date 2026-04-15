"""Tests for Phase 3 gate chain runtime."""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import session
import validate_gate_artifact as vga
import gate_chain
import shadow_process


# ----- Session ID format & collision resistance -----

def test_session_id_format():
    sid = session.generate_id()
    assert session.SESSION_ID_PATTERN.match(sid), f"bad format: {sid}"


def test_session_id_collision_resistant():
    # 24 bits entropy. Birthday-paradox expected collisions for N=500 draws
    # in the same minute: ~500^2 / (2 * 2^24) = ~0.0075 (1 in ~135 runs).
    # We assert <= 1 collision out of 500 draws to keep the test reliable
    # while still detecting catastrophic regression in entropy quality.
    fixed = datetime(2026, 4, 15, 17, 46, tzinfo=timezone.utc)
    ids = [session.generate_id(fixed) for _ in range(500)]
    collisions = len(ids) - len(set(ids))
    assert collisions <= 1, f"Expected <= 1 collision in 500 draws, got {collisions}"


# ----- Marker file lifecycle -----

def test_marker_roundtrip(tmp_path, monkeypatch):
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid1 = session.get_or_create(marker)
    sid2 = session.get_or_create(marker)
    assert sid1 == sid2  # fresh marker returns same id


def test_marker_regenerates_after_24h(tmp_path, monkeypatch):
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid1 = session.get_or_create(marker)
    # Simulate old mtime (25h ago)
    old_ts = time.time() - (25 * 3600)
    import os
    os.utime(marker, (old_ts, old_ts))
    sid2 = session.get_or_create(marker)
    assert sid1 != sid2


def test_current_returns_none_when_absent(tmp_path, monkeypatch):
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    assert session.current(marker) is None


def test_end_session_removes_marker(tmp_path, monkeypatch):
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    session.get_or_create(marker)
    assert marker.exists()
    session.end_session(marker)
    assert not marker.exists()


# ----- Schema validation (parameterized per phase) -----

VALID_ARTIFACTS = {
    "research": {
        "phase": "research", "ts": "2026-04-15T18:00:00Z",
        "session_id": "s-abc", "questions": ["q1"], "findings": [{"x": 1}],
    },
    "plan": {
        "phase": "plan", "ts": "2026-04-15T18:00:00Z",
        "session_id": "s-abc", "plan_path": "docs/plan.md", "phases": ["p1"],
    },
    "audit": {
        "phase": "audit", "ts": "2026-04-15T18:00:00Z",
        "session_id": "s-abc", "target": "docs/plan.md", "verdict": "PASS",
    },
    "implement": {
        "phase": "implement", "ts": "2026-04-15T18:00:00Z",
        "session_id": "s-abc", "files_touched": ["a.py"],
    },
    "substantiate": {
        "phase": "substantiate", "ts": "2026-04-15T18:00:00Z",
        "session_id": "s-abc", "verdict": "PASS",
        "merkle_seal": "a" * 64,
    },
    "validate": {
        "phase": "validate", "ts": "2026-04-15T18:00:00Z",
        "session_id": "s-abc", "overall": "PASS",
        "criteria_results": [{"criterion": "c1", "status": "pass"}],
    },
    "remediate": {
        "phase": "remediate", "ts": "2026-04-15T18:00:00Z",
        "session_id": "s-abc", "events_addressed": [],
        "proposed_changes": [],
    },
}


@pytest.mark.parametrize("phase,payload", list(VALID_ARTIFACTS.items()))
def test_schema_accepts_valid_artifact(tmp_path, phase, payload):
    artifact = tmp_path / f"{phase}.json"
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    errors = vga.validate_one(phase, artifact)
    assert errors == [], f"{phase} should validate: {errors}"


def test_schema_rejects_missing_required_field(tmp_path):
    artifact = tmp_path / "plan.json"
    artifact.write_text(json.dumps({"phase": "plan"}), encoding="utf-8")
    errors = vga.validate_one("plan", artifact)
    assert any("ts" in e or "required" in e for e in errors)


def test_schema_rejects_wrong_phase_const(tmp_path):
    artifact = tmp_path / "audit.json"
    bad = dict(VALID_ARTIFACTS["audit"])
    bad["phase"] = "plan"
    artifact.write_text(json.dumps(bad), encoding="utf-8")
    errors = vga.validate_one("audit", artifact)
    assert errors


def test_schema_rejects_bad_verdict_enum(tmp_path):
    artifact = tmp_path / "audit.json"
    bad = dict(VALID_ARTIFACTS["audit"])
    bad["verdict"] = "MAYBE"
    artifact.write_text(json.dumps(bad), encoding="utf-8")
    errors = vga.validate_one("audit", artifact)
    assert errors


# ----- Gate chain check_prior_artifact -----

def test_check_prior_research_is_chain_start(tmp_path, monkeypatch):
    # research has no prior -> found/valid both true
    result = gate_chain.check_prior_artifact("research")
    assert result.found is True
    assert result.valid is True


def test_check_prior_missing_returns_not_found(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)
    result = gate_chain.check_prior_artifact("plan", session_id=sid)
    assert result.found is False
    assert "missing" in result.errors[0]


def test_check_prior_valid_returns_valid(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    # Write a valid research artifact
    research_dir = gates / sid
    research_dir.mkdir(parents=True)
    (research_dir / "research.json").write_text(
        json.dumps(VALID_ARTIFACTS["research"]), encoding="utf-8"
    )

    result = gate_chain.check_prior_artifact("plan", session_id=sid)
    assert result.found is True
    assert result.valid is True


def test_check_prior_malformed_returns_invalid(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    research_dir = gates / sid
    research_dir.mkdir(parents=True)
    (research_dir / "research.json").write_text(
        json.dumps({"phase": "research"}), encoding="utf-8"  # missing required fields
    )

    result = gate_chain.check_prior_artifact("plan", session_id=sid)
    assert result.found is True
    assert result.valid is False
    assert len(result.errors) > 0


# ----- emit_gate_override integration with shadow_process -----

def test_emit_gate_override_writes_shadow_event(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)

    eid = gate_chain.emit_gate_override(
        current_phase="plan",
        prior_phase_name="research",
        reason="scope too small for research phase",
        session_id="2026-04-15T18:00-abcdef",
    )
    assert len(eid) == 64

    events = shadow_process.read_events(log)
    assert len(events) == 1
    e = events[0]
    assert e["event_type"] == "gate_override"
    assert e["severity"] == 1
    assert e["details"]["current_phase"] == "plan"
    assert e["details"]["prior_phase"] == "research"


# ----- validate --all mode -----

def test_validate_all_empty_session_returns_zero(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    session.get_or_create(marker)
    checked, errors, _ = vga.validate_all_current_session()
    assert checked == 0
    assert errors == 0


def test_validate_all_no_session(tmp_path, monkeypatch):
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    checked, errors, report = vga.validate_all_current_session()
    assert checked == 0
    assert errors == 0
    assert "No active session" in report[0]


# ----- write_artifact helper -----

def test_write_artifact_round_trips(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    out = vga.write_artifact("plan", {
        "ts": "2026-04-15T18:00:00Z",
        "plan_path": "docs/plan.md",
        "phases": ["p1", "p2"],
    }, session_id=sid)
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["phase"] == "plan"
    assert data["session_id"] == sid


def test_write_artifact_rejects_invalid(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    with pytest.raises(ValueError, match="Cannot write invalid"):
        vga.write_artifact("plan", {"ts": "bad"}, session_id=sid)


# ----- V-7 + V-D (Phase 12 v2 audit) gate_chain.write_gate_artifact coverage -----

def test_write_gate_artifact_creates_file_at_correct_path(tmp_path, monkeypatch):
    """Helper writes to .qor/gates/<sid>/<phase>.json."""
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    payload = {
        "ts": "2026-04-15T18:00:00Z",
        "plan_path": "docs/plan.md",
        "phases": ["p1"],
    }
    out = gate_chain.write_gate_artifact("plan", payload, session_id=sid)
    assert out == gates / sid / "plan.json"
    assert out.exists()


def test_write_gate_artifact_validates_payload_against_schema(tmp_path, monkeypatch):
    """Invalid payload (missing required field) raises ValueError."""
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    bad_payload = {"ts": "2026-04-15T18:00:00Z"}  # missing required plan_path, phases
    with pytest.raises(ValueError):
        gate_chain.write_gate_artifact("plan", bad_payload, session_id=sid)


def test_write_gate_artifact_uses_session_get_or_create_when_sid_none(tmp_path, monkeypatch):
    """When session_id=None, helper invokes session.get_or_create."""
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    # No session yet; helper must create one
    assert not marker.exists()

    payload = {
        "ts": "2026-04-15T18:00:00Z",
        "plan_path": "docs/plan.md",
        "phases": ["p1"],
    }
    out = gate_chain.write_gate_artifact("plan", payload)
    assert marker.exists()  # session.get_or_create was invoked
    assert out.exists()


def test_write_gate_artifact_respects_explicit_session_id(tmp_path, monkeypatch):
    """When session_id is provided, helper uses that exact id (no implicit create)."""
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)

    explicit_sid = "2026-04-15T1800-explicit"
    payload = {
        "ts": "2026-04-15T18:00:00Z",
        "plan_path": "docs/plan.md",
        "phases": ["p1"],
    }
    out = gate_chain.write_gate_artifact("plan", payload, session_id=explicit_sid)
    assert out == gates / explicit_sid / "plan.json"
    # Marker may or may not exist; but the artifact MUST be at the explicit-sid path
    import json as _json
    data = _json.loads(out.read_text())
    assert data["session_id"] == explicit_sid


def test_write_gate_artifact_returns_path(tmp_path, monkeypatch):
    """Return value is the written Path (not None, not str)."""
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setattr(vga, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    payload = {
        "ts": "2026-04-15T18:00:00Z",
        "plan_path": "docs/plan.md",
        "phases": ["p1"],
    }
    result = gate_chain.write_gate_artifact("plan", payload, session_id=sid)
    from pathlib import Path
    assert isinstance(result, Path)
