"""Phase 256: the residue closure holds, and holds honestly.

Anti-recurrence bindings over the live genome. A closure pass is the most
self-serving artifact this repository produces -- the number it moves is the
number it is judged by -- so the dispositions it recorded are pinned here rather
than trusted.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import check_shadow_threshold as cst
from qor.scripts import shadow_process as sp
from qor.scripts.publication_boundary_lint import _GH_URL_RE, _SELF_REPO

REPO = Path(__file__).resolve().parents[1]
PRIVATE_MAPPING = REPO / ".qor" / "private" / "upstream-issues.json"

# Closed with a destination or a live enforcer. Excludes the declared permanent
# skips, whose emitters keep firing by design -- that distinction is the point
# of the phase, so the test must not blur it.
#
# Phase 283 removed ("gate_skipped_prerequisite_absent",
# "instruction_hygiene_lint"). It qualified for neither set. The module has
# never existed in this repository, while /qor-substantiate Step 4.6.11 and the
# qor-guard-instructions skill both document the control as fail-closed, so the
# gate records a disclosed skip at every seal and the emitter is live -- it was
# not closed with a destination or an enforcer. Nor is it a permanent skip: the
# other declarations there are inapplicable by construction (no SQL migrations,
# no Surface column, no agent-teams host) and render as `cannot-automate:`,
# which would be false for a control that simply has not been built. It belongs
# in neither set until the module ships or the control is withdrawn, and while
# it sits in neither, the event stays honestly unaddressed.
CLOSED_SIGNATURES = {
    ("degradation", "concurrent-edit-during-audit"),
    ("degradation", "delegated-review-delivery-failure"),
    ("gate_skipped_prerequisite_absent", "intent_lock"),
    ("capability_shortfall", "qor-namespace-resolution"),
    ("hallucination", "invented-artifact-path"),
    ("regression", "details:816f0c38a2d1"),
}


def _deferred() -> list[dict]:
    return [
        e for e in sp.read_all_events()
        if e.get("addressed_reason") == "deferred_upstream"
    ]


def test_every_deferred_upstream_event_names_a_destination():
    """Deferral is closure by transfer of ownership, not by reclassification.

    Without a destination the state is a synonym for "not my problem", which is
    the failure `UpstreamClosureError` exists to prevent at the write path; this
    is the same guarantee checked against what actually landed.
    """
    events = _deferred()
    assert events, "expected the Phase 256 deferrals in the genome"

    undestined = [e["id"] for e in events if not (e.get("issue_url") or "").strip()]

    assert undestined == []


def test_deferred_upstream_destinations_are_publication_safe():
    """The destination must not republish what the boundary sweep removed.

    Checked with the lint's own regex and self-repo constant so the two controls
    cannot drift apart: a change that taught the lint a new owner would have to
    change this test too.
    """
    offenders = [
        (e["id"], e["issue_url"])
        for e in _deferred()
        for owner in _GH_URL_RE.findall(e.get("issue_url") or "")
        if owner != _SELF_REPO
    ]

    assert offenders == [], (
        f"deferred_upstream issue_url names an outside repository: {offenders}"
    )


def test_every_deferred_reference_resolves_in_the_private_mapping():
    """An anonymized destination must not become an unresolvable one.

    Skipped where the mapping is absent: `.qor/private/` is gitignored, so CI
    genuinely has no copy and asserting there would test the checkout, not the
    closure.
    """
    if not PRIVATE_MAPPING.is_file():
        pytest.skip("private upstream mapping is gitignored and absent here")

    mapping = json.loads(PRIVATE_MAPPING.read_text(encoding="utf-8"))
    referenced = {(e.get("issue_url") or "").strip() for e in _deferred()}

    unresolved = sorted(r for r in referenced if r not in mapping)

    assert unresolved == []


def test_closed_residue_signatures_do_not_reappear_unaddressed():
    """The non-permanent closures stay closed.

    A signature reappearing here means either the closure was against a live
    emitter -- the misclassification tribunal ground V-3 caught for agent-teams
    -- or the defect recurred. Both need to be loud.
    """
    open_signatures = {
        cst._signature(e) for e in sp.read_all_events() if not e.get("addressed")
    }

    reopened = sorted(CLOSED_SIGNATURES & open_signatures)

    assert reopened == []


def test_declared_permanent_skips_carry_a_substantive_justification():
    """Every declaration must survive the enforcer validator it becomes.

    The config value is written verbatim into `closure_enforcer` as a
    `cannot-automate:` string, so a declaration the validator would reject is a
    closure the repository cannot defend.
    """
    from qor.scripts.qorlogic_config import load_section
    from qor.scripts.remediate_attestation import _validate_closure_enforcer

    declared = load_section(REPO, "permanent_skips")
    assert declared, "expected the Phase 256 permanent-skip declarations"

    for key, justification in declared.items():
        _validate_closure_enforcer(f"cannot-automate: {justification}", repo_root=REPO)
