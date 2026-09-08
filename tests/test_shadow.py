"""Tests for shadow-process automation (Phase 4)."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone

import pytest

from qor.scripts import shadow_process
from qor.scripts import check_shadow_threshold as cst
from qor.scripts import create_shadow_issue as csi


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
    # Phase 253 (GH #410): distinct signatures. This test checks that a breach
    # writes the marker, not how severity is counted -- and since recurrence now
    # collapses, two events differing only in timestamp are one signature and
    # would sum to 5 rather than 10.
    events = [
        make_event(severity=5, ts="2026-04-15T10:00:00Z", details={"gate": "gate_a"}),
        make_event(severity=5, ts="2026-04-15T11:00:00Z",
                   session_id="2026-04-15T11:00-def456", details={"gate": "gate_b"}),
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
    orig = [x for x in updated if x["id"] == e["id"]][0]
    assert orig["addressed"] is False
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
    updated1, esc1, _ = cst.sweep([src], now)
    assert len(esc1) == 1
    _, esc2, _ = cst.sweep(updated1 + esc1, now)
    assert len(esc2) == 0


def test_aged_escalation_idempotent_even_if_escalation_addressed():
    """Even if the escalation was addressed (issue created), the source is still aged
    and unaddressed -- but a new escalation must not fire because one already exists."""
    now = datetime(2027, 4, 15, tzinfo=timezone.utc)
    src = make_event(severity=3, ts="2026-04-15T00:00:00Z")
    updated1, esc1, _ = cst.sweep([src], now)
    for ev in esc1:
        ev["addressed"] = True
    _, esc2, _ = cst.sweep(updated1 + esc1, now)
    assert len(esc2) == 0


# ----- Issue creation + addressed flip -----

def test_create_shadow_issue_flips_addressed(tmp_path, monkeypatch):
    log = tmp_path / "shadow.md"
    marker = tmp_path / "marker.json"
    monkeypatch.setattr(csi, "MARKER_PATH", marker)
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)

    # Phase 253 (GH #410): distinct signatures. This test checks that a breach
    # writes the marker, not how severity is counted -- and since recurrence now
    # collapses, two events differing only in timestamp are one signature and
    # would sum to 5 rather than 10.
    events = [
        make_event(severity=5, ts="2026-04-15T10:00:00Z", details={"gate": "gate_a"}),
        make_event(severity=5, ts="2026-04-15T11:00:00Z",
                   session_id="2026-04-15T11:00-def456", details={"gate": "gate_b"}),
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
    eid = shadow_process.append_event(e, log_path=log)
    assert len(eid) == 64
    events = shadow_process.read_events(log)
    assert len(events) == 1
    assert events[0]["id"] == eid


def test_append_multiple_preserves_order(tmp_path):
    log = tmp_path / "shadow.md"
    for i in range(3):
        e = make_event(ts=f"2026-04-15T1{i}:00:00Z", session_id=f"s-{i}")
        del e["id"]
        shadow_process.append_event(e, log_path=log)
    events = shadow_process.read_events(log)
    assert len(events) == 3
    assert events[0]["ts"] < events[1]["ts"] < events[2]["ts"]


# ----- Phase 14: classification-aware append -----

def test_append_event_classifies_upstream(tmp_path):
    upstream = tmp_path / "upstream.md"
    local = tmp_path / "local.md"
    import unittest.mock as mock
    with mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream), \
         mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local):
        e = make_event()
        del e["id"]
        shadow_process.append_event(e, attribution="UPSTREAM")
    assert shadow_process.read_events(upstream)
    assert not local.exists()


def test_id_source_map_distinguishes_files(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e1 = make_event(session_id="s-local")
    e2 = make_event(session_id="s-upstream")
    shadow_process.append_event(e1, log_path=local)
    shadow_process.append_event(e2, log_path=upstream)
    import unittest.mock as mock
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        src_map = shadow_process.id_source_map()
    stored_local = shadow_process.read_events(local)
    stored_upstream = shadow_process.read_events(upstream)
    assert src_map[stored_local[0]["id"]] == local
    assert src_map[stored_upstream[0]["id"]] == upstream


def test_escalation_events_not_dropped_during_sweep(tmp_path):
    """Escalation events classified UPSTREAM survive the dual-file write-back."""
    upstream = tmp_path / "upstream.md"
    local = tmp_path / "local.md"
    now = datetime(2026, 7, 1, tzinfo=timezone.utc)
    old_ts = (now - timedelta(days=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
    e = make_event(ts=old_ts, severity=4, session_id="s-aged")
    shadow_process.append_event(e, log_path=local)
    import unittest.mock as mock
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        events = shadow_process.read_all_events()
        updated, new_escalations, breach_sum = cst.sweep(events, now)
        assert len(new_escalations) > 0
        src_map = shadow_process.id_source_map()
        for esc in new_escalations:
            src_map[esc["id"]] = shadow_process.UPSTREAM_LOG_PATH
        shadow_process.write_events_per_source(
            updated + new_escalations, src_map,
        )
    escalations = shadow_process.read_events(upstream)
    assert len(escalations) > 0
    assert escalations[0]["event_type"] == "aged_high_severity_unremediated"


# ----- Phase 273 (GH #454): load_marker names which fault occurred -----

def _marker(tmp_path, body, *, encoding="utf-8"):
    """Point create_shadow_issue at a marker with the given raw content."""
    from qor.scripts import create_shadow_issue as csi

    p = tmp_path / "remediate-pending"
    if isinstance(body, bytes):
        p.write_bytes(body)
    else:
        p.write_text(body, encoding=encoding)
    csi.MARKER_PATH = p
    return csi, p


def test_load_marker_exits_on_a_truncated_marker(tmp_path, monkeypatch):
    from qor.scripts import create_shadow_issue as _csi

    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    csi, p = _marker(tmp_path, '{"event_ids": [')
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    assert "not readable JSON" in str(exc.value)
    assert "check_shadow_threshold" in str(exc.value)


def test_load_marker_exits_on_non_utf8_bytes(tmp_path, monkeypatch):
    """PowerShell Out-File writes UTF-16; the decode fails before json does."""
    from qor.scripts import create_shadow_issue as _csi

    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    csi, p = _marker(tmp_path, '{"event_ids": []}'.encode("utf-16"))
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    assert "not UTF-8" in str(exc.value)


def test_load_marker_exits_on_non_dict_json(tmp_path, monkeypatch):
    """Valid JSON that is not an object returned cleanly and failed later."""
    from qor.scripts import create_shadow_issue as _csi

    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    csi, p = _marker(tmp_path, "[]")
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    assert "expected an object" in str(exc.value)


def test_load_marker_exits_on_event_ids_as_a_string(tmp_path, monkeypatch):
    """The silent-success mode.

    `set("evt-1")` is a set of CHARACTERS, so nothing matches and main returned
    0 on a breached threshold. This survives an isinstance(dict) guard, which is
    why the shape check is not optional.
    """
    from qor.scripts import create_shadow_issue as _csi

    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    csi, p = _marker(
        tmp_path,
        json.dumps({"event_ids": "evt-1", "threshold": 10, "breach_ts": "2026-01-01T00:00:00Z"}),
    )
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    assert "event_ids" in str(exc.value)
    assert "expected a list" in str(exc.value)


def test_load_marker_exits_on_a_missing_required_key(tmp_path, monkeypatch):
    """The same deferred shape one frame later: build_body subscripts these."""
    from qor.scripts import create_shadow_issue as _csi

    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    csi, p = _marker(tmp_path, json.dumps({"event_ids": []}))
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    message = str(exc.value)
    assert "threshold" in message and "breach_ts" in message


def test_load_marker_still_returns_a_valid_marker(tmp_path, monkeypatch):
    """The good path is byte-identical; the writer's payload is admitted."""
    from qor.scripts import create_shadow_issue as _csi

    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    payload = {
        "breach_ts": "2026-01-01T00:00:00Z",
        "threshold": 10,
        "severity_sum": 15,
        "event_count": 1,
        "event_ids": ["a" * 64],
        "next_action": "Run /qor-remediate",
    }
    csi, p = _marker(tmp_path, json.dumps(payload))
    assert csi.load_marker() == payload


def test_load_marker_still_exits_when_absent(tmp_path, monkeypatch):
    from qor.scripts import create_shadow_issue as _csi

    monkeypatch.setattr(_csi, "MARKER_PATH", tmp_path / "nope", raising=False)
    with pytest.raises(SystemExit) as exc:
        _csi.load_marker()
    assert "No marker at" in str(exc.value)


# ----- Phase 278 (GH #459): the validator that guarded nothing is wired -----
#
# validate_event_id shipped, was tested, and was called from nowhere. Four sites
# build the set of ids to act on; a malformed id matches no event, the selection
# is empty, and the process exits 0 on a breached governance threshold.
#
# Phase 273 guarded event_ids' TYPE. These guard its ELEMENTS.


def _marker_with_ids(tmp_path, event_ids):
    from qor.scripts import create_shadow_issue as csi
    p = tmp_path / "remediate-pending"
    p.write_text(json.dumps({
        "event_ids": event_ids, "threshold": 10,
        "breach_ts": "2026-01-01T00:00:00Z", "severity_sum": 15,
        "event_count": 1, "next_action": "Run /qor-remediate",
    }), encoding="utf-8")
    csi.MARKER_PATH = p
    return csi


@pytest.mark.parametrize("ids,why", [
    (["evt-1"], "non-hash string -- passes Phase 273's list check"),
    ([12345], "integer -- the TypeError case"),
    (["a" * 32], "truncated hash"),
    (["A" * 64], "uppercase; the regex is lowercase-only"),
])
def test_marker_with_malformed_event_ids_exits_with_systemexit(tmp_path, monkeypatch, ids, why):
    """SystemExit, matching every sibling guard in load_marker -- not ValueError,
    which would be an unhandled traceback one line below a clean message."""
    from qor.scripts import create_shadow_issue as _csi
    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    csi = _marker_with_ids(tmp_path, ids)
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    assert "event id" in str(exc.value).lower(), why


def test_marker_rejection_message_names_the_regen_command(tmp_path, monkeypatch):
    """Every other guard here points at the one command that rebuilds the marker."""
    from qor.scripts import create_shadow_issue as _csi
    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    csi = _marker_with_ids(tmp_path, ["evt-1"])
    with pytest.raises(SystemExit) as exc:
        csi.load_marker()
    assert "check_shadow_threshold" in str(exc.value)


def test_marker_with_generated_valid_ids_is_accepted(tmp_path, monkeypatch):
    """Asserted over GENERATED ids, never a live count: PROCESS_SHADOW_GENOME.md
    is appended to by routine governance operation, so a test reading it goes red
    on the next shadow event."""
    import hashlib
    from qor.scripts import create_shadow_issue as _csi
    monkeypatch.setattr(_csi, "MARKER_PATH", _csi.MARKER_PATH, raising=False)
    generated = [hashlib.sha256(f"event-{i}".encode()).hexdigest() for i in range(3)]
    csi = _marker_with_ids(tmp_path, generated)
    assert csi.load_marker()["event_ids"] == generated


def _run_main(monkeypatch, argv):
    """create_shadow_issue.main() reads sys.argv directly and takes no argv
    parameter, so the CLI must be driven through sys.argv rather than a call
    argument."""
    import sys as _sys
    from qor.scripts import create_shadow_issue as csi
    monkeypatch.setattr(_sys, "argv", ["create_shadow_issue.py", *argv])
    return csi.main()


def _log_with_event(tmp_path, monkeypatch):
    """A shadow log holding one real, unaddressed event."""
    from qor.scripts import create_shadow_issue as csi
    from qor.scripts import shadow_process
    log = tmp_path / "PROCESS_SHADOW_GENOME.md"
    ev = make_event()
    del ev["id"]
    ev["addressed"] = False
    eid = shadow_process.append_event(ev, log_path=log)
    return csi, log, eid


@pytest.mark.parametrize("flag", ["--mark-resolved", "--flip-only"])
def test_events_flag_with_a_malformed_id_returns_two(tmp_path, monkeypatch, flag):
    """rc == 2, the measured convention for an argument fault at these sites."""
    csi, log, _ = _log_with_event(tmp_path, monkeypatch)
    argv = [flag, "--events", "evt-1", "--log", str(log)]
    if flag == "--flip-only":
        argv = ["--flip-only", "https://i/1", "--events", "evt-1", "--log", str(log)]
    assert _run_main(monkeypatch, argv) == 2


def test_flip_only_with_a_malformed_id_leaves_the_marker_intact(tmp_path, monkeypatch):
    """The load-bearing property is PLACEMENT, not the exit code.

    Phase 278 wrote this against the unconditional unlink: a test asserting only
    rc == 2 passed with the guard sitting after it, so the marker surviving was
    the witness that the guard ran first.

    Phase 279 (GH #472) removed that unlink, which HOLLOWED THIS TEST OUT --
    marker.exists() now holds wherever the guard sits, because nothing on this
    path deletes the marker at all. A correct test made vacuous by a later phase
    that never touched it.

    The witness is re-pinned on control flow, which survives changes to what
    happens afterwards: flip_events_only is replaced by a sentinel that fails on
    contact, so REACHING it fails the test. Guard-before-flip strictly implies
    guard-before-anything-after-the-flip, so this pins a superset of what the
    marker assertion pinned.

    raising=True (the default) is required, not stylistic: with raising=False a
    later rename of flip_events_only would create a dead attribute, the sentinel
    would never fire, and this test would hollow out again by exactly the
    mechanism it was rewritten to survive. pytest.fail raises an
    OutcomeException deriving from BaseException, so the sentinel also survives
    any future broad `except Exception` at the call site.

    The marker assertion is kept as characterization, not as the witness.
    """
    csi, log, _ = _log_with_event(tmp_path, monkeypatch)
    marker = tmp_path / "remediate-pending"
    marker.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(csi, "MARKER_PATH", marker, raising=False)

    def _must_not_be_reached(*_a, **_k):
        pytest.fail("the guard must short-circuit before flip_events_only")

    monkeypatch.setattr(csi, "flip_events_only", _must_not_be_reached)

    rc = _run_main(monkeypatch, ["--flip-only", "https://i/1", "--events", "evt-1", "--log", str(log)])

    assert rc == 2
    assert marker.exists()  # characterization: nothing on this path deletes it


def test_events_with_a_trailing_comma_is_still_accepted(tmp_path, monkeypatch):
    """Characterization test: this works today and must keep working. A trailing
    comma is an artifact of the separator, not an id the operator named."""
    csi, log, eid = _log_with_event(tmp_path, monkeypatch)
    assert _run_main(monkeypatch, ["--mark-resolved", "--events", eid + ",", "--log", str(log)]) == 0


def test_events_with_surrounding_whitespace_is_accepted(tmp_path, monkeypatch):
    """Red before: ' <id> ' marks 0 events today because the space is not stripped."""
    from qor.scripts import shadow_process
    csi, log, eid = _log_with_event(tmp_path, monkeypatch)
    assert _run_main(monkeypatch, ["--mark-resolved", "--events", f" {eid} ", "--log", str(log)]) == 0
    assert shadow_process.read_events(log)[0]["addressed"] is True


def test_events_naming_no_ids_returns_two(tmp_path, monkeypatch):
    """','   normalizes to an empty set. Without the require-non-empty rule that
    becomes a silent empty selection exiting 0 -- this phase's own defect,
    reintroduced through its fix."""
    csi, log, _ = _log_with_event(tmp_path, monkeypatch)
    assert _run_main(monkeypatch, ["--mark-resolved", "--events", ",", "--log", str(log)]) == 2


def test_a_valid_id_matching_no_event_still_exits_zero(tmp_path, monkeypatch):
    """An empty result is not an error. The defect is malformed input reported as
    success, not an empty result reported as success."""
    import hashlib
    csi, log, _ = _log_with_event(tmp_path, monkeypatch)
    absent = hashlib.sha256(b"no-such-event").hexdigest()
    assert _run_main(monkeypatch, ["--mark-resolved", "--events", absent, "--log", str(log)]) == 0


# ----- Phase 279 (GH #472): the marker's writer owns its removal -----
#
# --flip-only deleted the breach marker unconditionally, discarding the flipped
# count it had just printed. A well-formed id matching no event flipped nothing,
# destroyed the breach record, and returned 0 -- so the next run found nothing to
# do for a legitimate reason, indistinguishable from a clean state.
#
# The deletion is removed rather than conditioned. The marker asserts that the
# unaddressed severity sum exceeds the threshold; --flip-only never reads it, its
# ids come from a cross-repo sweep unrelated to it, and every condition available
# to it (flipped > 0, or the flipped ids covering the marker's) is a proxy for a
# comparison it lacks the inputs to make.


def _marker_and_event(tmp_path, monkeypatch):
    """A real unaddressed event plus a breach marker naming it."""
    csi, log, eid = _log_with_event(tmp_path, monkeypatch)
    marker = tmp_path / "remediate-pending"
    marker.write_text(json.dumps({
        "event_ids": [eid], "threshold": 10, "breach_ts": "2026-01-01T00:00:00Z",
        "severity_sum": 15, "event_count": 1, "next_action": "Run /qor-remediate",
    }), encoding="utf-8")
    monkeypatch.setattr(csi, "MARKER_PATH", marker)
    return csi, log, eid, marker


def test_flip_only_with_no_matching_events_leaves_the_marker(tmp_path, monkeypatch):
    """The reported defect. A well-formed id matching no event flips nothing --
    and must not destroy the record of a breach it knows nothing about."""
    import hashlib
    csi, log, _, marker = _marker_and_event(tmp_path, monkeypatch)
    absent = hashlib.sha256(b"no-such-event").hexdigest()

    rc = _run_main(monkeypatch, ["--flip-only", "https://i/1", "--events", absent, "--log", str(log)])

    assert rc == 0
    assert marker.exists(), "0 flipped must not delete the breach record"


def test_flip_only_with_matching_events_also_leaves_the_marker(tmp_path, monkeypatch):
    """Removal is unconditional in the other direction too: this command never
    deletes the marker. Without this row the behaviour is half-specified and
    invites reintroducing a `flipped > 0` condition -- which is wrong for the
    same reason, since flipping 1 of 10 breach events leaves the breach standing."""
    csi, log, eid, marker = _marker_and_event(tmp_path, monkeypatch)

    rc = _run_main(monkeypatch, ["--flip-only", "https://i/1", "--events", eid, "--log", str(log)])

    assert rc == 0
    assert marker.exists(), "the writer owns removal; this command never does"


def test_flip_only_still_flips_and_still_returns_zero(tmp_path, monkeypatch):
    """No regression in what the command is for."""
    csi, log, eid, _ = _marker_and_event(tmp_path, monkeypatch)

    rc = _run_main(monkeypatch, ["--flip-only", "https://i/1", "--events", eid, "--log", str(log)])

    assert rc == 0
    after = shadow_process.read_events(log)[0]
    assert after["addressed"] is True
    assert after["issue_url"] == "https://i/1"
