#!/usr/bin/env python3
"""Gate chain library: check prior-phase artifacts, emit override events.

Used by skills at startup. Advisory enforcement (soft): missing/invalid
artifact returns a result indicating the shortfall; caller surfaces
the prompt to the user.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from qor.scripts import session
from qor.scripts import shadow_process
from qor.scripts import validate_gate_artifact as vga

from qor import workdir as _workdir

GATES_DIR = _workdir.gate_dir()

# Phase sequence (remediate is out-of-band, not listed here)
# Phase 59: ideation prepended as optional pre-research phase. Advisory-gate
# posture: research and plan accept ideation OR research as their prior. The
# `check_prior_artifact` helper recognizes the ideation predecessor when an
# ideation.json is present in the session dir.
CHAIN = ["research", "plan", "audit", "implement", "substantiate", "validate"]
IDEATION_PHASE = "ideation"


class ProvenanceError(Exception):
    """Raised when write_gate_artifact is called without QOR_SKILL_ACTIVE provenance.

    Phase 52 wiring: closes the skill-protocol bypass surface where any caller
    could write gate artifacts without proof that a skill protocol invoked them.
    Set QOR_SKILL_ACTIVE=<phase> to authorize the call. Set
    QOR_GATE_PROVENANCE_OPTIONAL=1 only for tests + grandfathered fixtures.
    """


@dataclass
class GateResult:
    found: bool
    valid: bool
    path: Path | None
    errors: list[str] = field(default_factory=list)


def prior_phase(current_phase: str) -> str | None:
    if current_phase not in CHAIN:
        return None
    idx = CHAIN.index(current_phase)
    if idx == 0:
        return None  # research has no prior
    return CHAIN[idx - 1]


def check_prior_artifact(
    current_phase: str, session_id: str | None = None
) -> GateResult:
    prior = prior_phase(current_phase)
    if prior is None:
        # Phase 59: research has no prior in CHAIN, but ideation may
        # optionally precede research. If ideation.json exists, accept it
        # as the prior; otherwise return the legacy "no prior" success.
        if current_phase == "research":
            return _check_ideation_predecessor(session_id) or GateResult(
                found=True, valid=True, path=None, errors=[],
            )
        return GateResult(found=True, valid=True, path=None, errors=[])

    sid = session_id or session.current()
    if sid is None:
        return GateResult(
            found=False, valid=False, path=None,
            errors=["no active session; run qor/scripts/session.py new"],
        )

    artifact = GATES_DIR / sid / f"{prior}.json"
    if not artifact.exists():
        # Phase 59: when checking plan's predecessor, accept ideation.json
        # as a valid alternative to research.json (advisory-gate posture).
        if current_phase == "plan":
            ideation_result = _check_ideation_predecessor(session_id)
            if ideation_result and ideation_result.found:
                return ideation_result
        return GateResult(
            found=False, valid=False, path=artifact,
            errors=[f"prior-phase artifact missing: {artifact}"],
        )

    errs = vga.validate_one(prior, artifact)
    return GateResult(
        found=True,
        valid=not errs,
        path=artifact,
        errors=errs,
    )


def _check_ideation_predecessor(session_id: str | None) -> GateResult | None:
    """Phase 59: recognize ideation.json as a valid predecessor.

    Returns a GateResult if an ideation gate artifact is present and validates;
    None otherwise (caller falls back to its legacy behavior).
    """
    sid = session_id or session.current()
    if sid is None:
        return None
    artifact = GATES_DIR / sid / "ideation.json"
    if not artifact.exists():
        return None
    errs = vga.validate_one("ideation", artifact)
    return GateResult(
        found=True, valid=not errs, path=artifact, errors=errs,
    )


def emit_gate_override(
    current_phase: str,
    prior_phase_name: str,
    reason: str,
    session_id: str,
    override_authority: str = "user",
    justification: str | None = None,
) -> str:
    """Append gate_override event (sev 1) to PROCESS_SHADOW_GENOME.

    Phase 54: consults ``override_friction.check`` before emitting; raises
    ``OverrideFrictionRequired`` when the per-session threshold is reached
    and no ``justification`` is supplied. Skill prose handles the exception
    by prompting the operator for a justification (>=50 chars) and
    re-calling with ``justification=<text>``.
    """
    from qor.scripts import override_friction

    friction = override_friction.check(session_id)
    if friction.threshold_reached and not justification:
        raise override_friction.OverrideFrictionRequired(
            f"Override-friction threshold reached "
            f"({friction.count}/{friction.threshold}) for session {session_id}. "
            f"Re-call emit_gate_override with justification=<text "
            f"(>={override_friction.MIN_JUSTIFICATION_LEN} chars)>."
        )

    event = {
        "ts": shadow_process.now_iso(),
        "skill": f"qor-{current_phase}",
        "session_id": session_id,
        "event_type": "gate_override",
        "severity": 1,
        "details": {
            "current_phase": current_phase,
            "prior_phase": prior_phase_name,
            "reason": reason,
            "override_authority": override_authority,
        },
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    if justification is not None:
        event = override_friction.record_with_justification(event, justification)
    return shadow_process.append_event(event, attribution="UPSTREAM")


def read_phase_artifact(phase: str, session_id: str | None = None) -> dict:
    """Load a previously-written gate artifact as a dict.

    Used by downstream phases that need the full payload, not just a
    validity check (see /qor-substantiate Step 4.7 doc-integrity wiring).
    """
    import json as _json
    sid = session_id or session.get_or_create()
    path = vga.GATES_DIR / sid / f"{phase}.json"
    if not path.exists():
        raise FileNotFoundError(f"Gate artifact not found: {path}")
    return _json.loads(path.read_text(encoding="utf-8"))


def write_gate_artifact(
    phase: str,
    payload: dict,
    session_id: str | None = None,
    ai_provenance: dict | None = None,
) -> "Path":
    """Write a gate artifact to .qor/gates/<session_id>/<phase>.json after schema validation.

    Skills with `gate_writes: <phase>` in frontmatter call this at end of execution
    so downstream phases can find the artifact via check_prior_artifact.

    `payload` should include the schema-required fields for the given phase
    (the helper injects `phase` and `session_id` if missing).

    Phase 37 Phase 1: for audit artifacts, also append to the session's
    `audit_history.jsonl` after the singleton write succeeds. Singleton remains
    authoritative for chain gating; history log is advisory for stall detection.

    Phase 52: provenance binding. Refuses writes from contexts that have not
    declared QOR_SKILL_ACTIVE=<phase> (matching the `phase` argument). The
    QOR_GATE_PROVENANCE_OPTIONAL=1 env bypasses the check (test-only;
    autouse fixture in tests/conftest.py sets it). Closes the bypass surface
    where any caller could write gate artifacts without skill provenance.
    """
    if not os.environ.get("QOR_GATE_PROVENANCE_OPTIONAL"):
        active = os.environ.get("QOR_SKILL_ACTIVE")
        if active is None:
            raise ProvenanceError(
                f"write_gate_artifact called without QOR_SKILL_ACTIVE env. "
                f"Set QOR_SKILL_ACTIVE={phase!r} when invoking the skill, or "
                f"QOR_GATE_PROVENANCE_OPTIONAL=1 to bypass (tests only)."
            )
        if active != phase:
            raise ProvenanceError(
                f"QOR_SKILL_ACTIVE={active!r} but write_gate_artifact called "
                f"with phase={phase!r}; skill-phase mismatch."
            )
    sid = session_id or session.get_or_create()
    if ai_provenance is not None:
        payload = {**payload, "ai_provenance": ai_provenance}
    path = vga.write_artifact(phase, payload, session_id=sid)
    if phase == "audit":
        from qor.scripts import audit_history
        audit_history.append(payload, session_id=sid)
    _fire_gate_written_hook(phase, sid, path)
    return path


def _fire_gate_written_hook(phase: str, session_id: str, path: "Path") -> None:
    """Phase 57: invoke gate_hooks.dispatch_gate_written after authoritative write.

    Read-back-from-disk hash so the event payload reflects what's persisted.
    Wraps in `try/except Exception` so hook errors never break the write.
    `KeyboardInterrupt` and `SystemExit` propagate (Phase 57 SIGINT-safety
    invariant per SG-BareExceptionSwallowsSignals-A).
    """
    import hashlib
    from qor.scripts import gate_hooks
    try:
        payload_bytes = path.read_bytes()
        event = gate_hooks.GateWrittenEvent(
            phase=phase,
            session_id=session_id,
            artifact_path=path,
            payload_sha256=hashlib.sha256(payload_bytes).hexdigest(),
            ts=shadow_process.now_iso(),
        )
        gate_hooks.dispatch_gate_written(event)
    except Exception:
        # Hook errors must not break the authoritative write path. KeyboardInterrupt
        # and SystemExit propagate naturally.
        pass
