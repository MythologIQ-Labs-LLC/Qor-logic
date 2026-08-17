#!/usr/bin/env python3
"""remediate: two-stage addressed flip (Phase 36, B19).

Phase 36 two-stage contract codified in doctrine-governance-enforcement.md §10.1:

Stage 1 -- ``mark_addressed_pending(ids, session_id)``:
    Flips ``addressed_pending: true`` on the given events. ``addressed`` stays
    ``false`` (and ``addressed_ts``/``addressed_reason`` remain ``null``). This
    signals "remediation proposed; awaiting review." Called from
    ``/qor-remediate`` Step 4.

Stage 2 -- ``mark_addressed(ids, session_id, review_pass_artifact_path,
remediate_gate_path)``:
    Flips ``addressed: true`` + ``addressed_reason: "remediated"`` + stamps
    ``addressed_ts`` ONLY after verifying a PASS audit artifact whose
    ``reviews_remediate_gate`` field references the remediate gate being
    closed. Called from ``/qor-audit`` Step 4 when operator passes the
    ``reviews-remediate:<path>`` skill arg.

On verification failure ``mark_addressed`` raises ``ReviewAttestationError``;
no event is mutated. This is the V1 resolution from Phase 36 Pass 1 audit --
review-pass attestation requires an explicit operator signal (the
``reviews_remediate_gate`` field), not mere file presence.

Phase 226 (GH #333): Stage 2 accepts either a list plus one shared enforcer or
an ``{event_id: closure_enforcer}`` mapping. Distinct findings therefore retain
the executable mechanism that actually guards each pattern. A separately
attested ``correct_closure_enforcers`` path repairs already-addressed events
whose historical closure citation was wrong without reopening the finding.

SG-032 guard: unknown IDs are surfaced in the returned ``missing`` list
rather than silently dropped.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, NamedTuple

from qor.scripts import shadow_process
from qor.scripts.remediate_attestation import (  # noqa: F401 -- exceptions re-exported
    ClosureEnforcerError,
    ReviewAttestationError,
    _normalized_enforcers,
    _validate_closure_enforcer,
    _verify_review_pass_artifact,
)


class MarkResult(NamedTuple):
    """Result of a flip operation (Phase 230; GH #341).

    ``skipped`` carries ids known to the shadow log but excluded by the
    invoked operation's eligibility guard -- already-addressed for the mark
    paths, not-remediated or citation-already-equal for the corrective path --
    so "nothing to do" is distinguishable from "nothing matched" (``missing``,
    the SG-032 surface, unchanged). Three fields by design: a result that can
    be two-unpacked back into ignorability would preserve the defect.
    """

    changed: int
    missing: list[str]
    skipped: list[str]


def _flip_event_fields(
    event_ids: list[str],
    fields: dict,
) -> MarkResult:
    """Apply ``fields`` overlay to each matching unaddressed event; route write per source."""
    events = shadow_process.read_all_events()
    src_map = shadow_process.id_source_map()
    target = set(event_ids)

    flipped = 0
    skipped: list[str] = []
    for event in events:
        if event["id"] not in target:
            continue
        if event["addressed"]:
            skipped.append(event["id"])
            continue
        event.update(fields)
        flipped += 1

    known_ids = set(src_map.keys())
    missing_ids = [eid for eid in event_ids if eid not in known_ids]

    if flipped:
        shadow_process.write_events_per_source(events, src_map)
    return MarkResult(flipped, missing_ids, skipped)


def _flip_event_fields_per_event(
    enforcers: Mapping[str, str],
    fields: dict,
    *,
    addressed_only: bool = False,
) -> MarkResult:
    """Apply common fields plus each event's own closure enforcer.

    ``addressed_only`` is used only by the corrective path. It permits changing
    the closure citation of an already-remediated event while leaving its
    addressed state and timestamp intact.
    """
    events = shadow_process.read_all_events()
    src_map = shadow_process.id_source_map()
    changed = 0
    skipped: list[str] = []

    for event in events:
        event_id = event["id"]
        if event_id not in enforcers:
            continue
        if addressed_only:
            if not event.get("addressed") or event.get("addressed_reason") != "remediated":
                skipped.append(event_id)
                continue
            if event.get("closure_enforcer") == enforcers[event_id]:
                skipped.append(event_id)
                continue
            event["closure_enforcer"] = enforcers[event_id]
            changed += 1
            continue
        if event.get("addressed"):
            skipped.append(event_id)
            continue
        event.update(fields)
        event["closure_enforcer"] = enforcers[event_id]
        changed += 1

    known_ids = set(src_map.keys())
    missing_ids = [event_id for event_id in enforcers if event_id not in known_ids]
    if changed:
        shadow_process.write_events_per_source(events, src_map)
    return MarkResult(changed, missing_ids, skipped)


def mark_addressed_pending(
    event_ids: list[str],
    session_id: str,  # noqa: ARG001 -- reserved for future audit trail wiring
) -> MarkResult:
    """Stage 1: flip addressed_pending=true only. addressed stays false.

    ``skipped`` names already-addressed events; an already-pending, not-yet-
    addressed event re-flips idempotently and counts in ``changed``.
    """
    return _flip_event_fields(event_ids, {"addressed_pending": True})


def mark_addressed(
    event_ids: list[str] | Mapping[str, str],
    session_id: str,  # noqa: ARG001 -- reserved for future audit trail wiring
    review_pass_artifact_path: str,
    remediate_gate_path: str,
    closure_enforcer: str | None = None,
    repo_root: Path | None = None,
) -> MarkResult:
    """Stage 2: after enforcer + review-pass verification, flip addressed=true.

    ``event_ids`` may be a list when every event shares ``closure_enforcer``, or
    an ``{event_id: enforcer}`` mapping when each finding has its own closure
    mechanism. Every enforcer is validated before the PASS attestation and no
    durable event is mutated unless the whole request is valid.
    """
    ids, enforcers = _normalized_enforcers(event_ids, closure_enforcer, repo_root)
    _verify_review_pass_artifact(review_pass_artifact_path, remediate_gate_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fields = {
        "addressed": True,
        "addressed_ts": now,
        "addressed_reason": "remediated",
        "addressed_pending": True,
    }
    if enforcers is not None:
        return _flip_event_fields_per_event(enforcers, fields)
    assert closure_enforcer is not None
    fields["closure_enforcer"] = closure_enforcer
    return _flip_event_fields(ids, fields)


def correct_closure_enforcers(
    event_enforcers: Mapping[str, str],
    session_id: str,  # noqa: ARG001 -- reserved for future audit trail wiring
    review_pass_artifact_path: str,
    remediate_gate_path: str,
    repo_root: Path | None = None,
) -> MarkResult:
    """Correct closure citations on already-remediated events under PASS attestation.

    This is deliberately narrow: it cannot reopen events, change timestamps, or
    alter the remediation reason. It only replaces a wrong ``closure_enforcer``
    with a newly validated one for events already closed as ``remediated``.
    """
    _, enforcers = _normalized_enforcers(event_enforcers, None, repo_root)
    assert enforcers is not None
    _verify_review_pass_artifact(review_pass_artifact_path, remediate_gate_path)
    return _flip_event_fields_per_event(enforcers, {}, addressed_only=True)
