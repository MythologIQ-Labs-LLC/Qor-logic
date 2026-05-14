#!/usr/bin/env python3
"""Runtime helpers for the qor-audit skill (Phase 7 wiring).

Used by qor-audit to:
  - check that a prior plan artifact exists before auditing
  - decide whether to run in adversarial mode (claude-code + codex-plugin)
  - log capability_shortfall when adversarial isn't available
  - short-circuit unchanged-plan re-invocation (Phase 67; GH #45)
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import gate_chain
from qor.scripts import qor_platform as qplat
from qor.scripts import session
from qor.scripts import shadow_process

CURRENT_PHASE = "audit"


@dataclass(frozen=True)
class ShortCircuitResult:
    """Outcome of the unchanged-plan short-circuit check.

    Phase 67 (GH #45): when ``should_skip=True``, the operator amended
    nothing since the prior audit produced ``prior_verdict``; the skill
    surfaces the prior verdict instead of consuming a new audit cycle.
    """
    should_skip: bool
    prior_verdict: str | None = None
    plan_content_hash: str | None = None


def check_unchanged_plan_short_circuit(
    plan_path: Path,
    session_id: str,
) -> ShortCircuitResult:
    """Return a ShortCircuitResult indicating whether to skip re-audit.

    Reads the current plan file, computes its SHA-256, and compares against
    the prior audit gate artifact's ``target_content_hash`` field. When the
    hashes match, the plan is unchanged and the prior verdict carries
    forward.

    Graceful fallbacks (all return ``should_skip=False``):
      - plan file missing on disk
      - no prior audit.json for the session
      - prior artifact lacks ``target_content_hash`` (pre-Phase-67 audits)
    """
    try:
        plan_bytes = Path(plan_path).read_bytes()
    except (FileNotFoundError, IsADirectoryError):
        return ShortCircuitResult(should_skip=False)
    plan_hash = hashlib.sha256(plan_bytes).hexdigest()
    try:
        prior = gate_chain.read_phase_artifact("audit", session_id=session_id)
    except (FileNotFoundError, ValueError, KeyError):
        return ShortCircuitResult(should_skip=False, plan_content_hash=plan_hash)
    if not prior:
        return ShortCircuitResult(should_skip=False, plan_content_hash=plan_hash)
    prior_hash = prior.get("target_content_hash")
    if prior_hash and prior_hash == plan_hash:
        return ShortCircuitResult(
            should_skip=True,
            prior_verdict=prior.get("verdict"),
            plan_content_hash=plan_hash,
        )
    return ShortCircuitResult(should_skip=False, plan_content_hash=plan_hash)


def check_prior_artifact(session_id: str | None = None) -> gate_chain.GateResult:
    """Delegate to gate_chain. Returns the prior-phase (plan) GateResult."""
    return gate_chain.check_prior_artifact(CURRENT_PHASE, session_id=session_id)


def should_run_adversarial_mode() -> bool:
    """True only when host=claude-code AND codex-plugin is declared available.

    codex-plugin is a Claude Code-specific feature (per pre-Phase-7 dialogue);
    a declaration of codex-plugin=true on any other host is operator error
    and is ignored.
    """
    state = qplat.current()
    if state is None:
        return False
    host = state.get("detected", {}).get("host")
    if host != "claude-code":
        return False
    return qplat.is_available("codex-plugin")


def emit_capability_shortfall(capability: str, session_id: str) -> str:
    """Append a sev-2 capability_shortfall event to the shadow log."""
    event = {
        "ts": shadow_process.now_iso(),
        "skill": "qor-audit",
        "session_id": session_id,
        "event_type": "capability_shortfall",
        "severity": 2,
        "details": {
            "capability": capability,
            "reason": (
                "qor-audit is running in solo mode because the requested "
                f"capability '{capability}' is not available on this host."
            ),
        },
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    return shadow_process.append_event(event, attribution="UPSTREAM")


def emit_gate_override(reason: str, session_id: str) -> str:
    """Convenience: emit gate_override (sev 1) for a missing/invalid plan artifact."""
    return gate_chain.emit_gate_override(
        current_phase=CURRENT_PHASE,
        prior_phase_name="plan",
        reason=reason,
        session_id=session_id,
    )


def session_id() -> str:
    """Resolve current session id (creates marker if absent)."""
    return session.get_or_create()
