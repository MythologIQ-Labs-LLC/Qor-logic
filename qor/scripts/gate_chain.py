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
    """
    sid = session_id or session.get_or_create()
    return vga.write_artifact(phase, payload, session_id=sid)
