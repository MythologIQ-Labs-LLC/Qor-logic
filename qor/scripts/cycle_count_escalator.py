#!/usr/bin/env python3
"""Cycle-count escalator (Phase 37 B21).

Thin orchestrator over ``stall_walk.run``. Called from /qor-plan Step 2c and
/qor-audit Step 0 to surface a /qor-remediate escalation recommendation when
the session has accumulated >=3 consecutive same-signature VETO audits with
no implement/debug break.

Operator decline is recorded by ``orchestration_override.record``, which also
writes ``.qor/session/<sid>/escalation_suppressed``. The suppression marker is
honored here on the next check within the same session.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qor import workdir as _workdir
from qor.scripts import stall_walk


ESCALATION_THRESHOLD = 3


@dataclass(frozen=True)
class EscalationRecommendation:
    suggested_skill: str
    escalation_reason: str
    signature: str
    cycle_count: int


def _suppression_active(session_id: str, first_match_ts: str | None) -> bool:
    if first_match_ts is None:
        return False
    marker = _workdir.root() / ".qor" / "session" / session_id / "escalation_suppressed"
    if not marker.is_file():
        return False
    marker_ts = marker.read_text(encoding="utf-8").strip()
    return marker_ts > first_match_ts


def check(session_id: str) -> EscalationRecommendation | None:
    """Return an escalation recommendation or None."""
    count, signature, first_match_ts = stall_walk.run(session_id)
    if count < ESCALATION_THRESHOLD:
        return None
    if _suppression_active(session_id, first_match_ts):
        return None
    return EscalationRecommendation(
        suggested_skill="/qor-remediate",
        escalation_reason="cycle-count",
        signature=signature or "",
        cycle_count=count,
    )


def check_session_total(session_id: str) -> EscalationRecommendation | None:
    """Session-total mode: escalate when any signature reaches K=3 cumulative.

    Phase 69 (GH #43): catches the recurrence-across-artifacts pattern where
    the same signature appears 3+ times in one session but is interrupted by
    PASS audits or implement breaks (so the consecutive-streak ``check``
    misses it). Runs alongside ``check``; both modes can fire independently.

    Returns ``EscalationRecommendation`` with
    ``escalation_reason="session-total"`` when threshold met; ``None`` otherwise.
    Respects the same suppression marker as ``check``.
    """
    totals = stall_walk.count_session_signature_totals(session_id)
    if not totals:
        return None
    over_threshold = [(sig, n) for sig, n in totals.items() if n >= ESCALATION_THRESHOLD]
    if not over_threshold:
        return None
    if _suppression_active(session_id, None):
        return None
    over_threshold.sort(key=lambda item: (-item[1], item[0]))
    signature, count = over_threshold[0]
    return EscalationRecommendation(
        suggested_skill="/qor-remediate",
        escalation_reason="session-total",
        signature=signature,
        cycle_count=count,
    )
