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

from qor import workdir as _workdir
from qor.scripts import session, stall_walk


ESCALATION_THRESHOLD = 3


@dataclass(frozen=True)
class EscalationRecommendation:
    suggested_skill: str
    escalation_reason: str
    signature: str
    cycle_count: int


def _suppression_active(
    session_id: str,
    first_match_ts: str | None,
    *,
    inclusive: bool = False,
) -> bool:
    """True when an operator decline should silence this escalation.

    The marker file holds the timestamp of the decline. ``first_match_ts`` is
    the anchor it is compared against, and the two modes anchor differently:

    - ``check`` passes the OLDEST audit of the current consecutive run, and
      compares strictly (``inclusive=False``, ``marker > anchor``). Its run
      resets on a PASS, a signature change or an implement break, so the anchor
      advances and the suppression naturally expires.
    - ``check_session_total`` passes the K-window floor -- the oldest of the
      most recent ``ESCALATION_THRESHOLD`` occurrences of one signature -- and
      compares inclusively (``inclusive=True``, ``marker >= anchor``). Its
      counter never resets, so the window is what makes the suppression expire
      after K further occurrences instead of lasting the session.

    ``inclusive`` exists because ``now_iso`` formats to whole seconds: a decline
    can share a second with the anchor record, and under a strict comparison
    that would mean a decline the operator just made does not take effect
    (Phase 266, GH #447). The default preserves ``check``'s behaviour exactly.
    """
    session.validate_session_id(session_id)  # GAP-SEC-05: no path traversal
    if first_match_ts is None:
        return False
    marker = _workdir.root() / ".qor" / "session" / session_id / "escalation_suppressed"
    if not marker.is_file():
        return False
    marker_ts = marker.read_text(encoding="utf-8").strip()
    if inclusive:
        return marker_ts >= first_match_ts
    return marker_ts > first_match_ts


def check(session_id: str) -> EscalationRecommendation | None:
    """Return an escalation recommendation or None."""
    session.validate_session_id(session_id)  # GAP-SEC-05/07: validate before stall_walk path build
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


def _anchor(ts_list: list[str]) -> str | None:
    """The K-window floor, degrading when the list is too short to hold one.

    Phase 267: a signature can be over threshold while its timestamp list is
    shorter than K, because `count_session_signature_totals` counts rows that
    `session_signature_timestamps` omits (see that function). Indexing blindly
    raised; skipping the suppression check instead would let an operator record
    a decline that does nothing, with no in-band escape.

    So the anchor degrades: full window, else the earliest stamp, else None.
    `_suppression_active` returns False on None, so an empty list yields "not
    suppressed" -- the safe direction for a governance signal, where the failure
    mode should be a prompt the operator can decline rather than a silence they
    never see.
    """
    if len(ts_list) >= ESCALATION_THRESHOLD:
        return ts_list[-ESCALATION_THRESHOLD]
    if ts_list:
        return ts_list[0]
    return None


def check_session_total(session_id: str) -> EscalationRecommendation | None:
    """Session-total mode: escalate when any signature reaches K=3 cumulative.

    Phase 69 (GH #43): catches the recurrence-across-artifacts pattern where
    the same signature appears 3+ times in one session but is interrupted by
    PASS audits or implement breaks (so the consecutive-streak ``check``
    misses it). Runs alongside ``check``; both modes can fire independently.

    Returns ``EscalationRecommendation`` with
    ``escalation_reason="session-total"`` when threshold met; ``None`` otherwise.

    Phase 266 (GH #447): reads the same suppression marker FILE as ``check``
    under different semantics, which the previous wording ("respects the same
    suppression marker") obscured while the code in fact read no marker at all.
    A decline silences one signature until it recurs ``ESCALATION_THRESHOLD``
    further times; suppressed signatures are filtered out before a winner is
    chosen, so declining one never masks another.
    """
    # Phase 267 (GH #448): validate before any path is built, matching `check`.
    # Phase 266's `_suppression_active` call also validates, but only after the
    # read below, so it did not close this.
    session.validate_session_id(session_id)
    totals = stall_walk.count_session_signature_totals(session_id)
    if not totals:
        return None
    over_threshold = [(sig, n) for sig, n in totals.items() if n >= ESCALATION_THRESHOLD]
    if not over_threshold:
        return None
    # Phase 266 (GH #447): filter suppressed signatures BEFORE selecting a
    # winner. Suppressing after selection made one declined signature mask
    # every other over-threshold signature, including ones the operator had
    # never seen.
    stamps = stall_walk.session_signature_timestamps(session_id)
    live = [
        (sig, n) for sig, n in over_threshold
        if not _suppression_active(
            session_id, _anchor(stamps.get(sig, [])), inclusive=True
        )
    ]
    if not live:
        return None
    live.sort(key=lambda item: (-item[1], item[0]))
    signature, count = live[0]
    return EscalationRecommendation(
        suggested_skill="/qor-remediate",
        escalation_reason="session-total",
        signature=signature,
        cycle_count=count,
    )
