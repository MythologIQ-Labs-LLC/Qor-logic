"""Tests for shadow-process automation (Phase 4)."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import shadow_process
import check_shadow_threshold as cst
import create_shadow_issue as csi


def make_event(
    *,
    ts: str = "2026-04-15T12:00:00Z",
    skill: str = "qor-audit",
    session_id: str = "2026-04-15T12:00-abc123",
    event_type: str = "gate_override",
    severity: int = 1,
    details: dict | None = None,
    addressed: bool = False,
    source_entry_id: str | None = None,
) -> dict:
    ev = {
        "ts": ts,
        "skill": skill,
        "session_id": session_id,
        "event_type": event_type,
        "severity": severity,
        "details": details or {},
        "addressed": addressed,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": source_entry_id,
    }
    ev["id"] = shadow_process.compute_id(ev)
    return ev


# ----- Schema & id determinism -----

def test_event_id_deterministic():
    e1 = make_event()
    e2 = make_event()
    assert e1["id"] == e2["id"]


def test_event_id_differs_on_severity():
    a = make_event(severity=1)
    b = make_event(severity=2)
    assert a["id"] != b["id"]


def test_schema_validates_well_formed_event():
    e = make_event()
    shadow_process.validate(e)


def test_schema_rejects_out_of_range_severity():
    import jsonschema
    e = make_event(severity=1)
    e["severity"] = 0
    with pytest.raises(jsonschema.ValidationError):
        shadow_process.validate(e)


def test_schema_rejects_unknown_event_type():
    import jsonschema
    e = make_event()
    e["event_type"] = "mystery"
    with pytest.raises(jsonschema.ValidationError):
        shadow_process.validate(e)


# ----- Threshold logic -----

def test_threshold_sum_ignores_addressed():
    now = datetime(2026, 4, 15, 12, tzinfo=timezone.utc)
    events = [
        make_event(severity=5, addressed=True),
        make_event(severity=5, addressed=False, ts="2026-04-15T11:00:00Z"),
    ]
    _, _, total = cst.sweep(events, now)
    assert total == 5


def test_threshold_breach_triggers_marker(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    events = [
        make_event(severity=5, ts="2026-04-15T10:00:00Z"),
        make_event(severity=5, ts="2026-04-15T11:00:00Z", session_id="2026-04-15T11:00-def456"),
    ]
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    marker = tmp_path / "marker.json"
    monkeypatch.setattr(cst, "MARKER_PATH", marker)
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)

    rc = cst.main.__wrapped__() if hasattr(cst.main, "__wrapped__") else None
    # Call main via args
    import sys as _s
    old_argv = _s.argv
    _s.argv = ["check_shadow_threshold", "--log", str(log), "--now", "2026-04-15T13:00:00Z"]
    try:
        rc = cst.main()
    finally:
        _s.argv = old_argv

    assert rc == 10
    assert marker.exists()
    payload = json.loads(marker.read_text())
    assert payload["severity_sum"] == 10
    assert payload["event_count"] == 2


def test_under_threshold_no_marker(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    events = [make_event(severity=3)]
    log.write_text(json.dumps(events[0]) + "\n", encoding="utf-8")

    marker = tmp_path / "marker.json"
    marker.write_text("{}", encoding="utf-8")  # stale marker from prior run
    monkeypatch.setattr(cst, "MARKER_PATH", marker)

    import sys as _s
    _s.argv = ["check", "--log", str(log), "--now", "2026-04-15T13:00:00Z"]
    rc = cst.main()
    assert rc == 0
    assert not marker.exists()  # stale marker removed


# ----- Stale expiry (severity-gated) -----

def test_stale_expiry_sev1(tmp_path, monkeypatch):
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)  # 108 days after ts
    e = make_event(severity=1, ts="2026-04-15T00:00:00Z")
    updated, _, _ = cst.sweep([e], now)
    assert updated[0]["addressed"] is True
    assert updated[0]["addressed_reason"] == "stale"


def test_stale_expiry_sev2(tmp_path):
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)
    e = make_event(severity=2, ts="2026-04-15T00:00:00Z")
    updated, _, _ = cst.sweep([e], now)
    assert updated[0]["addressed"] is True


def test_sev3_never_stale_expires():
    now = datetime(2027, 4, 15, tzinfo=timezone.utc)  # ~1 year after
    e = make_event(severity=3, ts="2026-04-15T00:00:00Z")
    updated, escalations, _ = cst.sweep([e], now)
    # Original event NOT stale-expired
    orig = [x for x in updated if x["id"] == e["id"]][0]
    assert orig["addressed"] is False
    # But a self-escalation event WAS emitted
    assert len(escalations) == 1
    assert escalations[0]["event_type"] == "aged_high_severity_unremediated"
    assert escalations[0]["source_entry_id"] == e["id"]


def test_sev5_never_stale_expires():
    now = datetime(2027, 4, 15, tzinfo=timezone.utc)
    e = make_event(severity=5, ts="2026-04-15T00:00:00Z")
    updated, escalations, _ = cst.sweep([e], now)
    orig = [x for x in updated if x["id"] == e["id"]][0]
    assert orig["addressed"] is False
    assert len(escalations) == 1


# ----- Idempotence of self-escalation -----

def test_aged_escalation_idempotent():
    now = datetime(2027, 4, 15, tzinfo=timezone.utc)
    src = make_event(severity=3, ts="2026-04-15T00:00:00Z")
    # First sweep emits escalation
    updated1, esc1, _ = cst.sweep([src], now)
    assert len(esc1) == 1
    # Second sweep on updated list: must NOT emit another escalation
    _, esc2, _ = cst.sweep(updated1, now)
    assert len(esc2) == 0


def test_aged_escalation_idempotent_even_if_escalation_addressed():
    """Even if the escalation was addressed (issue created), the source is still aged
    and unaddressed — but a new escalation must not fire because one already exists."""
    now = datetime(2027, 4, 15, tzinfo=timezone.utc)
    src = make_event(severity=3, ts="2026-04-15T00:00:00Z")
    updated1, _, _ = cst.sweep([src], now)
    # Mark the escalation as addressed
    for ev in updated1:
        if ev["event_type"] == "aged_high_severity_unremediated":
            ev["addressed"] = True
    # Second sweep: still no new escalation
    _, esc2, _ = cst.sweep(updated1, now)
    assert len(esc2) == 0


# ----- Issue creation + addressed flip -----

def test_create_shadow_issue_flips_addressed(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    marker = tmp_path / "marker.json"
    monkeypatch.setattr(csi, "MARKER_PATH", marker)
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)

    events = [
        make_event(severity=5, ts="2026-04-15T10:00:00Z"),
        make_event(severity=5, ts="2026-04-15T11:00:00Z", session_id="2026-04-15T11:00-def456"),
    ]
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    marker.write_text(json.dumps({
        "breach_ts": "2026-04-15T12:00:00Z",
        "threshold": 10,
        "severity_sum": 10,
        "event_count": 2,
        "event_ids": [e["id"] for e in events],
        "next_action": "run remediate",
    }), encoding="utf-8")

    # Mock gh subprocess.run: auth status succeeds, issue create returns fake URL
    fake_url = "https://github.com/MythologIQ-Labs-LLC/Qor-logic/issues/42"

    def fake_run(cmd, *args, **kwargs):
        if cmd[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:3] == ["gh", "issue", "create"]:
            return subprocess.CompletedProcess(cmd, 0, fake_url + "\n", "")
        raise AssertionError(f"Unexpected subprocess call: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    import sys as _s
    _s.argv = ["create_shadow_issue", "--log", str(log)]
    rc = csi.main()
    assert rc == 0

    # Events now addressed + issue_url populated
    after = shadow_process.read_events(log)
    assert all(e["addressed"] is True for e in after)
    assert all(e["issue_url"] == fake_url for e in after)
    # Marker removed
    assert not marker.exists()


def test_create_shadow_issue_no_matching_events(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    marker = tmp_path / "marker.json"
    monkeypatch.setattr(csi, "MARKER_PATH", marker)
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)

    events = [make_event(severity=1)]
    log.write_text(json.dumps(events[0]) + "\n", encoding="utf-8")
    marker.write_text(json.dumps({
        "breach_ts": "2026-04-15T12:00:00Z",
        "threshold": 10,
        "event_ids": ["0" * 64],  # no match
    }), encoding="utf-8")

    import sys as _s
    _s.argv = ["create_shadow_issue", "--log", str(log), "--skip-auth"]
    rc = csi.main()
    assert rc == 0  # graceful exit, nothing done


# ----- mark-resolved (Phase 11A, Gap #2) -----

def test_mark_resolved_flips_events_without_url(tmp_path):
    e1 = make_event(severity=3)
    e2 = make_event(severity=4, ts="2026-04-15T13:00:00Z", session_id="s-2")
    log = tmp_path / "shadow.md"
    log.write_text("\n".join(json.dumps(e) for e in [e1, e2]) + "\n", encoding="utf-8")

    flipped = csi.mark_resolved(log, {e1["id"], e2["id"]})
    assert flipped == 2

    after = shadow_process.read_events(log)
    for e in after:
        assert e["addressed"] is True
        assert e["addressed_reason"] == "remediated"
        assert e["issue_url"] is None
        assert e["addressed_ts"] is not None


def test_mark_resolved_skips_already_addressed(tmp_path):
    e1 = make_event(addressed=True)
    e2 = make_event(severity=2, ts="2026-04-15T13:00:00Z")
    log = tmp_path / "shadow.md"
    log.write_text("\n".join(json.dumps(e) for e in [e1, e2]) + "\n", encoding="utf-8")

    flipped = csi.mark_resolved(log, {e1["id"], e2["id"]})
    assert flipped == 1  # only e2 was unaddressed


def test_mark_resolved_cli_requires_events(tmp_path):
    log = tmp_path / "shadow.md"
    log.write_text("", encoding="utf-8")
    import sys as _s
    _s.argv = ["create", "--mark-resolved", "--log", str(log)]
    rc = csi.main()
    assert rc == 2  # missing --events


def test_mark_resolved_cli_happy_path(tmp_path):
    e = make_event(severity=3)
    log = tmp_path / "shadow.md"
    log.write_text(json.dumps(e) + "\n", encoding="utf-8")
    import sys as _s
    _s.argv = ["create", "--mark-resolved", "--log", str(log), "--events", e["id"]]
    rc = csi.main()
    assert rc == 0
    after = shadow_process.read_events(log)
    assert after[0]["addressed"] is True
    assert after[0]["addressed_reason"] == "remediated"


# ----- Append helper -----

def test_append_event_atomic(tmp_path):
    log = tmp_path / "shadow.md"
    e = make_event()
    # Strip the id so append computes it
    del e["id"]
    eid = shadow_process.append_event(e, log)
    assert len(eid) == 64
    events = shadow_process.read_events(log)
    assert len(events) == 1
    assert events[0]["id"] == eid


def test_append_multiple_preserves_order(tmp_path):
    log = tmp_path / "shadow.md"
    for i in range(3):
        e = make_event(ts=f"2026-04-15T1{i}:00:00Z", session_id=f"s-{i}")
        del e["id"]
        shadow_process.append_event(e, log)
    events = shadow_process.read_events(log)
    assert len(events) == 3
    assert events[0]["ts"] < events[1]["ts"] < events[2]["ts"]
