from __future__ import annotations

import pytest

from qor.scripts import roadmap_state, roadmap_view


def _event(seq: int, event_type: str, payload: dict, *, version: str = "1") -> dict:
    return {
        "contract_version": version,
        "event_id": f"evt_{seq}",
        "roadmap_id": "demo",
        "seq": seq,
        "ts": "2026-08-27T00:00:00Z",
        "type": event_type,
        "payload": payload,
    }


def _created() -> dict:
    return _event(1, "roadmap_created", {
        "objective": {
            "title": "Deliver the pilot",
            "success_conditions": ["handoff is legal"],
            "exclusions": ["production implementation"],
        }
    })


def _node(seq: int, node_id: str, kind: str, *, authority: str | None = None) -> dict:
    return _event(seq, "node_added", {"node": {
        "id": node_id,
        "kind": kind,
        "title": node_id,
        "resolver": "/qor-research" if kind == "fact" else "authority" if kind == "decision" else "external",
        "authority_required": authority,
    }})


def test_rejects_unsupported_future_version() -> None:
    event = _created()
    event["contract_version"] = "2"
    with pytest.raises(roadmap_state.UnsupportedVersionError):
        roadmap_state.reduce_events([event])


def test_rejects_unknown_reference_and_cycle() -> None:
    with pytest.raises(roadmap_state.InvalidHistoryError, match="unknown roadmap node"):
        roadmap_state.reduce_events([
            _created(),
            _node(2, "a", "fact"),
            _event(3, "dependency_added", {
                "predecessor_id": "missing", "dependent_id": "a",
            }),
        ])

    events = [
        _created(),
        _node(2, "a", "fact"),
        _node(3, "b", "prerequisite"),
        _event(4, "dependency_added", {"predecessor_id": "a", "dependent_id": "b"}),
        _event(5, "dependency_added", {"predecessor_id": "b", "dependent_id": "a"}),
    ]
    with pytest.raises(roadmap_state.InvalidHistoryError, match="cycle rejected"):
        roadmap_state.reduce_events(events)


def test_frontier_keeps_independent_work_ready_and_respects_authority() -> None:
    events = [
        _created(),
        _node(2, "fact", "fact"),
        _node(3, "decision", "decision", authority="operator"),
        _node(4, "prereq", "prerequisite"),
        _event(5, "dependency_added", {
            "predecessor_id": "fact", "dependent_id": "decision",
        }),
    ]
    state = roadmap_state.reduce_events(events)
    assert roadmap_view.frontier_report(state)["frontier"] == ["fact", "prereq"]
    assert roadmap_view.frontier_report(
        state, available_authorities=["operator"]
    )["frontier"] == ["fact", "prereq"]

    events.append(_event(6, "node_resolved", {
        "node_id": "fact",
        "evidence_pointers": ["docs/research.md"],
        "rationale": "verified",
        "authority": None,
    }))
    state = roadmap_state.reduce_events(events)
    assert roadmap_view.frontier_report(state)["frontier"] == ["prereq"]
    assert roadmap_view.frontier_report(
        state, available_authorities=["operator"]
    )["frontier"] == ["decision", "prereq"]


def test_fact_requires_evidence_and_decision_requires_declared_authority() -> None:
    fact_events = [_created(), _node(2, "fact", "fact"), _event(3, "node_resolved", {
        "node_id": "fact", "evidence_pointers": [], "rationale": "", "authority": None,
    })]
    with pytest.raises(roadmap_state.InvalidHistoryError, match="evidence pointer"):
        roadmap_state.reduce_events(fact_events)

    decision_events = [
        _created(), _node(2, "decision", "decision", authority="operator"),
        _event(3, "node_resolved", {
            "node_id": "decision",
            "evidence_pointers": [],
            "rationale": "choice",
            "authority": "agent",
        }),
    ]
    with pytest.raises(roadmap_state.InvalidHistoryError, match="requires authority"):
        roadmap_state.reduce_events(decision_events)


def test_plan_handoff_fails_closed_until_scope_is_ready() -> None:
    events = [
        _created(),
        _node(2, "fact", "fact"),
        _event(3, "planning_scope_added", {"scope": {
            "id": "pilot", "title": "Pilot", "node_ids": ["fact"], "unresolved_space_ids": [],
        }}),
    ]
    state = roadmap_state.reduce_events(events)
    with pytest.raises(roadmap_state.InvalidHistoryError, match="not ready"):
        roadmap_view.build_plan_handoff(
            state,
            scope_id="pilot",
            predecessor_phase="research",
            predecessor_artifact=".qor/gates/s/research.json",
        )


def test_re_resolution_is_rejected_as_supersession() -> None:
    """Phase 239 promotion audit, blocking finding: a second node_resolved for
    an already-resolved node silently replaced recorded rationale, authority,
    and evidence -- decision supersession by another name, which the admitted
    P1 contract excludes in the plan's non_goals, the contract clause list,
    and the skill's own no-supersession claim."""
    events = [
        _created(),
        _node(2, "decision", "decision", authority="operator"),
        _event(3, "node_resolved", {
            "node_id": "decision",
            "evidence_pointers": [],
            "rationale": "original decision",
            "authority": "operator",
        }),
        _event(4, "node_resolved", {
            "node_id": "decision",
            "evidence_pointers": [],
            "rationale": "silently replaced rationale",
            "authority": "operator",
        }),
    ]
    with pytest.raises(roadmap_state.InvalidHistoryError, match="already resolved"):
        roadmap_state.reduce_events(events)

    fact_events = [
        _created(),
        _node(2, "fact", "fact"),
        _event(3, "node_resolved", {
            "node_id": "fact",
            "evidence_pointers": ["docs/evidence-a.md"],
            "rationale": "measured",
            "authority": None,
        }),
        _event(4, "node_resolved", {
            "node_id": "fact",
            "evidence_pointers": ["docs/evidence-b.md"],
            "rationale": "replaced evidence",
            "authority": None,
        }),
    ]
    with pytest.raises(roadmap_state.InvalidHistoryError, match="already resolved"):
        roadmap_state.reduce_events(fact_events)


def test_duplicate_identities_and_sequence_gaps_are_rejected() -> None:
    """Phase 239 promotion audit, secondary finding: the admitted contract
    enumerates duplicate identities and sequence gaps as reduction rejections;
    both were implemented but untested."""
    dup_node = [_created(), _node(2, "n1", "fact"), _node(3, "n1", "fact")]
    with pytest.raises(roadmap_state.InvalidHistoryError, match="duplicate"):
        roadmap_state.reduce_events(dup_node)

    dup_event_id = [_created(), _node(2, "n1", "fact")]
    clone = _node(3, "n2", "fact")  # distinct node id: only the event_id collides
    clone["event_id"] = "evt_2"
    dup_event_id.append(clone)
    with pytest.raises(roadmap_state.InvalidHistoryError, match="duplicate event_id"):
        roadmap_state.reduce_events(dup_event_id)

    gap = [_created(), _node(3, "n1", "fact")]  # seq jumps 1 -> 3
    with pytest.raises(roadmap_state.InvalidHistoryError, match="seq|sequence|contiguous"):
        roadmap_state.reduce_events(gap)
