#!/usr/bin/env python3
"""Stall walk (Phase 37 B20 Part 2).

Walks session gate artifacts backward to count consecutive same-signature VETO
audits with no intervening implement/debug break. Returns
``(count, signature, first_match_ts)`` where ``first_match_ts`` is the OLDEST
audit timestamp contributing to the current run.

Used by both ``cycle_count_escalator.check`` (live escalation) and
``remediate_pattern_match`` plan-replay classifier (pattern analysis). Single
source of truth for stall detection logic.

Reset conditions (any one breaks the consecutive run):
- PASS audit record encountered
- findings_signature differs from the in-progress run's signature
- LEGACY-sentinel record encountered
- implement*.json or debug*.json artifact timestamp newer than the prior audit
"""
from __future__ import annotations

import json
from pathlib import Path

from qor import workdir as _workdir
from qor.scripts import audit_history, findings_signature


def _list_break_artifacts(session_id: str) -> list[dict]:
    """Return implement/debug singleton artifacts (if any) with ts + kind."""
    base = _workdir.gate_dir() / session_id
    breaks: list[dict] = []
    for kind in ("implement", "debug"):
        path = base / f"{kind}.json"
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8"))
            ts = payload.get("ts")
            if ts:
                breaks.append({"kind": kind, "ts": ts})
    return breaks


def _walk_backward(
    audits: list[dict],
    breaks: list[dict],
) -> tuple[int, str | None, str | None]:
    """Walk audits newest-to-oldest; count same-signature VETO streak."""
    if not audits:
        return 0, None, None
    sorted_audits = sorted(audits, key=lambda r: r.get("ts", ""), reverse=True)
    count = 0
    run_sig: str | None = None
    first_match_ts: str | None = None
    break_ts_values = [b["ts"] for b in breaks]

    for record in sorted_audits:
        if record.get("verdict") != "VETO":
            break
        sig = findings_signature.compute_record(record)
        if sig == findings_signature.LEGACY_SENTINEL:
            break
        if run_sig is None:
            run_sig = sig
        elif sig != run_sig:
            break
        ts = record.get("ts", "")
        if any(bt > ts for bt in break_ts_values if bt and first_match_ts is None):
            break
        if first_match_ts and any(bt > ts and bt <= first_match_ts for bt in break_ts_values):
            break
        count += 1
        first_match_ts = ts
    return count, run_sig, first_match_ts


def run(session_id: str) -> tuple[int, str | None, str | None]:
    """Public entry: return (count, signature, first_match_ts) for the session."""
    audits = audit_history.read(session_id)
    breaks = _list_break_artifacts(session_id)
    return _walk_backward(audits, breaks)


def count_session_signature_totals(session_id: str) -> dict[str, int]:
    """Return ``{signature: count}`` across the entire session audit history.

    Phase 69 (GH #43): the consecutive-streak mode in ``run()`` resets on any
    PASS / signature change / implement break. This counter does NOT reset --
    it counts every VETO contribution to each signature across the whole
    session, catching the session-arc recurrence pattern where the same
    signature recurs across multiple artifacts non-consecutively.

    LEGACY-sentinel records (pre-Phase-37 audits without findings_categories)
    are excluded; PASS audits do not contribute.
    """
    totals: dict[str, int] = {}
    for record in audit_history.read(session_id):
        if record.get("verdict") != "VETO":
            continue
        sig = findings_signature.compute_record(record)
        if sig == findings_signature.LEGACY_SENTINEL:
            continue
        totals[sig] = totals.get(sig, 0) + 1
    return totals
