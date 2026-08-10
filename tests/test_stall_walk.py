"""Tests for qor/scripts/stall_walk.py (Phase 37 B20 Part 2)."""
from __future__ import annotations

import json
import unittest.mock as mock


from qor.scripts import stall_walk, audit_history


def _audit(ts, verdict, cats=None, sid="s"):
    p = {
        "phase": "audit", "ts": ts, "session_id": sid,
        "target": "docs/plan.md", "verdict": verdict,
    }
    if cats is not None:
        p["findings_categories"] = cats
    elif verdict == "VETO":
        p["findings_categories"] = ["specification-drift"]
    return p


def _seed_audits(tmp_path, sid, audits):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        for a in audits:
            audit_history.append(a, session_id=sid)


def _seed_break(tmp_path, sid, kind, ts):
    path = tmp_path / sid / f"{kind}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "phase": kind, "ts": ts, "session_id": sid,
        "files_touched": ["x.py"],
    }), encoding="utf-8")


def _run(tmp_path, sid):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path):
        return stall_walk.run(sid)


def test_run_empty_session_returns_zero_tuple(tmp_path):
    count, sig, ts = _run(tmp_path, "s-empty")
    assert count == 0 and sig is None and ts is None


def test_run_counts_three_vetos_same_signature(tmp_path):
    sid = "s-streak"
    _seed_audits(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
    ])
    count, sig, ts = _run(tmp_path, sid)
    assert count == 3
    assert sig is not None and sig != "LEGACY"
    assert ts == "2026-04-20T12:00:00Z"


def test_run_resets_on_signature_change(tmp_path):
    sid = "s-change"
    _seed_audits(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["ghost-ui"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["ghost-ui"], sid),
    ])
    count, sig, _ = _run(tmp_path, sid)
    # Newest two match; oldest razor-overage is different sig -> run stops at 2
    assert count == 2


def test_run_resets_on_pass(tmp_path):
    sid = "s-pass"
    _seed_audits(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "PASS", [], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
    ])
    count, _, _ = _run(tmp_path, sid)
    # Walking newest-first: VETO (count=1) -> PASS (break). count=1.
    assert count == 1


def test_run_resets_on_legacy_record(tmp_path):
    sid = "s-legacy"
    legacy = _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid)
    legacy.pop("findings_categories")
    _seed_audits(tmp_path, sid, [
        legacy,
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
    ])
    count, _, _ = _run(tmp_path, sid)
    # Walking newest-first: VETO -> count=1. Legacy -> break.
    assert count == 1


def test_run_resets_on_implement_artifact_newer_than_prior_veto(tmp_path):
    sid = "s-impl"
    _seed_audits(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
    ])
    _seed_break(tmp_path, sid, "implement", "2026-04-20T12:01:00Z")
    count, _, _ = _run(tmp_path, sid)
    # Newest VETO counts (1), then implement.ts=12:01 is newer than prior VETO ts=12:00 -> break
    assert count == 1


def test_run_returns_oldest_matching_timestamp(tmp_path):
    sid = "s-oldest"
    _seed_audits(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
    ])
    _, _, first_ts = _run(tmp_path, sid)
    assert first_ts == "2026-04-20T12:00:00Z"
