"""Phase 285: an escalated event must not be counted beside its escalation.

At `STALE_DAYS` a severity 1-2 event is closed as stale; a severity >= 3 event is
not. Instead a severity-5 escalation naming it is appended and the original stays
open, so one condition contributes twice. The escalation is itself severity 5 and
`existing_escalations` holds source ids rather than escalation ids, so an
escalation escalates in turn: iterated and persisted, the threshold reads
55 / 95 / 135 / 175 at ninety-day intervals and rises without limit.

These tests drive `collapsed_severity` and `sweep` directly. Both are pure, so
nothing here touches the live genome -- the iterated projection feeds each round's
returned events into the next in memory rather than through
`shadow_process.write_events_per_source`, which writes to `LOCAL_LOG_PATH`.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

from qor.scripts import check_shadow_threshold as cst
from qor.scripts import shadow_process


def _event(eid: str, severity: int = 3, *, gate: str = "g", event_type: str = "degradation"):
    return {
        "id": eid,
        "ts": "2026-01-01T00:00:00Z",
        "skill": "qor-test",
        "session_id": "test-session",
        "event_type": event_type,
        "severity": severity,
        "details": {"gate": gate},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }


def _escalation_of(source: dict, eid: str, *, addressed: bool = False):
    """The shape `sweep` appends, built from the module's own constant."""
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
        },
        "addressed": addressed,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": source["id"],
    }


def test_an_escalated_original_is_not_counted_alongside_its_escalation():
    orig = _event("o")
    esc = _escalation_of(orig, "E1")
    assert cst.collapsed_severity([orig, esc]) == 5, (
        "one condition contributes twice: the original's 3 plus its escalation's 5"
    )


def test_an_unescalated_event_of_the_same_severity_still_counts():
    assert cst.collapsed_severity([_event("o")]) == 3, (
        "the rule must key on supersession, not on severity"
    )


def test_an_escalation_whose_source_is_absent_still_counts_itself():
    orphan = _escalation_of(_event("missing"), "E1")
    assert cst.collapsed_severity([orphan]) == 5, (
        "an escalation naming an id no event carries must not be dropped"
    )


def test_a_closed_escalation_returns_the_original_to_the_count():
    orig = _event("o")
    esc = _escalation_of(orig, "E1", addressed=True)
    assert cst.collapsed_severity([orig, esc]) == 3, (
        "supersession is a live relationship; resolving the escalation must not "
        "erase the debt it carried"
    )


def test_a_superseded_event_does_not_claim_its_signature_slot():
    """A live sibling sharing a superseded event's signature must still count.

    If the skip lands after `seen.add(sig)` the superseded event claims the slot
    and the sibling is silently dropped -- an under-count, the direction
    `check_shadow_threshold` itself calls the more dangerous one.
    """
    superseded = _event("s")
    esc = _escalation_of(superseded, "E1")
    sibling = _event("live")  # same gate, so same signature
    assert cst.collapsed_severity([superseded, esc, sibling]) == 8, (
        "expected the escalation's 5 plus the live sibling's 3"
    )


def test_a_chain_of_escalations_counts_only_its_live_tip():
    orig = _event("o")
    e1 = _escalation_of(orig, "E1")
    e2 = _escalation_of(e1, "E2")
    assert cst.collapsed_severity([orig, e1, e2]) == 5, (
        "each generation supersedes the one it names; only the tip contributes"
    )


def test_the_iterated_projection_is_constant():
    """Four ninety-day rounds over a copy of the real log, iterated in memory.

    `main` persists each round via `write_events_per_source`; doing that here
    would append synthetic escalations to `docs/PROCESS_SHADOW_GENOME.md`. The
    rounds are chained in memory instead.
    """
    base = [copy.deepcopy(e) for e in shadow_process.read_all_events()]
    now = datetime.now(timezone.utc)
    events = [copy.deepcopy(e) for e in base]
    totals = []
    for i in range(1, 5):
        updated, new_escalations, _ = cst.sweep(events, now + timedelta(days=90 * i))
        events = updated + new_escalations
        totals.append(cst.collapsed_severity(events))
    assert len(set(totals)) == 1, (
        f"the quantity must stop rising from escalation alone; saw {totals}"
    )
