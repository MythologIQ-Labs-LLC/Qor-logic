"""Operator-declared permanent skips (Phase 256).

Some gates skip on every cycle because they name a property of the repository
that no enforcer will ever satisfy: no SQL migrations for the Data-API scan, no
`Surface` column for the feature-index lint, no host capability for agent-teams.
Their Phase 75 disclosed-skip events accrue as unaddressed debt forever, so
closing them one pass at a time is a treadmill.

An operator declares such a property in `.qorlogic/config.json`:

    "permanent_skips": {"<gate or capability>": "<justification, >= 50 chars>"}

and the event is stamped closed as it is written. The event still reaches the
log -- the disclosed-skip exists so a skipped gate stays visible, and only its
debt accrual changes.

Scope is bounded to event types that report an *absence*. A defect keeps the
attested two-stage path through `remediate_mark_addressed.mark_addressed`, which
refuses to flip anything without a PASS review artifact; emit-time closure has
no such attestation, so it must not be able to reach a defect.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from qor.scripts import qorlogic_config

_CLOSABLE_ON_EMISSION = frozenset({
    "gate_skipped_prerequisite_absent",
    "capability_shortfall",
})

# Mirrors remediate_attestation._validate_closure_enforcer's `cannot-automate:`
# form, whose justification floor is the same. The declaration becomes that
# enforcer verbatim, so the two must agree.
_MIN_JUSTIFICATION = 50

_ENFORCER_PREFIX = "cannot-automate: "


class PermanentSkipDeclarationError(ValueError):
    """A declaration whose justification is too short to be one.

    Raised rather than ignored: a typo that silently restored the treadmill
    would teach nobody, which is the failure mode the declaration exists to
    remove.
    """


def declared_justification(event: dict, repo_root: Path | None = None) -> str | None:
    """Return the declared justification covering this event, else None."""
    if event.get("event_type") not in _CLOSABLE_ON_EMISSION:
        return None
    details = event.get("details") or {}
    key = details.get("gate") or details.get("capability")
    if not key:
        return None
    declared = qorlogic_config.load_section(repo_root, "permanent_skips")
    justification = declared.get(key)
    if justification is None:
        return None
    if not isinstance(justification, str) or len(justification.strip()) < _MIN_JUSTIFICATION:
        raise PermanentSkipDeclarationError(
            f"permanent_skips[{key!r}] justification must be a string of at least "
            f"{_MIN_JUSTIFICATION} characters stating why no enforcer will ever "
            "satisfy this gate here"
        )
    return justification.strip()


def apply(event: dict, repo_root: Path | None = None) -> dict:
    """Stamp `event` closed when a declaration covers it; else return it as-is."""
    justification = declared_justification(event, repo_root)
    if justification is None:
        return event
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        **event,
        "addressed": True,
        "addressed_pending": True,
        "addressed_reason": "remediated",
        "addressed_ts": now,
        "closure_enforcer": _ENFORCER_PREFIX + justification,
    }
