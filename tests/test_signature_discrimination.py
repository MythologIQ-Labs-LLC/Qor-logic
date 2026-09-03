"""Phase 254: the severity collapse must not merge distinct defects.

Phase 253 keyed the signature on `(event_type, details.gate or
details.capability)`. Events carrying neither collapsed by type alone, so two
unrelated `degradation` defects counted as one. Phase 253 was written to stop
over-counting recurrence and introduced an under-count of distinct defects --
the more dangerous direction, because the number it produces looks better.
"""
from __future__ import annotations

from qor.scripts import check_shadow_threshold as cst

_ID = "a" * 64


def _event(eid: str, etype: str, severity: int, **details) -> dict:
    return {
        "id": (eid * 64)[:64],
        "ts": "2026-09-03T00:00:00Z",
        "skill": "qor-substantiate",
        "session_id": "2026-09-03T0000-aaaaaa",
        "event_type": etype,
        "severity": severity,
        "details": details,
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }


def test_distinct_patterns_do_not_collapse():
    """The exact pair found in the live genome.

    One defect is about amending a plan mid-audit; the other about a mandated
    reviewer going idle without delivering. Merging them hides real debt.
    """
    events = [
        _event("1", "degradation", 4, pattern="concurrent-edit-during-audit"),
        _event("2", "degradation", 3, pattern="delegated-review-delivery-failure"),
    ]

    assert cst.collapsed_severity(events) == 7


def test_identical_details_still_collapse():
    """The fix must not become "never collapse"."""
    events = [
        _event("3", "orchestration_override", 2, reason="same decision"),
        _event("4", "orchestration_override", 2, reason="same decision"),
    ]

    assert cst.collapsed_severity(events) == 2


def test_gate_still_wins_over_the_digest():
    """Phase 253 must survive for the events it was written for.

    The real skip events carry a `details.phase` that advances every seal. If
    the digest were consulted before `gate`, those 28 occurrences would stop
    collapsing and the original defect would return.
    """
    events = [
        _event("5", "gate_skipped_prerequisite_absent", 1,
               gate="data_api_acl_lint", phase=251),
        _event("6", "gate_skipped_prerequisite_absent", 1,
               gate="data_api_acl_lint", phase=252),
    ]

    assert cst.collapsed_severity(events) == 1


def test_capability_and_pattern_precedence():
    """The chain resolves gate > capability > pattern > digest."""
    gate = _event("7", "x", 1, gate="G", capability="C", pattern="P")
    cap = _event("8", "x", 1, capability="C", pattern="P")
    pat = _event("9", "x", 1, pattern="P")

    assert cst._signature(gate)[1] == "G"
    assert cst._signature(cap)[1] == "C"
    assert cst._signature(pat)[1] == "P"
    assert cst._signature(_event("b", "x", 1, other="o"))[1].startswith("details:")


def test_sliding_window_detector_collapses_by_pattern():
    """Tribunal ground V-1 (entry #709).

    `repeated_veto_pattern` reports one condition -- repeated VETOs are
    occurring -- but its `recent_phases` advances every firing. Without an
    explicit classifier the digest fallback turns one recurring condition into
    one signature per seal, growing without bound.
    """
    events = [
        _event("c", "repeated_veto_pattern", 3,
               pattern="repeated-veto", recent_phases=[234, 244], max_pass_count=2),
        _event("d", "repeated_veto_pattern", 3,
               pattern="repeated-veto", recent_phases=[243, 244], max_pass_count=2),
        _event("e", "repeated_veto_pattern", 3,
               pattern="repeated-veto", recent_phases=[246, 247], max_pass_count=2),
    ]

    assert cst.collapsed_severity(events) == 3


def test_live_genome_sum_rises_after_discrimination():
    """Anti-recurrence binding: this repository is the rule's first subject.

    Correcting an under-count makes the debt larger. A future change that
    quietly re-merges distinct defects would make this fail.
    """
    from qor.scripts import shadow_process as sp

    events = sp.read_events()
    unaddressed = [e for e in events if not e.get("addressed")]

    def shipped_rule(evs):
        seen, total = set(), 0
        for e in evs:
            d = e.get("details") or {}
            sig = (e["event_type"], d.get("gate") or d.get("capability"))
            if sig in seen:
                continue
            seen.add(sig)
            total += e["severity"]
        return total

    assert cst.collapsed_severity(events) > shipped_rule(unaddressed)
