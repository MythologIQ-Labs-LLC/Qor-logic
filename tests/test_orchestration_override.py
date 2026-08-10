"""Tests for qor/scripts/orchestration_override.py (Phase 37 B21)."""
from __future__ import annotations

import unittest.mock as mock


from qor.scripts import orchestration_override as oo, shadow_process


def test_override_appends_severity2_event(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    local.write_text("", encoding="utf-8")
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream), \
         mock.patch("qor.scripts.orchestration_override._workdir.root", return_value=tmp_path):
        event_id = oo.record(
            session_id="s-oo-1",
            skill="qor-plan",
            recommended_skill="/qor-remediate",
            reason="operator elected to continue planning",
        )
    assert event_id
    events = shadow_process.read_events(local)
    assert len(events) == 1
    assert events[0]["event_type"] == "orchestration_override"
    assert events[0]["severity"] == 2
    assert events[0]["details"]["recommended_skill"] == "/qor-remediate"


def test_override_writes_suppression_marker(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    local.write_text("", encoding="utf-8")
    upstream.write_text("", encoding="utf-8")
    sid = "s-oo-mark"
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream), \
         mock.patch("qor.scripts.orchestration_override._workdir.root", return_value=tmp_path):
        oo.record(sid, "qor-audit", "/qor-remediate", "inline amend")
    marker = tmp_path / ".qor" / "session" / sid / "escalation_suppressed"
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8").strip()  # non-empty timestamp


def test_gate_loop_counts_orchestration_override():
    from qor.scripts.remediate_pattern_match import PATTERN_RULES
    gate_loop_predicate = dict(PATTERN_RULES)["gate-loop"]
    e = lambda et: {"event_type": et, "id": "x"}
    # Two orchestration_overrides -> fires
    assert gate_loop_predicate([e("orchestration_override"), e("orchestration_override")]) is True


def test_mixed_gate_and_orchestration_override_count():
    from qor.scripts.remediate_pattern_match import PATTERN_RULES
    gate_loop_predicate = dict(PATTERN_RULES)["gate-loop"]
    e = lambda et: {"event_type": et, "id": "x"}
    # 1 gate_override + 1 orchestration_override -> fires (union >= 2)
    assert gate_loop_predicate([e("gate_override"), e("orchestration_override")]) is True
    # Only 1 override event total -> does not fire
    assert gate_loop_predicate([e("gate_override")]) is False
