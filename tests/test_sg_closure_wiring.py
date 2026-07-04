"""Phase 166: wiring lock for the SG closure-enforcement surfaces (GH #249)."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_AUDIT = _REPO / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
_REMEDIATE = _REPO / "qor" / "skills" / "sdlc" / "qor-remediate" / "SKILL.md"


def test_audit_ladder_and_remediate_document_closure_enforcer():
    audit = _AUDIT.read_text(encoding="utf-8")  # prose-lint: ok=wiring regression lock; skill prose has no invokable unit
    remediate = _REMEDIATE.read_text(encoding="utf-8")  # prose-lint: ok=wiring regression lock; skill prose has no invokable unit
    step06 = audit[audit.index("### Step 0.6"):audit.index("### Step 1:")]
    assert "sg_closure_lint || true" in step06, (
        "audit Step 0.6 ladder must run the WARN-only sg_closure_lint"
    )
    assert "closure_enforcer=" in audit, (  # prose-lint: ok=wiring regression lock; skill prose has no invokable unit
        "audit Step 4.2 mark_addressed example must pass closure_enforcer"
    )
    assert "closure_enforcer" in remediate and "cannot-automate:" in remediate, (
        "remediate skill must document the closure_enforcer contract and its "
        "cannot-automate escape form"
    )
