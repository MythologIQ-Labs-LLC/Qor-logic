"""Phase 69 (#43): session-total signature counting in cycle_count_escalator.

The existing `stall_walk.run` counts CONSECUTIVE same-signature VETOs;
resets on any PASS / signature change / implement break. This misses
the session-arc pattern where the same signature recurs across multiple
artifacts in one session, non-consecutively.

Phase 69 adds `count_session_signature_totals` (aggregates per-signature
counts across the entire session history) and `check_session_total`
(surfaces escalation at K=3 cumulative per signature).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor import workdir as _workdir
from qor.scripts import audit_history, validate_gate_artifact as vga
from qor.scripts.cycle_count_escalator import (
    ESCALATION_THRESHOLD,
    EscalationRecommendation,
    check_session_total,
)
from qor.scripts.stall_walk import count_session_signature_totals


@pytest.fixture
def isolate_gates_dir(tmp_path, monkeypatch):
    """Re-point gate dir at tmp_path for test isolation.

    Both `vga.GATES_DIR` (used by validate_gate_artifact + downstream writers)
    AND `_workdir.gate_dir` (used by audit_history.history_path) must point
    at tmp_path. The fixture monkeypatches both.
    """
    isolated = tmp_path / ".qor" / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", isolated)
    monkeypatch.setattr(_workdir, "gate_dir", lambda: isolated)
    yield


def _audit_record(
    session_id: str,
    ts: str,
    verdict: str,
    categories: list[str] | None = None,
) -> dict:
    """Build a minimal audit gate record valid against audit.schema.json."""
    rec = {
        "phase": "audit",
        "ts": ts,
        "session_id": session_id,
        "target": "docs/plan-fixture.md",
        "verdict": verdict,
        "report_path": ".agent/staging/AUDIT_REPORT.md",
        "risk_grade": "L1",
    }
    if categories is not None and verdict == "VETO":
        rec["findings_categories"] = categories
    return rec


def _seed_history(records: list[dict], session_id: str) -> None:
    """Append records to the session's audit_history.jsonl."""
    for rec in records:
        audit_history.append(rec, session_id=session_id)


def test_empty_session_returns_no_signatures(tmp_path, isolate_gates_dir):
    sid = "fixture-empty"
    totals = count_session_signature_totals(sid)
    assert totals == {}


def test_single_veto_returns_count_one(tmp_path, isolate_gates_dir):
    sid = "fixture-single"
    _seed_history(
        [_audit_record(sid, "2026-05-14T10:00:00Z", "VETO", ["specification-drift"])],
        sid,
    )
    totals = count_session_signature_totals(sid)
    assert len(totals) == 1
    sig, count = next(iter(totals.items()))
    assert count == 1


def test_non_consecutive_triple_veto_with_pass_interleaved(tmp_path, isolate_gates_dir):
    """3 VETOs with same signature, PASS records interleaved -- session-total reaches 3."""
    sid = "fixture-non-consec"
    _seed_history(
        [
            _audit_record(sid, "2026-05-14T10:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T10:30:00Z", "PASS"),
            _audit_record(sid, "2026-05-14T11:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T11:30:00Z", "PASS"),
            _audit_record(sid, "2026-05-14T12:00:00Z", "VETO", ["specification-drift"]),
        ],
        sid,
    )
    totals = count_session_signature_totals(sid)
    assert len(totals) == 1
    sig, count = next(iter(totals.items()))
    assert count == 3, f"expected 3 non-consecutive VETOs, got {count}"


def test_consecutive_triple_veto_same_signature(tmp_path, isolate_gates_dir):
    """Consecutive triple VETO: both modes agree on count 3."""
    sid = "fixture-consec"
    _seed_history(
        [
            _audit_record(sid, "2026-05-14T10:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T10:30:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T11:00:00Z", "VETO", ["specification-drift"]),
        ],
        sid,
    )
    totals = count_session_signature_totals(sid)
    assert len(totals) == 1
    sig, count = next(iter(totals.items()))
    assert count == 3


def test_legacy_sentinel_excluded(tmp_path, isolate_gates_dir):
    """Audit records without findings_categories (pre-Phase-37) do not contribute."""
    sid = "fixture-legacy"
    _seed_history(
        [
            _audit_record(sid, "2026-05-14T10:00:00Z", "VETO"),  # no categories -> LEGACY
            _audit_record(sid, "2026-05-14T11:00:00Z", "VETO", ["specification-drift"]),
        ],
        sid,
    )
    totals = count_session_signature_totals(sid)
    # The real signature should be counted once; LEGACY should not appear.
    assert "LEGACY" not in totals
    assert sum(totals.values()) == 1


def test_multi_signature_isolation(tmp_path, isolate_gates_dir):
    """Different signatures count independently."""
    sid = "fixture-multi"
    _seed_history(
        [
            _audit_record(sid, "2026-05-14T10:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T11:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T12:00:00Z", "VETO", ["ghost-ui"]),
        ],
        sid,
    )
    totals = count_session_signature_totals(sid)
    assert len(totals) == 2
    counts = sorted(totals.values())
    assert counts == [1, 2]


def test_check_session_total_returns_recommendation_at_threshold(tmp_path, isolate_gates_dir):
    sid = "fixture-recommend"
    _seed_history(
        [
            _audit_record(sid, "2026-05-14T10:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T10:30:00Z", "PASS"),
            _audit_record(sid, "2026-05-14T11:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T11:30:00Z", "PASS"),
            _audit_record(sid, "2026-05-14T12:00:00Z", "VETO", ["specification-drift"]),
        ],
        sid,
    )
    rec = check_session_total(sid)
    assert isinstance(rec, EscalationRecommendation)
    assert rec.suggested_skill == "/qor-remediate"
    assert rec.escalation_reason == "session-total"
    assert rec.cycle_count == ESCALATION_THRESHOLD


def test_check_session_total_returns_none_below_threshold(tmp_path, isolate_gates_dir):
    sid = "fixture-below"
    _seed_history(
        [
            _audit_record(sid, "2026-05-14T10:00:00Z", "VETO", ["specification-drift"]),
            _audit_record(sid, "2026-05-14T11:00:00Z", "VETO", ["specification-drift"]),
        ],
        sid,
    )
    rec = check_session_total(sid)
    assert rec is None
