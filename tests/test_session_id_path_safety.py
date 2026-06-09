"""Phase 147 (GAP-SEC-04/05/07): operator-supplied session_id cannot escape
.qor/session/ at the orchestration-override / cycle-count-escalator path-build
sites. The validator existed but was applied inconsistently; these tests pin
that it is now enforced before any path is constructed.
"""
from __future__ import annotations

import pytest


def test_validate_rejects_traversal():
    from qor.scripts.session import validate_session_id

    for bad in ["../evil", "a/b", "..\\x", "", "a/../b", "/abs"]:
        with pytest.raises(ValueError):
            validate_session_id(bad)
    # a real sid does not raise
    validate_session_id("2026-06-09T0000-rsd351")


def test_record_rejects_traversal_sid(tmp_path, monkeypatch):
    monkeypatch.setattr("qor.workdir.root", lambda: tmp_path)
    from qor.scripts import orchestration_override

    with pytest.raises(ValueError):
        orchestration_override.record(
            "../../evil", skill="qor-plan", recommended_skill="/qor-remediate", reason="x"
        )
    # no file written outside .qor/session/
    assert not (tmp_path.parent / "evil").exists()
    assert not (tmp_path / "evil").exists()


def test_suppression_active_rejects_traversal_sid():
    from qor.scripts import cycle_count_escalator

    with pytest.raises(ValueError):
        cycle_count_escalator._suppression_active("../evil", "2026-06-09T00:00:00Z")


def test_record_accepts_valid_sid(tmp_path, monkeypatch):
    monkeypatch.setattr("qor.workdir.root", lambda: tmp_path)
    from qor.scripts import orchestration_override, shadow_process

    # hermetic: redirect the shadow-event append off the real genome file
    # (LOCAL_LOG_PATH is an import-time constant; the workdir patch cannot reach it)
    log = tmp_path / "shadow.jsonl"
    monkeypatch.setattr(shadow_process, "LOCAL_LOG_PATH", log)
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)

    sid = "2026-06-09T0000-abc123"
    event_id = orchestration_override.record(
        sid, skill="qor-plan", recommended_skill="/qor-remediate", reason="x"
    )
    assert event_id
    marker = tmp_path / ".qor" / "session" / sid / "escalation_suppressed"
    assert marker.is_file()
