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

import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from qor.scripts import shadow_process


class ReviewAttestationError(Exception):
    """Raised when a review-pass artifact fails verification during mark_addressed."""


class ClosureEnforcerError(Exception):
    """Raised when a closure lacks a valid executable enforcer (Phase 166; GH #249)."""


_MODULE_RE = re.compile(r"^qor\.(scripts|reliability)\.[a-z0-9_]+$")
_GATE_STEP_RE = re.compile(r"^/qor-[a-z-]+ Step [0-9]+(\.[0-9]+)*$")
_CANNOT_AUTOMATE_PREFIX = "cannot-automate:"


def _validate_closure_enforcer(value: str, repo_root: Path | None = None) -> None:
    """Accept exactly four enforcer forms; raise ClosureEnforcerError otherwise.

    Forms: (1) existing tests/test_*.py path; (2) importable qor.scripts.* /
    qor.reliability.* module; (3) '/qor-<skill> Step N[.M]' gate reference;
    (4) 'cannot-automate: <justification >= 50 chars>'.
    """
    root = repo_root or Path.cwd()
    if not value or not value.strip():
        raise ClosureEnforcerError("closure_enforcer is required and cannot be empty")
    if value.startswith(_CANNOT_AUTOMATE_PREFIX):
        justification = value[len(_CANNOT_AUTOMATE_PREFIX):].strip()
        if len(justification) < 50:
            raise ClosureEnforcerError(
                "cannot-automate justification must be >= 50 characters "
                f"(got {len(justification)})"
            )
        return
    if re.fullmatch(r"tests/test_[a-z0-9_]+\.py", value):
        if not (root / value).is_file():
            raise ClosureEnforcerError(f"enforcer test file does not exist: {value}")
        return
    if _MODULE_RE.fullmatch(value):
        if importlib.util.find_spec(value) is None:
            raise ClosureEnforcerError(f"enforcer module is not importable: {value}")
        return
    if _GATE_STEP_RE.fullmatch(value):
        return
    raise ClosureEnforcerError(
        f"closure_enforcer matches none of the four accepted forms: {value!r} "
        "(test path | qor module | '/qor-<skill> Step N' | 'cannot-automate: <justification>')"
    )


def _flip_event_fields(
    event_ids: list[str],
    fields: dict,
) -> tuple[int, list[str]]:
    """Apply ``fields`` overlay to each matching unaddressed event; route write per source."""
    events = shadow_process.read_all_events()
    src_map = shadow_process.id_source_map()
    target = set(event_ids)

    flipped = 0
    for event in events:
        if event["id"] in target and not event["addressed"]:
            event.update(fields)
            flipped += 1

    known_ids = set(src_map.keys())
    missing_ids = [eid for eid in event_ids if eid not in known_ids]

    if flipped:
        shadow_process.write_events_per_source(events, src_map)
    return flipped, missing_ids


def _flip_event_fields_per_event(
    enforcers: Mapping[str, str],
    fields: dict,
    *,
    addressed_only: bool = False,
) -> tuple[int, list[str]]:
    """Apply common fields plus each event's own closure enforcer.

    ``addressed_only`` is used only by the corrective path. It permits changing
    the closure citation of an already-remediated event while leaving its
    addressed state and timestamp intact.
    """
    events = shadow_process.read_all_events()
    src_map = shadow_process.id_source_map()
    changed = 0

    for event in events:
        event_id = event["id"]
        if event_id not in enforcers:
            continue
        if addressed_only:
            if not event.get("addressed") or event.get("addressed_reason") != "remediated":
                continue
            if event.get("closure_enforcer") == enforcers[event_id]:
                continue
            event["closure_enforcer"] = enforcers[event_id]
            changed += 1
            continue
        if event.get("addressed"):
            continue
        event.update(fields)
        event["closure_enforcer"] = enforcers[event_id]
        changed += 1

    known_ids = set(src_map.keys())
    missing_ids = [event_id for event_id in enforcers if event_id not in known_ids]
    if changed:
        shadow_process.write_events_per_source(events, src_map)
    return changed, missing_ids


def mark_addressed_pending(
    event_ids: list[str],
    session_id: str,  # noqa: ARG001 -- reserved for future audit trail wiring
) -> tuple[int, list[str]]:
    """Stage 1: flip addressed_pending=true only. addressed stays false."""
    return _flip_event_fields(event_ids, {"addressed_pending": True})


def _verify_review_pass_artifact(
    review_pass_artifact_path: str,
    remediate_gate_path: str,
) -> None:
    """Verify the audit artifact is a legitimate PASS review of the named remediate gate.

    Raises ReviewAttestationError on any failure. No return value.
    """
    artifact_path = Path(review_pass_artifact_path)
    if not artifact_path.is_file():
        raise ReviewAttestationError(
            f"review-pass artifact not found: {review_pass_artifact_path}"
        )
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewAttestationError(
            f"review-pass artifact unreadable: {review_pass_artifact_path}: {exc}"
        ) from exc
    if payload.get("phase") != "audit":
        raise ReviewAttestationError(
            f"review-pass artifact is not an audit gate (phase={payload.get('phase')!r})"
        )
    if payload.get("verdict") != "PASS":
        raise ReviewAttestationError(
            f"review-pass artifact verdict is not PASS: {payload.get('verdict')!r}"
        )
    declared_gate = payload.get("reviews_remediate_gate")
    if not declared_gate:
        raise ReviewAttestationError(
            "review-pass artifact missing 'reviews_remediate_gate' field "
            "(operator must pass reviews-remediate:<path> to /qor-audit)"
        )
    if Path(declared_gate).resolve() != Path(remediate_gate_path).resolve():
        raise ReviewAttestationError(
            f"review-pass artifact reviews_remediate_gate mismatch: "
            f"declared={declared_gate!r} expected={remediate_gate_path!r}"
        )


def _normalized_enforcers(
    event_ids: list[str] | Mapping[str, str],
    closure_enforcer: str | None,
    repo_root: Path | None,
) -> tuple[list[str], dict[str, str] | None]:
    """Validate shared or per-event enforcers without mutating durable state."""
    if isinstance(event_ids, Mapping):
        if closure_enforcer is not None:
            raise ClosureEnforcerError(
                "closure_enforcer must be omitted when event_ids is an event-to-enforcer mapping"
            )
        mapping = dict(event_ids)
        if not mapping:
            raise ClosureEnforcerError("event-to-enforcer mapping cannot be empty")
        for value in mapping.values():
            _validate_closure_enforcer(value, repo_root=repo_root)
        return list(mapping), mapping

    if closure_enforcer is None:
        raise ClosureEnforcerError("closure_enforcer is required for a list of event IDs")
    _validate_closure_enforcer(closure_enforcer, repo_root=repo_root)
    return list(event_ids), None


def mark_addressed(
    event_ids: list[str] | Mapping[str, str],
    session_id: str,  # noqa: ARG001 -- reserved for future audit trail wiring
    review_pass_artifact_path: str,
    remediate_gate_path: str,
    closure_enforcer: str | None = None,
    repo_root: Path | None = None,
) -> tuple[int, list[str]]:
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
) -> tuple[int, list[str]]:
    """Correct closure citations on already-remediated events under PASS attestation.

    This is deliberately narrow: it cannot reopen events, change timestamps, or
    alter the remediation reason. It only replaces a wrong ``closure_enforcer``
    with a newly validated one for events already closed as ``remediated``.
    """
    _, enforcers = _normalized_enforcers(event_enforcers, None, repo_root)
    assert enforcers is not None
    _verify_review_pass_artifact(review_pass_artifact_path, remediate_gate_path)
    return _flip_event_fields_per_event(enforcers, {}, addressed_only=True)
