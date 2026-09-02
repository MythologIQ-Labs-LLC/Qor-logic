"""Phase 253 (GH #410): closure states and threshold semantics.

The two-stage flip had no way to say "this remediation is real, and it belongs
to a different repository", so a consumer whose proposals were mostly upstream
could neither close them honestly nor resume development. And the threshold
counted every occurrence of a correctly-disclosed event, so it measured how many
phases had been sealed rather than accumulated process debt.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from qor.scripts import check_shadow_threshold as cst
from qor.scripts import remediate_mark_addressed as rma

SCHEMA = Path("qor/gates/schema/shadow_event.schema.json")


def _event(eid: str, etype: str, severity: int, **details) -> dict:
    return {
        # ids are SHA-256 per the schema; a short label is expanded rather than
        # loosening the pattern the real emitter satisfies.
        "id": (eid * 64)[:64].replace("m", "a").replace("n", "b"),
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


def _validate(event: dict) -> None:
    jsonschema.validate(event, json.loads(SCHEMA.read_text(encoding="utf-8")))


# --- fix 1: the closure vocabulary -------------------------------------------

def test_schema_accepts_deferred_upstream_with_an_issue_url():
    e = _event("a" * 12, "capability_shortfall", 2, gate="x")
    e |= {
        "addressed": True,
        "addressed_reason": "deferred_upstream",
        "addressed_ts": "2026-09-03T01:00:00Z",
        "issue_url": "https://example.invalid/org/repo/issues/1",
    }

    _validate(e)


def test_schema_rejects_deferred_upstream_without_issue_url():
    """Closure by transfer of ownership requires the transfer to be recorded.

    Without this the state is a synonym for "not my problem".
    """
    e = _event("b" * 12, "capability_shortfall", 2, gate="x")
    e |= {"addressed": True, "addressed_reason": "deferred_upstream",
          "addressed_ts": "2026-09-03T01:00:00Z", "issue_url": None}

    with pytest.raises(jsonschema.ValidationError):
        _validate(e)


def test_schema_still_rejects_an_unknown_reason():
    """The enum stays closed; adding one value must not open it."""
    e = _event("c" * 12, "capability_shortfall", 2, gate="x")
    e |= {"addressed": True, "addressed_reason": "because_i_said_so",
          "addressed_ts": "2026-09-03T01:00:00Z"}

    with pytest.raises(jsonschema.ValidationError):
        _validate(e)


# --- fix 6: recurrence collapse ----------------------------------------------

def test_repeated_disclosed_event_counts_once():
    """A permanent, correct property of a repository is not accumulating debt.

    `data_api_acl_lint` skips every seal because there are no SQL migrations.
    Counting each occurrence made the threshold measure phase count.
    """
    events = [
        _event(f"{i:012d}", "gate_skipped_prerequisite_absent", 1, gate="data_api_acl_lint")
        for i in range(3)
    ]

    assert cst.collapsed_severity(events) == 1


def test_distinct_signatures_each_count():
    """The pair that keeps collapse from becoming blanket suppression."""
    events = [
        _event("d" * 12, "gate_skipped_prerequisite_absent", 1, gate="data_api_acl_lint"),
        _event("e" * 12, "gate_skipped_prerequisite_absent", 1, gate="instruction_hygiene_lint"),
    ]

    assert cst.collapsed_severity(events) == 2


def test_collapse_ignores_addressed_events():
    events = [
        _event("f" * 12, "regression", 3, gate="g"),
        {**_event("g" * 12, "regression", 3, gate="h"), "addressed": True},
    ]

    assert cst.collapsed_severity(events) == 3


def test_live_genome_collapse_removes_the_recurrence_noise():
    """Anti-recurrence binding: this repository is the rule's first subject.

    Measured and stated honestly: the collapse removes recurrence noise but does
    NOT clear this repository's breach. Asserting that it would was false, and
    would have invited tuning the rule until the number looked acceptable.
    """
    from qor.scripts import shadow_process as sp

    events = sp.read_events()
    raw = sum(e["severity"] for e in events if not e.get("addressed"))
    collapsed = cst.collapsed_severity(events)

    assert collapsed <= raw
    assert collapsed < raw, "the live genome must actually contain recurrence"


# --- fix 4: the pending discount, bought with a validated enforcer -----------

def test_pending_without_an_enforcer_still_counts():
    """The compensating guard: a bare proposal must not silence the signal."""
    e = _event("h" * 12, "regression", 3, gate="g")
    e["addressed_pending"] = True

    assert cst.collapsed_severity([e]) == 3


def test_pending_with_a_valid_enforcer_is_excluded():
    """The discount is bought with the same evidence stage 2 demands."""
    e = _event("i" * 12, "regression", 3, gate="g")
    e |= {"addressed_pending": True,
          "closure_enforcer": "qor.scripts.check_shadow_threshold:collapsed_severity"}

    assert cst.collapsed_severity([e]) == 0


# --- fix 5: the routing escape ------------------------------------------------

def test_marker_clears_when_every_unaddressed_event_has_a_proposal():
    events = [
        {**_event("j" * 12, "regression", 3, gate="g"), "addressed_pending": True},
        {**_event("k" * 12, "degradation", 4, gate="h"), "addressed_pending": True},
    ]

    assert cst.every_unaddressed_event_has_a_pending_proposal(events) is True


def test_marker_persists_when_any_event_lacks_a_proposal():
    events = [
        {**_event("m" * 12, "regression", 3, gate="g"), "addressed_pending": True},
        _event("n" * 12, "degradation", 4, gate="h"),
    ]

    assert cst.every_unaddressed_event_has_a_pending_proposal(events) is False


# --- fix 3: per-change enforcers ---------------------------------------------

def test_per_change_enforcer_mapping_is_accepted_by_the_callee():
    """Pins the capability `/qor-audit` Step 4.2 now uses.

    `mark_addressed` has accepted `{event_id: enforcer}` since Phase 166; the
    skill passed a flat list with one top-level enforcer and never used it.
    """
    import inspect

    src = inspect.getsource(rma.mark_addressed)

    assert "Mapping" in inspect.signature(rma.mark_addressed).parameters["event_ids"].annotation \
        or "Mapping" in str(inspect.signature(rma.mark_addressed))
    assert "_normalized_enforcers" in src, (
        "per-change enforcer normalization must remain the validation path"
    )
