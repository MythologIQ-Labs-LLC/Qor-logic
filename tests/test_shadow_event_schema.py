"""Tests for shadow_event schema invariants (Phase 36).

Covers the addressed_pending field and its allOf invariant: events with
addressed=true AND addressed_reason="remediated" must also have
addressed_pending=true. Legacy events (addressed_reason in {issue_created,
stale, null}) remain unaffected.
"""
from __future__ import annotations

import pytest
import jsonschema

from qor.scripts import shadow_process


def _base_event(**overrides) -> dict:
    event = {
        "ts": "2026-04-20T12:00:00Z",
        "skill": "qor-audit",
        "session_id": "phase36-schema-test",
        "event_type": "gate_override",
        "severity": 1,
        "details": {},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    event.update(overrides)
    return event


def test_schema_allows_addressed_pending_optional():
    """Event without addressed_pending field validates (legacy compatibility)."""
    event = _base_event()
    assert "addressed_pending" not in event
    shadow_process.validate(event)


def test_schema_invariant_remediated_requires_pending():
    """addressed=true, addressed_reason=remediated, no addressed_pending -> fails."""
    event = _base_event(
        addressed=True,
        addressed_ts="2026-04-20T12:30:00Z",
        addressed_reason="remediated",
    )
    with pytest.raises(jsonschema.ValidationError):
        shadow_process.validate(event)


def test_schema_invariant_remediated_with_pending_true_validates():
    """addressed=true, reason=remediated, pending=true, enforcer set -> valid.

    Phase 166 (GH #249): a remediated closure also requires closure_enforcer;
    the tests/test_sg_closure_enforcement.py suite covers the rejection paths.
    """
    event = _base_event(
        addressed=True,
        addressed_ts="2026-04-20T12:30:00Z",
        addressed_reason="remediated",
        addressed_pending=True,
        closure_enforcer="qor.scripts.sg_closure_lint",
    )
    shadow_process.validate(event)


def test_schema_invariant_issue_created_does_not_require_pending():
    """Legacy close path (issue_created) unaffected by invariant."""
    event = _base_event(
        addressed=True,
        addressed_ts="2026-04-20T12:30:00Z",
        addressed_reason="issue_created",
        issue_url="https://example.com/issue/1",
    )
    assert "addressed_pending" not in event
    shadow_process.validate(event)


def test_schema_invariant_stale_does_not_require_pending():
    """Legacy stale-close path unaffected by invariant."""
    event = _base_event(
        addressed=True,
        addressed_ts="2026-04-20T12:30:00Z",
        addressed_reason="stale",
    )
    assert "addressed_pending" not in event
    shadow_process.validate(event)
