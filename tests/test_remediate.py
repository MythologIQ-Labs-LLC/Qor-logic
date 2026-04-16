"""Tests for qor-remediate helpers (Phase 18).

Covers all 5 helpers: read_context, pattern_match, propose, mark_addressed, emit_gate.
Follows TDD order enumerated in docs/plan-qor-phase18-v2-qor-remediate.md.
"""
from __future__ import annotations

import json
import unittest.mock as mock
from pathlib import Path

import pytest

import shadow_process
import remediate_read_context as rrc
import remediate_pattern_match as rpm
import remediate_propose as rp
import remediate_mark_addressed as rma
import remediate_emit_gate as reg


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


def _seed(path: Path, events: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


# ===== Track A: remediate_read_context =====

def test_read_context_reads_both_files(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e_local = make_event(session_id="s-local")
    e_upstream = make_event(session_id="s-up", event_type="regression", severity=3)
    _seed(local, [e_local])
    _seed(upstream, [e_upstream])
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        groups = rrc.load_unaddressed_groups()
    total = sum(len(v) for v in groups.values())
    assert total == 2


def test_read_context_filters_addressed(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e_open = make_event(session_id="s-open")
    e_closed = make_event(session_id="s-closed", addressed=True)
    _seed(local, [e_open, e_closed])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        groups = rrc.load_unaddressed_groups()
    total = sum(len(v) for v in groups.values())
    assert total == 1


def test_read_context_groups_by_key(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    # Two events sharing (event_type, skill, session_id), one differing by session
    shared_sid = "2026-04-15T12:00-shared"
    e1 = make_event(session_id=shared_sid, ts="2026-04-15T12:00:00Z")
    e2 = make_event(session_id=shared_sid, ts="2026-04-15T13:00:00Z")
    e3 = make_event(session_id="other-sid", ts="2026-04-15T14:00:00Z")
    _seed(local, [e1, e2, e3])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        groups = rrc.load_unaddressed_groups()
    assert len(groups) == 2
    shared_key = ("gate_override", "qor-audit", shared_sid)
    assert shared_key in groups
    assert len(groups[shared_key]) == 2


def test_read_context_empty_returns_empty_dict(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    local.write_text("", encoding="utf-8")
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        groups = rrc.load_unaddressed_groups()
    assert groups == {}
    assert isinstance(groups, dict)


# ===== Track B: remediate_pattern_match =====

def test_classify_gate_loop():
    sid = "2026-04-15T12:00-gateloop"
    e1 = make_event(session_id=sid, event_type="gate_override")
    e2 = make_event(session_id=sid, event_type="gate_override", ts="2026-04-15T13:00:00Z")
    groups = {("gate_override", "qor-audit", sid): [e1, e2]}
    results = rpm.classify(groups)
    assert len(results) == 1
    assert results[0]["pattern"] == "gate-loop"
    assert set(results[0]["event_ids"]) == {e1["id"], e2["id"]}


def test_classify_regression():
    e = make_event(event_type="regression", severity=3)
    groups = {("regression", "qor-audit", e["session_id"]): [e]}
    results = rpm.classify(groups)
    assert any(r["pattern"] == "regression" for r in results)


def test_classify_hallucination():
    e = make_event(event_type="hallucination", severity=4)
    groups = {("hallucination", "qor-audit", e["session_id"]): [e]}
    results = rpm.classify(groups)
    assert any(r["pattern"] == "hallucination" for r in results)


def test_classify_capability_shortfall_aggregation():
    sid = "2026-04-15T12:00-shortfall"
    evs = [
        make_event(session_id=sid, event_type="capability_shortfall", severity=2,
                   ts=f"2026-04-15T1{i}:00:00Z") for i in range(3)
    ]
    # 3 events in one session, same (event_type, skill, session_id) -> one group
    groups = {("capability_shortfall", "qor-audit", sid): evs}
    results = rpm.classify(groups)
    assert any(r["pattern"] == "capability-shortfall aggregation" for r in results)


def test_classify_aged_high_severity():
    e = make_event(event_type="aged_high_severity_unremediated", severity=5,
                   source_entry_id="a" * 64)
    groups = {("aged_high_severity_unremediated", "qor-audit", e["session_id"]): [e]}
    results = rpm.classify(groups)
    assert any(r["pattern"] == "aged-high-severity" for r in results)


def test_classify_empty_returns_empty_list():
    assert rpm.classify({}) == []


# ===== Track C: remediate_propose =====

def test_propose_gate_loop_produces_proposal():
    classification = {
        "pattern": "gate-loop",
        "event_ids": ["a" * 64, "b" * 64],
        "skill": "qor-audit",
    }
    out = rp.propose(classification)
    assert "pattern" in out
    assert "proposal_kind" in out
    assert "proposal_text" in out
    assert "addressed_event_ids" in out


def test_propose_aged_high_severity_proposal():
    classification = {
        "pattern": "aged-high-severity",
        "event_ids": ["c" * 64],
        "skill": "qor-shadow-process",
    }
    out = rp.propose(classification)
    assert out["proposal_kind"] in {"skill", "agent", "gate", "doctrine"}


def test_propose_event_ids_preserved():
    ids = ["a" * 64, "b" * 64, "c" * 64]
    classification = {"pattern": "regression", "event_ids": ids, "skill": "qor-audit"}
    out = rp.propose(classification)
    assert set(out["addressed_event_ids"]) == set(ids)


# ===== Track D: remediate_mark_addressed =====

def test_mark_addressed_flips_events(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e1 = make_event(session_id="s-flip-1")
    e2 = make_event(session_id="s-flip-2", ts="2026-04-15T13:00:00Z")
    _seed(local, [e1, e2])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        flipped, missing = rma.mark_addressed([e1["id"]], session_id="remediate-session-1")
    assert flipped == 1
    assert missing == []
    after = shadow_process.read_events(local)
    by_id = {e["id"]: e for e in after}
    assert by_id[e1["id"]]["addressed"] is True
    assert by_id[e1["id"]]["addressed_reason"] == "remediated"
    assert by_id[e1["id"]]["addressed_ts"] is not None
    assert by_id[e2["id"]]["addressed"] is False


def test_mark_addressed_routes_to_origin_file(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e_local = make_event(session_id="s-local-route")
    e_upstream = make_event(session_id="s-upstream-route",
                            event_type="aged_high_severity_unremediated",
                            severity=5, source_entry_id="d" * 64)
    _seed(local, [e_local])
    _seed(upstream, [e_upstream])
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        flipped, missing = rma.mark_addressed(
            [e_local["id"], e_upstream["id"]], session_id="route-session"
        )
    assert flipped == 2
    assert missing == []
    local_after = shadow_process.read_events(local)
    upstream_after = shadow_process.read_events(upstream)
    assert len(local_after) == 1
    assert local_after[0]["id"] == e_local["id"]
    assert local_after[0]["addressed"] is True
    assert len(upstream_after) == 1
    assert upstream_after[0]["id"] == e_upstream["id"]
    assert upstream_after[0]["addressed"] is True


def test_mark_addressed_surfaces_missing_ids(tmp_path):
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e_real = make_event(session_id="s-real")
    _seed(local, [e_real])
    upstream.write_text("", encoding="utf-8")
    fake_id = "d" * 64
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        flipped, missing = rma.mark_addressed(
            [e_real["id"], fake_id], session_id="miss-session"
        )
    assert flipped == 1
    assert missing == [fake_id]


# ===== Track E: remediate_emit_gate =====

def test_emit_gate_writes_json_at_expected_path(tmp_path):
    proposal = {
        "pattern": "regression",
        "proposal_kind": "skill",
        "proposal_text": "Add grounding check to qor-plan Step 2b.",
        "addressed_event_ids": ["a" * 64],
    }
    path = reg.emit(proposal, session_id="gate-session-1", base_dir=tmp_path)
    expected = tmp_path / ".qor" / "gates" / "gate-session-1" / "remediate.json"
    assert path == expected
    assert expected.exists()


def test_emit_gate_payload_roundtrips(tmp_path):
    proposal = {
        "pattern": "gate-loop",
        "proposal_kind": "gate",
        "proposal_text": "Tighten qor-audit rubric for gate-loop detection.",
        "addressed_event_ids": ["b" * 64, "c" * 64],
    }
    path = reg.emit(proposal, session_id="gate-session-2", base_dir=tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["pattern"] == proposal["pattern"]
    assert payload["proposal_kind"] == proposal["proposal_kind"]
    assert payload["proposal_text"] == proposal["proposal_text"]
    assert payload["addressed_event_ids"] == proposal["addressed_event_ids"]
    assert "ts" in payload
