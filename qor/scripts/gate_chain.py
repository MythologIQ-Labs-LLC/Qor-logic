#!/usr/bin/env python3
"""Gate chain library: check prior-phase artifacts, emit override events.

Used by skills at startup. Advisory enforcement (soft): missing/invalid
artifact returns a result indicating the shortfall; caller surfaces
the prompt to the user.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from qor.scripts import session
from qor.scripts import shadow_process
from qor.scripts import validate_gate_artifact as vga

from qor import workdir as _workdir

GATES_DIR = _workdir.gate_dir()

# Phase sequence (remediate is out-of-band, not listed here)
CHAIN = ["research", "plan", "audit", "implement", "substantiate", "validate"]


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
        return GateResult(found=True, valid=True, path=None, errors=[])

    sid = session_id or session.current()
    if sid is None:
        return GateResult(
            found=False, valid=False, path=None,
            errors=["no active session; run qor/scripts/session.py new"],
        )

    artifact = GATES_DIR / sid / f"{prior}.json"
    if not artifact.exists():
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


def emit_gate_override(
    current_phase: str,
    prior_phase_name: str,
    reason: str,
    session_id: str,
    override_authority: str = "user",
) -> str:
    """Append gate_override event (sev 1) to PROCESS_SHADOW_GENOME."""
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
) -> "Path":
    """Write a gate artifact to .qor/gates/<session_id>/<phase>.json after schema validation.

    Skills with `gate_writes: <phase>` in frontmatter call this at end of execution
    so downstream phases can find the artifact via check_prior_artifact.

    `payload` should include the schema-required fields for the given phase
    (the helper injects `phase` and `session_id` if missing).

    Phase 37 Phase 1: for audit artifacts, also append to the session's
    `audit_history.jsonl` after the singleton write succeeds. Singleton remains
    authoritative for chain gating; history log is advisory for stall detection.

    B24: after the authoritative write succeeds, fires the `gate_written`
    hook chain (entry-points + .qor/hooks.yaml). Hook exceptions are
    swallow-logged; never propagated. See `qor/scripts/gate_hooks.py`.
    """
    import hashlib
    sid = session_id or session.get_or_create()
    path = vga.write_artifact(phase, payload, session_id=sid)
    if phase == "audit":
        from qor.scripts import audit_history
        audit_history.append(payload, session_id=sid)
    _fire_gate_written_hook(phase, sid, path)
    return path


def _fire_gate_written_hook(phase: str, session_id: str, path: "Path") -> None:
    """Invoke the hook dispatcher after a successful gate-artifact write.

    Isolated so the authoritative write path never fails on hook errors:
    any exception surfacing from dispatch is swallowed here too.
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
    except BaseException:  # noqa: BLE001 — hooks must never break writes
        pass
