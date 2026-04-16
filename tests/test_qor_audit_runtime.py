"""Tests for qor_audit_runtime — Phase 7 skill wiring."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import qor_audit_runtime as runtime
from qor.scripts import qor_platform as qplat
from qor.scripts import shadow_process
from qor.scripts import gate_chain
from qor.scripts import session


# ----- check_prior_artifact -----

def test_check_prior_artifact_delegates_to_gate_chain(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    # No plan artifact exists -> not found
    result = runtime.check_prior_artifact(session_id=sid)
    assert result.found is False
    assert "missing" in result.errors[0]


def test_check_prior_artifact_returns_valid_when_plan_exists(tmp_path, monkeypatch):
    gates = tmp_path / "gates"
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    marker = tmp_path / "current_session"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    sid = session.get_or_create(marker)

    # Write a valid plan artifact
    plan_dir = gates / sid
    plan_dir.mkdir(parents=True)
    plan_artifact = {
        "phase": "plan",
        "ts": "2026-04-15T18:00:00Z",
        "session_id": sid,
        "plan_path": "docs/plan.md",
        "phases": ["phase-a"],
    }
    (plan_dir / "plan.json").write_text(json.dumps(plan_artifact), encoding="utf-8")

    result = runtime.check_prior_artifact(session_id=sid)
    assert result.found is True
    assert result.valid is True


# ----- should_run_adversarial_mode -----

def _set_platform(tmp_path, monkeypatch, host: str, codex_plugin: bool):
    """Helper: write a platform marker with the requested host + codex-plugin state."""
    marker = tmp_path / "platform.json"
    monkeypatch.setattr(qplat, "MARKER_PATH", marker)
    state = {
        "version": "1",
        "detected": {"host": host, "gh_cli": False},
        "declared": {
            "codex-plugin": codex_plugin,
            "agent-teams": False,
            "mcp-servers": [],
            "host_declared": host,
        },
        "profile_applied": "test-fixture",
        "ts": "2026-04-15T18:00:00Z",
    }
    marker.write_text(json.dumps(state), encoding="utf-8")
    return marker


def test_adversarial_true_only_when_claude_code_with_codex(tmp_path, monkeypatch):
    _set_platform(tmp_path, monkeypatch, host="claude-code", codex_plugin=True)
    assert runtime.should_run_adversarial_mode() is True


def test_adversarial_false_on_kilo_code_even_if_codex_declared(tmp_path, monkeypatch):
    """codex-plugin is Claude Code-specific; declaration on other hosts must be ignored."""
    _set_platform(tmp_path, monkeypatch, host="kilo-code", codex_plugin=True)
    assert runtime.should_run_adversarial_mode() is False


def test_adversarial_false_when_codex_absent(tmp_path, monkeypatch):
    _set_platform(tmp_path, monkeypatch, host="claude-code", codex_plugin=False)
    assert runtime.should_run_adversarial_mode() is False


def test_adversarial_false_on_codex_standalone(tmp_path, monkeypatch):
    """codex-standalone host means Codex IS the agent; the plugin notion doesn't apply."""
    _set_platform(tmp_path, monkeypatch, host="codex-standalone", codex_plugin=True)
    assert runtime.should_run_adversarial_mode() is False


def test_adversarial_false_when_no_platform_marker(tmp_path, monkeypatch):
    marker = tmp_path / "platform.json"  # never created
    monkeypatch.setattr(qplat, "MARKER_PATH", marker)
    assert runtime.should_run_adversarial_mode() is False


def test_adversarial_false_when_host_unknown(tmp_path, monkeypatch):
    _set_platform(tmp_path, monkeypatch, host="unknown", codex_plugin=True)
    assert runtime.should_run_adversarial_mode() is False


# ----- emit_capability_shortfall -----

def test_emit_capability_shortfall_appends_sev2_event(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)
    monkeypatch.setattr(shadow_process, "UPSTREAM_LOG_PATH", log)

    eid = runtime.emit_capability_shortfall("codex-plugin", "2026-04-15T18:00-abcdef")
    assert len(eid) == 64

    events = shadow_process.read_events(log)
    assert len(events) == 1
    assert events[0]["event_type"] == "capability_shortfall"
    assert events[0]["severity"] == 2
    assert events[0]["details"]["capability"] == "codex-plugin"


def test_emit_capability_shortfall_details_shape(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)
    monkeypatch.setattr(shadow_process, "UPSTREAM_LOG_PATH", log)

    runtime.emit_capability_shortfall("agent-teams", "s-id")
    events = shadow_process.read_events(log)
    assert "reason" in events[0]["details"]
    assert "agent-teams" in events[0]["details"]["reason"]


# ----- emit_gate_override (sev 1) -----

def test_emit_gate_override_writes_sev1_event(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)
    monkeypatch.setattr(shadow_process, "UPSTREAM_LOG_PATH", log)

    eid = runtime.emit_gate_override("missing plan artifact", "s-id")
    events = shadow_process.read_events(log)
    assert len(events) == 1
    assert events[0]["event_type"] == "gate_override"
    assert events[0]["severity"] == 1
    assert events[0]["details"]["current_phase"] == "audit"
    assert events[0]["details"]["prior_phase"] == "plan"
