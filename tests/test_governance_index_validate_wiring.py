"""Phase 120 (GH #149): /qor-validate wires the governance-index ledger cross-check."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-validate" / "SKILL.md"


def test_validate_invokes_cross_check():
    body = SKILL.read_text(encoding="utf-8")
    assert "governance-index --cross-check-ledger" in body, (  # prose-lint: ok=prompt-contract
        "qor-validate must invoke `qor-logic governance-index --cross-check-ledger` "
        "(the #140 ledger cross-check)"
    )
