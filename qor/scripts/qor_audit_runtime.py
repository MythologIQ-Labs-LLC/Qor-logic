#!/usr/bin/env python3
"""Runtime helpers for the qor-audit skill (Phase 7 wiring).

Used by qor-audit to:
  - check that a prior plan artifact exists before auditing
  - decide whether to run in adversarial mode (claude-code + codex-plugin)
  - log capability_shortfall when adversarial isn't available
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_chain  # noqa: E402
import qor_platform as qplat  # noqa: E402
import session  # noqa: E402
import shadow_process  # noqa: E402

CURRENT_PHASE = "audit"


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
    return shadow_process.append_event(event)


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
