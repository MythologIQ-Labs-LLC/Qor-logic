"""Tests for qor/scripts/cycle_count_escalator.py (Phase 37 B21)."""
from __future__ import annotations

import json
import unittest.mock as mock


from qor.scripts import cycle_count_escalator as cce, audit_history


def _audit(ts, verdict, cats, sid):
    p = {"phase": "audit", "ts": ts, "session_id": sid,
         "target": "docs/plan.md", "verdict": verdict}
    if cats is not None:
        p["findings_categories"] = cats
    return p


def _seed(tmp_path, sid, audits):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        for a in audits:
            audit_history.append(a, session_id=sid)


def _check(tmp_path, sid):
    # Patch all three workdir call sites
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.cycle_count_escalator._workdir.root", return_value=tmp_path):
        return cce.check(sid)


def test_two_consecutive_veto_does_not_escalate(tmp_path):
    sid = "s-2"
    _seed(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
    ])
    assert _check(tmp_path, sid) is None


def test_three_consecutive_veto_same_signature_escalates(tmp_path):
    sid = "s-3"
    _seed(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
    ])
    rec = _check(tmp_path, sid)
    assert rec is not None
    assert rec.suggested_skill == "/qor-remediate"
    assert rec.escalation_reason == "cycle-count"
    assert rec.cycle_count == 3


def test_signature_change_resets_counter(tmp_path):
    sid = "s-chg"
    _seed(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["ghost-ui"], sid),
    ])
    # Walking backward: VETO(ghost-ui) count=1, then VETO(razor) different sig -> stop
    assert _check(tmp_path, sid) is None


def test_pass_between_resets_counter(tmp_path):
    sid = "s-pb"
    _seed(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "PASS", [], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:03:00Z", "VETO", ["razor-overage"], sid),
    ])
    # Walking backward: 2 VETOs then PASS breaks -> count=2
    assert _check(tmp_path, sid) is None


def test_implement_between_resets_counter(tmp_path):
    sid = "s-impl"
    _seed(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:03:00Z", "VETO", ["razor-overage"], sid),
    ])
    # Place implement.json between the 1st and later VETOs
    impl = tmp_path / sid / "implement.json"
    impl.parent.mkdir(parents=True, exist_ok=True)
    impl.write_text(json.dumps({
        "phase": "implement", "ts": "2026-04-20T12:01:00Z",
        "session_id": sid, "files_touched": ["x.py"],
    }), encoding="utf-8")
    # Walking backward from 12:03: count includes newest two (same sig).
    # The implement break at 12:01 prevents reaching the oldest VETO at 12:00.
    assert _check(tmp_path, sid) is None


def test_legacy_records_do_not_escalate(tmp_path):
    sid = "s-leg"
    # Three VETOs, all with findings_categories absent -> LEGACY sentinel -> break
    for ts in ("2026-04-20T12:00:00Z", "2026-04-20T12:01:00Z", "2026-04-20T12:02:00Z"):
        a = _audit(ts, "VETO", None, sid)
        a.pop("findings_categories", None)
        _seed(tmp_path, sid, [a])
    assert _check(tmp_path, sid) is None


def test_suppression_marker_skips_escalation(tmp_path):
    sid = "s-supp"
    _seed(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
    ])
    # Suppression marker with a timestamp newer than first_match_ts (12:00:00Z)
    marker_dir = tmp_path / ".qor" / "session" / sid
    marker_dir.mkdir(parents=True, exist_ok=True)
    (marker_dir / "escalation_suppressed").write_text("2026-04-20T12:05:00Z", encoding="utf-8")
    assert _check(tmp_path, sid) is None


# --- Phase 266 (GH #447): session-total suppression -------------------------
#
# `check_session_total` passed `None` where `_suppression_active` expects a
# timestamp, so the operator-decline marker was never read. The repair anchors
# on the K-window floor -- the oldest of the most recent ESCALATION_THRESHOLD
# occurrences -- filters suppressed signatures before selecting a winner, and
# compares inclusively so a decline sharing a whole second with a contributing
# record still suppresses.

def _check_total(tmp_path, sid):
    """Sibling of `_check` for the cumulative mode; same three patch targets."""
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.cycle_count_escalator._workdir.root", return_value=tmp_path):
        return cce.check_session_total(sid)


def _marker(tmp_path, sid, ts):
    d = tmp_path / ".qor" / "session" / sid
    d.mkdir(parents=True, exist_ok=True)
    (d / "escalation_suppressed").write_text(ts, encoding="utf-8")


_SIG_A = ["razor-overage"]
_SIG_B = ["specification-drift"]


def _vetoes(sid, cats, stamps):
    return [_audit(ts, "VETO", cats, sid) for ts in stamps]


def test_session_total_decline_suppresses_at_threshold(tmp_path):
    """T1: the marker is read at all. Red before the fix."""
    sid = "st-1"
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:00:00Z", "2026-04-20T12:01:00Z", "2026-04-20T12:02:00Z"]))
    _marker(tmp_path, sid, "2026-04-20T12:02:30Z")
    assert _check_total(tmp_path, sid) is None


def test_session_total_marker_older_than_anchor_does_not_suppress(tmp_path):
    """T2: pins direction. A fix that always suppresses fails here."""
    sid = "st-2"
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:00:00Z", "2026-04-20T12:01:00Z", "2026-04-20T12:02:00Z"]))
    _marker(tmp_path, sid, "2026-04-20T11:00:00Z")
    rec = _check_total(tmp_path, sid)
    assert rec is not None
    assert rec.escalation_reason == "session-total"


def test_session_total_suppression_survives_the_declining_audits_own_record(tmp_path):
    """T3: N = n0 + 1 must stay suppressed. Fails under the newest anchor.

    The marker MUST sit strictly between the n0-th and (n0+1)-th record. Seeding
    it after every record makes this pass under all three anchors and pins
    nothing -- see the plan's D1 discrimination matrix.
    """
    sid = "st-3"
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:00:00Z", "2026-04-20T12:01:00Z", "2026-04-20T12:02:00Z"]))
    _marker(tmp_path, sid, "2026-04-20T12:02:30Z")
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, ["2026-04-20T12:03:00Z"]))
    assert _check_total(tmp_path, sid) is None


def test_session_total_escalation_rearms_after_k_further_occurrences(tmp_path):
    """T4: N = n0 + K must fire again. Fails under the oldest anchor."""
    sid = "st-4"
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:00:00Z", "2026-04-20T12:01:00Z", "2026-04-20T12:02:00Z"]))
    _marker(tmp_path, sid, "2026-04-20T12:02:30Z")
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:03:00Z", "2026-04-20T12:04:00Z", "2026-04-20T12:05:00Z"]))
    rec = _check_total(tmp_path, sid)
    assert rec is not None
    assert rec.cycle_count == 6


def test_declined_signature_does_not_mask_an_undeclined_one(tmp_path):
    """T5: a suppressed winner must not hide another over-threshold signature."""
    sid = "st-5"
    _seed(tmp_path, sid, _vetoes(sid, _SIG_B, [
        "2026-04-20T12:00:00Z", "2026-04-20T12:01:00Z", "2026-04-20T12:02:00Z"]))
    _marker(tmp_path, sid, "2026-04-20T12:02:30Z")
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:10:00Z", "2026-04-20T12:11:00Z", "2026-04-20T12:12:00Z"]))
    rec = _check_total(tmp_path, sid)
    assert rec is not None
    from qor.scripts import findings_signature
    expected = findings_signature.compute_record(
        _audit("2026-04-20T12:10:00Z", "VETO", _SIG_A, sid))
    assert rec.signature == expected


def test_session_signature_timestamps_are_sorted_and_exclude_pass_and_legacy(tmp_path):
    """T6: ascending is established by sorting, not inherited from file order."""
    from qor.scripts import stall_walk, findings_signature
    sid = "st-6"
    legacy = _audit("2026-04-20T12:04:00Z", "VETO", None, sid)
    legacy.pop("findings_categories", None)
    _seed(tmp_path, sid, [
        _audit("2026-04-20T12:02:00Z", "VETO", _SIG_A, sid),   # out of order
        _audit("2026-04-20T12:00:00Z", "VETO", _SIG_A, sid),
        _audit("2026-04-20T12:01:00Z", "PASS", [], sid),       # excluded
        legacy,                                                # excluded
        _audit("2026-04-20T12:03:00Z", "VETO", _SIG_A, sid),
    ])
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path):
        stamps = stall_walk.session_signature_timestamps(sid)
        sig = findings_signature.compute_record(
            _audit("2026-04-20T12:00:00Z", "VETO", _SIG_A, sid))
    assert stamps[sig] == [
        "2026-04-20T12:00:00Z", "2026-04-20T12:02:00Z", "2026-04-20T12:03:00Z"]


def test_count_session_signature_totals_is_unchanged(tmp_path):
    """T7: D2 tripwire. The counter's return shape must not drift."""
    from qor.scripts import stall_walk, findings_signature
    sid = "st-7"
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:00:00Z", "2026-04-20T12:01:00Z"]))
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path):
        totals = stall_walk.count_session_signature_totals(sid)
        sig = findings_signature.compute_record(
            _audit("2026-04-20T12:00:00Z", "VETO", _SIG_A, sid))
    assert totals == {sig: 2}


def test_same_second_decline_still_suppresses(tmp_path):
    """T8: marker equal to the anchor. Requires the inclusive comparison.

    Red today for T1's reason (the marker is never read) and red again if the
    anchor and filter land WITHOUT `inclusive=True`. Only the second red tests
    the flag; it must be observed at the intermediate commit.
    """
    sid = "st-8"
    _seed(tmp_path, sid, _vetoes(sid, _SIG_A, [
        "2026-04-20T12:00:00Z", "2026-04-20T12:07:00Z",
        "2026-04-20T12:07:00Z", "2026-04-20T12:07:00Z"]))
    _marker(tmp_path, sid, "2026-04-20T12:07:00Z")
    assert _check_total(tmp_path, sid) is None
