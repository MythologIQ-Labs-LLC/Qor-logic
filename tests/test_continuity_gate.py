"""Phase 216 (GH #285 Phase B): the continuity classifier.

Every test invokes `classify()` and asserts on the returned decision. The
classifier is a pure function over already-parsed inputs; it never reads the
upstream schema, so nothing here validates upstream conformance.
"""
from __future__ import annotations

import pytest

from qor.scripts import continuity_gate as cg

HEAD = "c" * 40
OLDER = "d" * 40


def _evidence(**over) -> cg.Evidence:
    base = dict(current_revision=HEAD)
    base.update(over)
    return cg.Evidence(**base)


def _checkpoint(valid=True, target=HEAD) -> dict:
    return {"valid": valid, "target_revision": target}


def test_valid_checkpoint_under_exhaustion_is_resumable():
    """Provider exhaustion is not product failure and not human escalation."""
    d = cg.classify(_evidence(
        interruption="provider_exhaustion", checkpoint=_checkpoint()))

    assert d.outcome == "verified", d
    assert d.directive == "resume-with-successor"
    assert "escalate" not in d.directive


@pytest.mark.parametrize("checkpoint,code", [
    (None, "checkpoint-absent"),
    ({"valid": False, "target_revision": HEAD}, "checkpoint-malformed"),
    ({"valid": True, "target_revision": OLDER}, "revision-mismatch"),
])
def test_missing_or_malformed_checkpoint_fails_closed(checkpoint, code):
    """Absence, malformation, and revision drift each fail closed distinctly."""
    d = cg.classify(_evidence(
        interruption="provider_exhaustion", checkpoint=checkpoint))

    assert d.outcome == "rejected", d
    assert d.reason == code


def test_live_writer_and_claim_conflict_rejected():
    """A successor may not edit while a live writer holds the claim."""
    d = cg.classify(_evidence(
        interruption="provider_exhaustion",
        checkpoint=_checkpoint(),
        writer_state="conflict"))

    assert d.outcome == "rejected"
    assert d.reason == "live-writer-conflict"


def test_revision_mismatch_prevents_continuation():
    """A checkpoint bound to another revision cannot continue this one."""
    d = cg.classify(_evidence(
        interruption="provider_exhaustion", checkpoint=_checkpoint(target=OLDER)))

    assert d.outcome == "rejected"
    assert d.reason == "revision-mismatch"


def test_receipt_accepted_only_for_exact_revision():
    """LD-1 regression: exact equality, never git ancestry.

    `intent_lock` passes when the captured commit is an ancestor of HEAD, by
    design since Phase 43. A receipt must not inherit that tolerance -- an
    ancestor-revision receipt is precisely the stale acceptance GH #285
    forbids. This is the single assertion proving the two mechanisms stayed
    separate.
    """
    exact = cg.classify(_evidence(receipt={"revision": HEAD, "kind": "receipt"}))
    assert exact.outcome == "verified"
    assert exact.reason == "receipt-exact"

    ancestor = cg.classify(_evidence(receipt={"revision": OLDER, "kind": "receipt"}))
    assert ancestor.outcome == "rejected", (
        "an ancestor-revision receipt must be rejected; accepting it would mean "
        "the classifier inherited intent_lock's ancestry semantics"
    )


def test_receipt_goes_stale_after_head_movement():
    """A receipt accepted at one revision does not survive the head advancing."""
    receipt = {"revision": HEAD, "kind": "receipt"}
    assert cg.classify(_evidence(receipt=receipt)).outcome == "verified"

    moved = cg.classify(cg.Evidence(current_revision="e" * 40, receipt=receipt))
    assert moved.outcome == "rejected"
    assert moved.reason == "receipt-stale"


def test_environment_outage_yields_inconclusive():
    """Environment failure is neither product failure nor fabricated success."""
    d = cg.classify(_evidence(
        interruption="environment_outage", checkpoint=_checkpoint()))

    assert d.outcome == "inconclusive", d
    assert d.outcome not in ("verified", "rejected")
    assert d.directive == "repair-evidence-environment"


@pytest.mark.parametrize("kind", ["self_report", "status_badge", "session_message"])
def test_self_report_cannot_satisfy_verification(kind):
    """Provider prose is not a receipt, however confident it sounds."""
    d = cg.classify(_evidence(receipt={"revision": HEAD, "kind": kind}))

    assert d.outcome == "rejected", d
    assert d.reason == "self-report-insufficient"
    assert d.outcome != "verified"


@pytest.mark.parametrize("authority", [
    "merge", "release", "deployment", "credential", "policy_mutation"])
def test_worker_authority_cannot_expand(authority):
    """A valid checkpoint buys continuation, never new authority."""
    d = cg.classify(_evidence(
        interruption="provider_exhaustion",
        checkpoint=_checkpoint(),
        requested_authority=authority))

    assert d.outcome == "rejected", d
    assert d.reason == "authority-expansion"


def test_outcome_is_independent_of_provider_identity():
    """LD-6: vendor-neutrality as outcome-independence, not name absence."""
    a = cg.classify(_evidence(
        interruption="provider_exhaustion", checkpoint=_checkpoint(),
        provider="provider-alpha"))
    b = cg.classify(_evidence(
        interruption="provider_exhaustion", checkpoint=_checkpoint(),
        provider="provider-beta"))

    assert a == b, "outcome must not depend on which provider produced the evidence"
