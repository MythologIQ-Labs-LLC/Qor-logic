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


def _count_session_overrides(session_id: str, *, log_path: Path | None = None) -> int:
    """Count gate_override events with the given session_id in the shadow log."""
    path = log_path or _shadow_log_path()
    if not path.exists():
        return 0
    count = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event_type") != "gate_override":
            continue
        if event.get("session_id") != session_id:
            continue
        count += 1
    return count


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
