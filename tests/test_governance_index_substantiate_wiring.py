"""Phase 120 (GH #149): /qor-substantiate wires the governance-index enforce gate.

Prompt-contract tests: read the production SKILL.md and assert the enforcement
invocation + fail-closed semantics + the Phase 75 prerequisite-table row.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def test_substantiate_invokes_governance_index_enforce():
    body = SKILL.read_text(encoding="utf-8")
    idx = body.find("governance-index --advance-last-reviewed")
    assert idx != -1, "substantiate must invoke `governance-index --advance-last-reviewed ... --enforce`"  # prose-lint: ok=prompt-contract
    window = body[idx: idx + 200]
    assert "--enforce" in window, "the index gate must run in --enforce (fail-closed) mode"
    assert "|| ABORT" in window, "the governance-index enforce gate must be fail-closed (|| ABORT), not WARN"


def test_substantiate_governance_index_has_prerequisite_row():
    body = SKILL.read_text(encoding="utf-8")
    assert "module:qor.scripts.governance_index" in body, (  # prose-lint: ok=prompt-contract
        "Step Prerequisites table must declare module:qor.scripts.governance_index "
        "(Phase 75 disclosed-skip contract for absent index)"
    )
