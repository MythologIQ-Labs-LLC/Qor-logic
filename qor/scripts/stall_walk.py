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
import re

from qor import workdir as _workdir
from qor.scripts import audit_history, findings_signature

# Phase 267: mirrors audit.schema.json's `ts` pattern. A value failing it is
# omitted rather than sorted, because this list is indexed positionally.
_TS_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")


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


def session_signature_timestamps(session_id: str) -> dict[str, list[str]]:
    """Return ``{signature: [ts, ...]}`` ascending, across the whole session.

    Phase 266 (GH #447): the sibling of ``count_session_signature_totals`` that
    keeps the timestamps that counter discards. Same records, same exclusions --
    PASS audits and LEGACY-sentinel records do not contribute -- so for every
    signature ``len(timestamps) == count``.

    Two properties the caller depends on, both established here rather than
    inherited:

    - Only a USABLE ``ts`` is collected: the key present AND its value matching
      the schema pattern. Phase 267 corrected the claim that stood here, which
      said ``audit_history.read`` re-validates every line so no record could
      lack one. It does not validate, by design (see that function), so this
      list can be SHORTER than ``count_session_signature_totals`` for the same
      signature. That asymmetry is deliberate: filtering the counter to match
      would change its answer for rows it counts today and could silence an
      escalation that fires now. The single consumer of the difference is the
      K-window anchor in ``cycle_count_escalator``, which degrades rather than
      indexing blindly.

      The pattern check is not fussiness. This list is sorted lexicographically
      and indexed positionally, so a malformed value would sort and anchor
      wrongly rather than merely being extra.
    - Each list is SORTED ascending before return. ``audit_history.read``
      returns records in file order and nothing enforces monotonic ``ts``; this
      module already sorts explicitly in ``_walk_backward`` for that reason.
    """
    stamps: dict[str, list[str]] = {}
    for record in audit_history.read(session_id):
        if record.get("verdict") != "VETO":
            continue
        sig = findings_signature.compute_record(record)
        if sig == findings_signature.LEGACY_SENTINEL:
            continue
        ts = record.get("ts")
        if not isinstance(ts, str) or not _TS_RE.fullmatch(ts):
            continue
        stamps.setdefault(sig, []).append(ts)
    return {sig: sorted(values) for sig, values in stamps.items()}
