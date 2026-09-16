"""GH #484: escalation payloads carry no collapsing key, so escalations of one
condition count separately.

`_signature` falls back to a digest of an event's own `details` when no
`gate`/`capability`/`pattern` key is present. An escalation's `details` is
always `{aged_entry_id, aged_skill, age_days}` -- none of those three -- and
`aged_entry_id` is unique per source event, so every escalation gets its own
digest and none collapse, even when they escalate the same underlying
condition. These tests pin the target behavior: an escalation stores the
root condition's own signature (`origin_signature`) at creation time, so
escalations of the same root collapse to one severity contribution, while
still never colliding with a live plain event's own signature namespace, and
staying identical across any number of escalation-of-escalation generations.
"""
from __future__ import annotations

from qor.scripts import check_shadow_threshold as cst


def _event(eid: str, event_type: str, severity: int, **details) -> dict:
    return {
        "id": eid,
        "ts": "2026-01-01T00:00:00Z",
        "skill": "qor-test",
        "session_id": "test-session",
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }


def _escalation_of(source: dict, eid: str, *, addressed: bool = False) -> dict:
    """The shape `sweep` appends (post GH #484): carries the root signature."""
    return {
        "id": eid,
        "ts": "2026-06-01T00:00:00Z",
        "skill": "qor-shadow-process",
        "session_id": "escalation-sweep",
        "event_type": cst.ESCALATION_EVENT,
        "severity": 5,
        "details": {
            "aged_entry_id": source["id"],
            "aged_skill": source["skill"],
            "age_days": 90,
            "origin_signature": list(cst._origin_signature(source)),
        },
        "addressed": addressed,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": source["id"],
    }


def test_escalations_of_the_same_root_condition_collapse():
    o1 = _event("o1", "degradation", 3, gate="g")
    o2 = _event("o2", "degradation", 3, gate="g")
    e1 = _escalation_of(o1, "E1")
    e2 = _escalation_of(o2, "E2")

    assert cst.collapsed_severity([e1, e2]) == 5, (
        "two escalations of the same root condition must contribute one "
        "severity-5 slot, not two (10)"
    )


def test_escalations_of_different_root_event_types_sharing_a_key_do_not_collapse():
    """The negative control GH #484 says the obvious positive-only test misses."""
    gate_override = _event("go", "gate_override", 3, gate="intent_lock")
    gate_skip = _event("gs", "gate_skipped_prerequisite_absent", 3, gate="intent_lock")
    esc_a = _escalation_of(gate_override, "EA")
    esc_b = _escalation_of(gate_skip, "EB")

    assert cst.collapsed_severity([esc_a, esc_b]) == 10, (
        "distinct event_types sharing a gate must stay distinguishable "
        "after escalation; collapsing to 5 would re-merge them"
    )


def test_escalation_of_an_escalation_carries_the_root_signature_unchanged():
    orig = _event("o", "degradation", 3, gate="g")
    esc1 = _escalation_of(orig, "E1")
    esc2 = _escalation_of(esc1, "E2")

    assert esc1["details"]["origin_signature"] == ["degradation", "g"]
    assert esc2["details"]["origin_signature"] == esc1["details"]["origin_signature"], (
        "an escalation-of-an-escalation must store the same root signature "
        "as its parent, not a wrapped/derived one"
    )


def test_a_three_generation_chain_collapses_with_a_fresh_single_generation_escalation_of_the_same_root():
    orig = _event("o", "degradation", 3, gate="g")
    esc1 = _escalation_of(orig, "E1")
    esc2 = _escalation_of(esc1, "E2")
    esc3 = _escalation_of(esc2, "E3")

    other_source = _event("o2", "degradation", 3, gate="g")
    fresh_esc = _escalation_of(other_source, "F1")

    assert cst.collapsed_severity([esc3, fresh_esc]) == 5, (
        "a 3-generation chain's live tip must collapse with a fresh "
        "single-generation escalation of the same root condition -- "
        "generation depth must not make the signature drift"
    )


def test_a_superseded_event_does_not_claim_its_signature_slot():
    """Re-pin of the existing supersession guarantee under the new shape.

    A live sibling sharing the escalated original's gate must still count in
    full: the escalation (its origin condition's signature, wrapped) must
    never collide with a plain live event's own signature.
    """
    superseded = _event("s", "degradation", 3, gate="g")
    esc = _escalation_of(superseded, "E1")
    sibling = _event("live", "degradation", 3, gate="g")

    assert cst.collapsed_severity([superseded, esc, sibling]) == 8, (
        "expected the escalation's 5 plus the live sibling's 3"
    )


def test_signature_of_escalation_never_equals_a_plain_events_signature():
    orig = _event("o", "degradation", 3, gate="g")
    esc = _escalation_of(orig, "E1")

    assert cst._signature(esc) != cst._signature(orig)
