"""Phase 57: hook errors must not break the authoritative write path."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import gate_chain, gate_hooks


@pytest.fixture(autouse=True)
def _reset(monkeypatch, tmp_path):
    gate_hooks.reload_entry_points()
    monkeypatch.setattr(gate_hooks._workdir, "root", lambda: tmp_path)
    monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")
    monkeypatch.chdir(tmp_path)
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


def test_dispatch_raising_exception_does_not_prevent_artifact_write(monkeypatch):
    def boom(event):
        raise RuntimeError("hook crash")

    monkeypatch.setattr(gate_hooks, "dispatch_gate_written", boom)

    sid = "test-session"
    path = gate_chain.write_gate_artifact("plan", _minimal_plan_payload(sid), session_id=sid)
    assert path.exists()
    assert path.read_text(encoding="utf-8")  # non-empty


def test_dispatch_raising_keyboard_interrupt_propagates_after_write(monkeypatch):
    captured_path: dict = {}

    def interrupt(event):
        captured_path["path"] = event.artifact_path
        raise KeyboardInterrupt("operator Ctrl-C")

    monkeypatch.setattr(gate_hooks, "dispatch_gate_written", interrupt)

    sid = "test-session-kb"
    with pytest.raises(KeyboardInterrupt):
        gate_chain.write_gate_artifact("plan", _minimal_plan_payload(sid), session_id=sid)

    # The hook captured the artifact path before raising; verify the file exists
    # at that path (write completed before hook fired).
    assert "path" in captured_path, "hook must observe artifact_path before raising"
    assert captured_path["path"].exists(), "artifact must persist before hook fires"
