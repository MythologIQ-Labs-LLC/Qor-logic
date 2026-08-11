"""Classify execution-continuity evidence into a routed outcome (Phase 216).

`classify()` is a pure function over already-parsed inputs. It performs no I/O,
no network access, and no upstream-schema validation -- parsing upstream
artifacts here would embed their shape and duplicate the contract by another
route (GH #285 ownership boundary).

Revision comparison is exact string equality, never git ancestry. `intent_lock`
deliberately accepts an ancestor commit so an implement commit may advance HEAD
between capture and verify (Phase 43). A verification receipt must not inherit
that tolerance: an ancestor-revision receipt is the stale acceptance GH #285
forbids. The two mechanisms answer different questions and stay separate.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Authority a continuation may never acquire, regardless of checkpoint validity.
FORBIDDEN_AUTHORITY = frozenset({
    "merge", "release", "deployment", "credential", "policy_mutation",
})

#: The only receipt kind that constitutes independent verification. Provider
#: prose, status badges, and session-completion messages are self-report.
RECEIPT_KIND = "receipt"


@dataclass(frozen=True)
class Evidence:
    """Continuity evidence, already parsed into Qor-owned shape."""

    current_revision: str
    interruption: str | None = None
    checkpoint: dict | None = None
    receipt: dict | None = None
    writer_state: str = "clear"
    actor_class: str = "successor"
    requested_authority: str | None = None
    provider: str | None = None


@dataclass(frozen=True)
class Decision:
    """A typed outcome plus the routing directive it implies."""

    outcome: str
    reason: str
    directive: str


def _authority_rule(evidence: Evidence) -> Decision | None:
    if evidence.requested_authority in FORBIDDEN_AUTHORITY:
        return Decision("rejected", "authority-expansion", "refuse")
    return None


def _writer_rule(evidence: Evidence) -> Decision | None:
    if evidence.writer_state == "conflict":
        return Decision("rejected", "live-writer-conflict", "refuse")
    return None


def _environment_rule(evidence: Evidence) -> Decision | None:
    """Environment failure is not product failure and not fabricated success."""
    if evidence.interruption == "environment_outage":
        return Decision(
            "inconclusive", "environment-unavailable", "repair-evidence-environment")
    return None


def _receipt_rule(evidence: Evidence) -> Decision | None:
    receipt = evidence.receipt
    if receipt is None:
        return None
    if receipt.get("kind") != RECEIPT_KIND:
        return Decision("rejected", "self-report-insufficient", "refuse")
    if receipt.get("revision") != evidence.current_revision:
        return Decision("rejected", "receipt-stale", "re-verify")
    return Decision("verified", "receipt-exact", "proceed")


def _checkpoint_rule(evidence: Evidence) -> Decision | None:
    if evidence.interruption != "provider_exhaustion":
        return None
    checkpoint = evidence.checkpoint
    if checkpoint is None:
        return Decision("rejected", "checkpoint-absent", "refuse")
    if not checkpoint.get("valid"):
        return Decision("rejected", "checkpoint-malformed", "refuse")
    if checkpoint.get("target_revision") != evidence.current_revision:
        return Decision("rejected", "revision-mismatch", "refuse")
    return Decision("verified", "checkpoint-resumable", "resume-with-successor")


#: Order is the specification. Fail-closed conditions precede acceptance, so a
#: valid checkpoint can never outrank a live-writer conflict or an authority
#: request, and an environment outage is classified before any evidence is
#: judged on its merits.
_RULES = (
    _authority_rule,
    _writer_rule,
    _environment_rule,
    _receipt_rule,
    _checkpoint_rule,
)


def classify(evidence: Evidence) -> Decision:
    """Return the routed outcome for one bundle of continuity evidence.

    Provider identity is carried on `Evidence` for the audit trail and is never
    read here; two bundles differing only in provider return equal decisions.
    """
    for rule in _RULES:
        decision = rule(evidence)
        if decision is not None:
            return decision
    return Decision("rejected", "evidence-absent", "refuse")
