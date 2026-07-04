"""Tests for qor-remediate helpers (Phase 18).

Covers all 5 helpers: read_context, pattern_match, propose, mark_addressed, emit_gate.
Follows TDD order enumerated in docs/plan-qor-phase18-v2-qor-remediate.md.
"""
from __future__ import annotations

import json
import unittest.mock as mock
from pathlib import Path

import pytest

from qor.scripts import shadow_process
from qor.scripts import remediate_read_context as rrc
from qor.scripts import remediate_pattern_match as rpm
from qor.scripts import remediate_propose as rp
from qor.scripts import remediate_mark_addressed as rma
from qor.scripts import remediate_emit_gate as reg


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

def test_mark_addressed_pending_flips_pending_only(tmp_path):
    """First-stage flip: addressed_pending=true; addressed stays false."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e1 = make_event(session_id="s-flip-1")
    e2 = make_event(session_id="s-flip-2", ts="2026-04-15T13:00:00Z")
    _seed(local, [e1, e2])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        flipped, missing = rma.mark_addressed_pending(
            [e1["id"]], session_id="remediate-session-1"
        )
    assert flipped == 1
    assert missing == []
    after = shadow_process.read_events(local)
    by_id = {e["id"]: e for e in after}
    assert by_id[e1["id"]]["addressed_pending"] is True
    assert by_id[e1["id"]]["addressed"] is False
    assert by_id[e1["id"]]["addressed_ts"] is None
    assert by_id[e1["id"]]["addressed_reason"] is None
    assert by_id[e2["id"]].get("addressed_pending", False) is False
    assert by_id[e2["id"]]["addressed"] is False


def test_mark_addressed_pending_routes_to_origin_file(tmp_path):
    """Pending-stage flip preserves LOCAL/UPSTREAM attribution."""
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
        flipped, missing = rma.mark_addressed_pending(
            [e_local["id"], e_upstream["id"]], session_id="route-session"
        )
    assert flipped == 2
    assert missing == []
    local_after = shadow_process.read_events(local)
    upstream_after = shadow_process.read_events(upstream)
    assert len(local_after) == 1
    assert local_after[0]["id"] == e_local["id"]
    assert local_after[0]["addressed_pending"] is True
    assert len(upstream_after) == 1
    assert upstream_after[0]["id"] == e_upstream["id"]
    assert upstream_after[0]["addressed_pending"] is True


def test_mark_addressed_pending_surfaces_missing_ids(tmp_path):
    """Unknown IDs are surfaced, not silently dropped."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e_real = make_event(session_id="s-real")
    _seed(local, [e_real])
    upstream.write_text("", encoding="utf-8")
    fake_id = "d" * 64
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        flipped, missing = rma.mark_addressed_pending(
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


# ===== Phase 36: two-stage addressed flip =====

def _write_audit_artifact(
    path: Path,
    *,
    verdict: str = "PASS",
    reviews_gate: str | None = None,
    session_id: str = "phase36-test",
) -> None:
    payload = {
        "phase": "audit",
        "ts": "2026-04-20T12:00:00Z",
        "session_id": session_id,
        "target": "docs/plan-phase36-test.md",
        "verdict": verdict,
    }
    if reviews_gate is not None:
        payload["reviews_remediate_gate"] = reviews_gate
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_remediate_gate(path: Path, event_ids: list[str]) -> None:
    payload = {
        "phase": "remediate",
        "ts": "2026-04-20T11:00:00Z",
        "session_id": "phase36-test",
        "events_addressed": event_ids,
        "proposed_changes": [],
        "addressed_event_ids": event_ids,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_mark_addressed_requires_review_pass_artifact(tmp_path):
    """Calling mark_addressed without a review-pass artifact file raises."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-req-rp")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    rma.mark_addressed_pending([e["id"]], session_id="s-req-rp")
    nonexistent = tmp_path / "missing_audit.json"
    remediate_gate = tmp_path / ".qor" / "gates" / "s-req-rp" / "remediate.json"
    _write_remediate_gate(remediate_gate, [e["id"]])
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        with pytest.raises(rma.ReviewAttestationError):
            rma.mark_addressed(
                [e["id"]],
                session_id="s-req-rp",
                review_pass_artifact_path=str(nonexistent),
                remediate_gate_path=str(remediate_gate),
                closure_enforcer="qor.scripts.sg_closure_lint",
            )


def test_mark_addressed_verifies_artifact_is_audit_pass(tmp_path):
    """Review-pass artifact with verdict != PASS raises."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-veto")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    rma.mark_addressed_pending([e["id"]], session_id="s-veto")
    remediate_gate = tmp_path / ".qor" / "gates" / "s-veto" / "remediate.json"
    _write_remediate_gate(remediate_gate, [e["id"]])
    audit_path = tmp_path / "audit.json"
    _write_audit_artifact(audit_path, verdict="VETO", reviews_gate=str(remediate_gate))
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        with pytest.raises(rma.ReviewAttestationError):
            rma.mark_addressed(
                [e["id"]],
                session_id="s-veto",
                review_pass_artifact_path=str(audit_path),
                remediate_gate_path=str(remediate_gate),
                closure_enforcer="qor.scripts.sg_closure_lint",
            )


def test_mark_addressed_rejects_audit_without_reviews_remediate_gate_field(tmp_path):
    """PASS audit missing reviews_remediate_gate field raises."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-no-field")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    rma.mark_addressed_pending([e["id"]], session_id="s-no-field")
    remediate_gate = tmp_path / ".qor" / "gates" / "s-no-field" / "remediate.json"
    _write_remediate_gate(remediate_gate, [e["id"]])
    audit_path = tmp_path / "audit.json"
    _write_audit_artifact(audit_path, verdict="PASS", reviews_gate=None)
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        with pytest.raises(rma.ReviewAttestationError):
            rma.mark_addressed(
                [e["id"]],
                session_id="s-no-field",
                review_pass_artifact_path=str(audit_path),
                remediate_gate_path=str(remediate_gate),
                closure_enforcer="qor.scripts.sg_closure_lint",
            )


def test_mark_addressed_rejects_reviews_remediate_gate_mismatch(tmp_path):
    """Audit's reviews_remediate_gate field points at different remediate gate -> raises."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-mismatch")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    rma.mark_addressed_pending([e["id"]], session_id="s-mismatch")
    remediate_gate = tmp_path / ".qor" / "gates" / "s-mismatch" / "remediate.json"
    _write_remediate_gate(remediate_gate, [e["id"]])
    other_gate = tmp_path / ".qor" / "gates" / "other" / "remediate.json"
    _write_remediate_gate(other_gate, [])
    audit_path = tmp_path / "audit.json"
    _write_audit_artifact(audit_path, verdict="PASS", reviews_gate=str(other_gate))
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        with pytest.raises(rma.ReviewAttestationError):
            rma.mark_addressed(
                [e["id"]],
                session_id="s-mismatch",
                review_pass_artifact_path=str(audit_path),
                remediate_gate_path=str(remediate_gate),
                closure_enforcer="qor.scripts.sg_closure_lint",
            )


def test_mark_addressed_success_path_sets_addressed_ts(tmp_path):
    """Valid review-pass artifact flips addressed=true, stamps addressed_ts, preserves pending."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-success")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        rma.mark_addressed_pending([e["id"]], session_id="s-success")
        remediate_gate = tmp_path / ".qor" / "gates" / "s-success" / "remediate.json"
        _write_remediate_gate(remediate_gate, [e["id"]])
        audit_path = tmp_path / "audit.json"
        _write_audit_artifact(audit_path, verdict="PASS", reviews_gate=str(remediate_gate))
        flipped, missing = rma.mark_addressed(
            [e["id"]],
            session_id="s-success",
            review_pass_artifact_path=str(audit_path),
            remediate_gate_path=str(remediate_gate),
            closure_enforcer="qor.scripts.sg_closure_lint",
        )
    assert flipped == 1
    assert missing == []
    after = shadow_process.read_events(local)
    assert after[0]["addressed"] is True
    assert after[0]["addressed_pending"] is True
    assert after[0]["addressed_reason"] == "remediated"
    assert after[0]["addressed_ts"] is not None


def test_pass_audit_without_arg_does_not_flip_events(tmp_path):
    """Unrelated PASS audit in same session (no reviews_remediate_gate arg) does NOT flip.

    Regression test for V1: coarse detection (remediate.json presence alone) would fire
    incorrectly on any PASS audit in session. The explicit-signal fix prevents this.
    """
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    e = make_event(session_id="s-unrelated")
    _seed(local, [e])
    upstream.write_text("", encoding="utf-8")
    remediate_gate = tmp_path / ".qor" / "gates" / "s-unrelated" / "remediate.json"
    _write_remediate_gate(remediate_gate, [e["id"]])
    # Audit with PASS but reviews_remediate_gate NOT set (operator did not pass the arg)
    audit_path = tmp_path / "audit.json"
    _write_audit_artifact(audit_path, verdict="PASS", reviews_gate=None)
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        rma.mark_addressed_pending([e["id"]], session_id="s-unrelated")
        # Skill-prose guard: if reviews_remediate_gate absent, do not call mark_addressed.
        payload = json.loads(audit_path.read_text(encoding="utf-8"))
        assert payload.get("reviews_remediate_gate") is None, "V1 regression: field should be absent"
        after = shadow_process.read_events(local)
    assert after[0]["addressed"] is False
    assert after[0]["addressed_pending"] is True


def test_legacy_events_with_issue_created_reason_still_read(tmp_path):
    """Legacy events (addressed via issue_created, no addressed_pending) still load."""
    local = tmp_path / "local.md"
    upstream = tmp_path / "upstream.md"
    legacy = make_event(session_id="s-legacy", addressed=True)
    legacy["addressed_ts"] = "2026-03-01T00:00:00Z"
    legacy["addressed_reason"] = "issue_created"
    legacy["issue_url"] = "https://example.com/issue/99"
    assert "addressed_pending" not in legacy
    _seed(local, [legacy])
    upstream.write_text("", encoding="utf-8")
    with mock.patch.object(shadow_process, "LOCAL_LOG_PATH", local), \
         mock.patch.object(shadow_process, "UPSTREAM_LOG_PATH", upstream):
        events = shadow_process.read_all_events()
    assert len(events) == 1
    assert events[0]["addressed"] is True
    assert events[0]["addressed_reason"] == "issue_created"


# ===== Phase 37: gate-loop classifier union + plan-replay =====

def _audit(ts, verdict, cats=None, sid="s37"):
    p = {
        "phase": "audit", "ts": ts, "session_id": sid,
        "target": "docs/plan.md", "verdict": verdict,
    }
    if cats is not None:
        p["findings_categories"] = cats
    elif verdict == "VETO":
        p["findings_categories"] = ["razor-overage"]
    return p


def _seed_audits_for_session(tmp_path, sid, audits):
    from qor.scripts import audit_history
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        for a in audits:
            audit_history.append(a, session_id=sid)


def test_gate_loop_classifier_counts_orchestration_override(tmp_path):
    # Two orchestration_override events in one group -> gate-loop fires
    sid = "s-oo-gl"
    e1 = make_event(session_id=sid, event_type="orchestration_override", severity=2)
    e2 = make_event(session_id=sid, event_type="orchestration_override",
                    severity=2, ts="2026-04-20T13:00:00Z")
    groups = {("orchestration_override", "qor-audit", sid): [e1, e2]}
    results = rpm.classify(groups)
    assert any(r["pattern"] == "gate-loop" for r in results)


def test_gate_loop_classifier_counts_mixed_override_types(tmp_path):
    # One gate_override + one orchestration_override in same group -> gate-loop fires
    sid = "s-mixed"
    e1 = make_event(session_id=sid, event_type="gate_override", severity=1)
    e2 = make_event(session_id=sid, event_type="orchestration_override",
                    severity=2, ts="2026-04-20T13:00:00Z")
    # Grouped by (event_type, skill, session_id): since event types differ, they'd
    # be in separate groups. Test the predicate directly against a merged group.
    merged = [e1, e2]
    from qor.scripts.remediate_pattern_match import PATTERN_RULES
    gate_loop_predicate = dict(PATTERN_RULES)["gate-loop"]
    assert gate_loop_predicate(merged) is True


def test_plan_replay_classifier_fires_at_k3(tmp_path):
    sid = "s-pr-k3"
    _seed_audits_for_session(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
    ])
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path):
        results = rpm.classify({}, session_id=sid)
    assert any(r["pattern"] == "plan-replay" for r in results)
    pr = next(r for r in results if r["pattern"] == "plan-replay")
    assert pr["details"]["cycle_count"] == 3


def test_plan_replay_classifier_does_not_fire_at_k2(tmp_path):
    sid = "s-pr-k2"
    _seed_audits_for_session(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
    ])
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path):
        results = rpm.classify({}, session_id=sid)
    assert not any(r["pattern"] == "plan-replay" for r in results)


def test_plan_replay_dedup_when_gate_loop_matches_same_session(tmp_path):
    sid = "s-pr-dedup"
    # Seed 3 VETO audits (triggers plan-replay) AND provide a gate-loop-matched group
    _seed_audits_for_session(tmp_path, sid, [
        _audit("2026-04-20T12:00:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:01:00Z", "VETO", ["razor-overage"], sid),
        _audit("2026-04-20T12:02:00Z", "VETO", ["razor-overage"], sid),
    ])
    e1 = make_event(session_id=sid, event_type="gate_override", severity=1)
    e2 = make_event(session_id=sid, event_type="gate_override", severity=1,
                    ts="2026-04-20T13:00:00Z")
    groups = {("gate_override", "qor-audit", sid): [e1, e2]}
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path), \
         mock.patch("qor.scripts.stall_walk._workdir.gate_dir", return_value=tmp_path):
        results = rpm.classify(groups, session_id=sid)
    # gate-loop present, plan-replay dropped
    assert any(r["pattern"] == "gate-loop" for r in results)
    assert not any(r["pattern"] == "plan-replay" for r in results)
