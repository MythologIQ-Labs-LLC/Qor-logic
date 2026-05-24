"""Phase 99: /qor-audit Step 3 Runtime Contract Walk wiring tests (GH #108 V2)."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QOR_AUDIT_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
REFERENCE = REPO_ROOT / "qor" / "references" / "audit-runtime-contract-walk.md"

WIRING_ANCHOR = "**Phase 99 wiring (GH #108 V2 — Runtime Contract Walk)**"
WALK_INVOCATION = "python -m qor.scripts.runtime_contract_walk --plan"
WARN_WRAP = "|| true"
REFERENCE_POINTER = "qor/references/audit-runtime-contract-walk.md"


def test_step_3_infrastructure_alignment_cites_runtime_contract_walk():
    text = QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    assert WIRING_ANCHOR in text, f"Phase 99 wiring anchor missing from {QOR_AUDIT_SKILL}"
    assert WALK_INVOCATION in text, "Walk invocation must appear in Step 3"


def test_step_3_runtime_contract_walk_warns_only_in_v2_ramp():
    """Asserts the V2 ramp uses `|| true` so a failing walk doesn't ABORT.

    A future V2-of-V2 phase will remove the wrap once operator evidence
    on V1 false-positive rate is in. Until then, the WARN-only ramp is
    binding: a hard VETO at this surface would block legitimate work
    while the walk's heuristics are unproven in production.
    """
    text = QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    wiring_pos = text.find(WIRING_ANCHOR)
    assert wiring_pos != -1
    invocation_pos = text.find(WALK_INVOCATION, wiring_pos)
    assert invocation_pos != -1
    # The `|| true` must be on the same code-fence block as the invocation.
    window = text[invocation_pos:invocation_pos + 200]
    assert WARN_WRAP in window, (
        "Phase 99 V2 ramp must wrap the walk invocation in `|| true`; got "
        f"window:\n{window}"
    )


def test_audit_skill_references_progressive_disclosure_reference_file():
    text = QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    assert REFERENCE_POINTER in text, (
        f"qor-audit SKILL.md must cite {REFERENCE_POINTER} (progressive disclosure)"
    )
    assert REFERENCE.exists(), (
        f"Reference file {REFERENCE} must exist at HEAD"
    )
