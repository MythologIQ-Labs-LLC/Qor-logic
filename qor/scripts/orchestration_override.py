#!/usr/bin/env python3
"""Orchestration override (Phase 37 B21).

Records operator decline of a cycle-count escalation. Emits a severity-2
``orchestration_override`` shadow event AND writes
``.qor/session/<session_id>/escalation_suppressed`` (a timestamp marker that
suppresses re-prompts within the current session).

The ``orchestration_override`` event type is unioned with ``gate_override`` in
the gate-loop classifier (see ``remediate_pattern_match.PATTERN_RULES``), so
repeated overrides feed back into the remediation classifier.
"""
from __future__ import annotations

from pathlib import Path

from qor import workdir as _workdir
from qor.scripts import session, shadow_process


def _write_suppression_marker(session_id: str, ts: str) -> Path:
    session.validate_session_id(session_id)  # GAP-SEC-04: no path traversal
    marker_dir = _workdir.root() / ".qor" / "session" / session_id
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker = marker_dir / "escalation_suppressed"
    marker.write_text(ts, encoding="utf-8")
    return marker


def record(
    session_id: str,
    skill: str,
    recommended_skill: str,
    reason: str,
) -> str:
    """Append override event, write suppression marker, return event id."""
    session.validate_session_id(session_id)  # GAP-SEC-04: fail before any side effect
    ts = shadow_process.now_iso()
    event = {
        "ts": ts,
        "skill": skill,
        "session_id": session_id,
        "event_type": "orchestration_override",
        "severity": 2,
        "details": {"recommended_skill": recommended_skill, "reason": reason},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    event_id = shadow_process.append_event(event, attribution="LOCAL")
    _write_suppression_marker(session_id, ts)
    return event_id
