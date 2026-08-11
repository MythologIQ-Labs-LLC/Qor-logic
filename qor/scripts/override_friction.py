"""Override-friction escalator (Phase 54).

Counts gate-override events per session; once the threshold is reached,
emit_gate_override raises ``OverrideFrictionRequired`` unless the caller
supplies a written justification (>=50 chars). Maps to OWASP LLM Top 10
LLM08 (Excessive Agency) strengthening and EU AI Act Art. 14 oversight.

Symmetric with ``qor.scripts.cycle_count_escalator``: same threshold (3),
same per-session scope, same override-discipline pattern.

Per ``qor/references/doctrine-ai-rmf.md`` §MANAGE-1.1 and
``qor/references/doctrine-governance-enforcement.md`` §11.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from qor import workdir

DEFAULT_THRESHOLD = 3
MIN_JUSTIFICATION_LEN = 50


class OverrideFrictionRequired(Exception):
    """Raised when threshold is reached and no justification supplied."""


@dataclass(frozen=True)
class OverrideFrictionResult:
    threshold_reached: bool
    count: int
    threshold: int


def _shadow_log_path() -> Path:
    return workdir.shadow_log()


def _iter_override_events(*, log_path: Path | None = None):
    """Yield every gate_override event in the shadow log.

    Shared by both axes so the per-session and per-gate counts can never
    disagree about what an override is -- two parsers would be the same
    one-of-several-entry-points defect this module is being extended to fix.
    """
    path = log_path or _shadow_log_path()
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event_type") == "gate_override":
            yield event


def _count_session_overrides(session_id: str, *, log_path: Path | None = None) -> int:
    """Count gate_override events with the given session_id in the shadow log."""
    return sum(1 for e in _iter_override_events(log_path=log_path)
               if e.get("session_id") == session_id)


@dataclass(frozen=True)
class GateRecurrenceResult:
    """Cross-session count for one gate.

    The per-session counter cannot see this axis: every phase rotates its
    session, so a per-phase-recurring override resets it each time. Four
    identical overrides was the observed shape (GH #324) and the one most worth
    seeing -- one override is judgment, four is a routine.
    """

    gate: str
    count: int
    threshold: int
    threshold_reached: bool


def _count_gate_overrides(gate: str, *, log_path: Path | None = None) -> int:
    """Count gate_override events naming this gate, across all sessions."""
    count = 0
    for event in _iter_override_events(log_path=log_path):
        if (event.get("details") or {}).get("gate") == gate:
            count += 1
    return count


def gate_recurrence(
    gate: str,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    log_path: Path | None = None,
) -> GateRecurrenceResult:
    """Return the cross-session recurrence state for one gate.

    Threshold reuses DEFAULT_THRESHOLD: same number, different axis. Checked
    against recorded history rather than chosen in the abstract -- at 3 this
    fires one phase before a human noticed the pattern by reading the log; at 2
    it fires on a second occurrence, which is common enough to be the alarm
    fatigue Phase 217 was sealed to remove.
    """
    count = _count_gate_overrides(gate, log_path=log_path)
    return GateRecurrenceResult(
        gate=gate, count=count, threshold=threshold,
        threshold_reached=count >= threshold,
    )


def check(
    session_id: str,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    log_path: Path | None = None,
) -> OverrideFrictionResult:
    """Return the current friction state for the session."""
    count = _count_session_overrides(session_id, log_path=log_path)
    return OverrideFrictionResult(
        threshold_reached=count >= threshold,
        count=count,
        threshold=threshold,
    )


def record_with_justification(event: dict, justification: str) -> dict:
    """Attach a justification to an override event payload.

    Raises ``ValueError`` if justification is shorter than ``MIN_JUSTIFICATION_LEN``.
    """
    if not isinstance(justification, str):
        raise ValueError("justification must be a string")
    if len(justification.strip()) < MIN_JUSTIFICATION_LEN:
        raise ValueError(
            f"justification must be at least {MIN_JUSTIFICATION_LEN} chars; "
            f"got {len(justification.strip())} after strip"
        )
    return {**event, "justification": justification}
