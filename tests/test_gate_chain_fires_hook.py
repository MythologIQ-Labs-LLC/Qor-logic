"""Phase 57: gate_chain.write_gate_artifact fires gate_written hook after write."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from qor.scripts import gate_chain, gate_hooks


@pytest.fixture(autouse=True)
def _reset(monkeypatch, tmp_path):
    gate_hooks.reload_entry_points()
    monkeypatch.setattr(gate_hooks._workdir, "root", lambda: tmp_path)
    monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")
    yield
    gate_hooks.reload_entry_points()


def _minimal_plan_payload(sid: str) -> dict:
    return {
        "phase": "plan",
        "session_id": sid,
        "ts": "2026-05-01T20:00:00Z",
        "plan_path": "docs/plan-x.md",
        "phases": ["p1"],
        "ci_commands": ["python -m pytest"],
        "open_questions": [],
        "doc_tier": "standard",
        "terms": [],
        "boundaries": {"limitations": [], "non_goals": [], "exclusions": []},
        "change_class": "feature",
        "ai_provenance": {
            "system": "Qor-logic", "version": "0.42.0",
            "host": "unknown", "model_family": "unknown",
            "human_oversight": "absent", "ts": "2026-05-01T20:00:00Z",
        },
    }


def test_write_gate_artifact_fires_dispatch_with_correct_event_shape(monkeypatch, tmp_path):
    captured: list = []

    def fake_dispatch(event):
        captured.append(event)

    monkeypatch.setattr(gate_hooks, "dispatch_gate_written", fake_dispatch)
    # write_gate_artifact resolves session.get_or_create which expects .qor dir
    monkeypatch.chdir(tmp_path)

    sid = "test-session"
    payload = _minimal_plan_payload(sid)
    path = gate_chain.write_gate_artifact("plan", payload, session_id=sid)

    assert path.exists()
    assert len(captured) == 1
    event = captured[0]
    assert event.phase == "plan"
    assert event.session_id == sid
    assert event.artifact_path == path
    assert len(event.payload_sha256) == 64
    assert event.payload_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert event.ts.endswith("Z")


def test_payload_sha256_matches_artifact_file_bytes(monkeypatch, tmp_path):
    captured: list = []

    monkeypatch.setattr(gate_hooks, "dispatch_gate_written",
                        lambda e: captured.append(e))
    monkeypatch.chdir(tmp_path)

    sid = "test-session-2"
    payload = _minimal_plan_payload(sid)
    path = gate_chain.write_gate_artifact("plan", payload, session_id=sid)

    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    assert captured[0].payload_sha256 == expected
