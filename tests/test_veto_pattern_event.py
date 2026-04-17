"""Phase 26 Phase 1: veto pattern -> Shadow Genome event emission."""
from __future__ import annotations

from unittest.mock import patch


def test_maybe_emit_fires_when_pattern_detected():
    from qor.scripts.veto_pattern import PatternResult, maybe_emit_pattern_event
    result = PatternResult(detected=True, recent_phases=[24, 25], max_pass_count=3)
    with patch("qor.scripts.shadow_process.append_event") as mock_append:
        emitted = maybe_emit_pattern_event(result, session_id="test-session-12345")
    assert emitted is True
    mock_append.assert_called_once()
    call_kwargs = mock_append.call_args.kwargs
    call_args = mock_append.call_args.args
    event = call_args[0] if call_args else call_kwargs.get("event")
    assert event["event_type"] == "repeated_veto_pattern"
    assert event["severity"] == 3
    assert event["skill"] == "qor-audit"
    assert event["session_id"] == "test-session-12345"
    assert event["details"]["recent_phases"] == [24, 25]
    assert event["details"]["max_pass_count"] == 3


def test_maybe_emit_skips_when_no_pattern():
    from qor.scripts.veto_pattern import PatternResult, maybe_emit_pattern_event
    result = PatternResult(detected=False, recent_phases=[], max_pass_count=0)
    with patch("qor.scripts.shadow_process.append_event") as mock_append:
        emitted = maybe_emit_pattern_event(result, session_id="test-session-12345")
    assert emitted is False
    mock_append.assert_not_called()


def test_event_payload_schema_compliant():
    """The payload must satisfy shadow_event.schema.json's required fields."""
    from qor.scripts.veto_pattern import PatternResult, build_event_payload
    result = PatternResult(detected=True, recent_phases=[24, 25], max_pass_count=3)
    event = build_event_payload(result, session_id="test-session-12345")
    for field in ("ts", "skill", "session_id", "event_type", "severity",
                  "details", "addressed", "issue_url", "addressed_ts",
                  "addressed_reason", "source_entry_id"):
        assert field in event, f"missing required field: {field}"
    assert event["addressed"] is False
    assert event["issue_url"] is None
    assert event["addressed_ts"] is None
    assert event["addressed_reason"] is None
    assert event["source_entry_id"] is None
