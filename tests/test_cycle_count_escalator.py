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
