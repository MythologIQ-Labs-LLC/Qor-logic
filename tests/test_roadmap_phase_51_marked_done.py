"""Phase 51 roadmap status update."""
from __future__ import annotations

from pathlib import Path

ROADMAP = Path(__file__).resolve().parent.parent / "docs" / "roadmap-prompt-compiler.md"
DOCTRINE = Path(__file__).resolve().parent.parent / "qor" / "references" / "doctrine-prompt-compilation.md"


def test_roadmap_phase_51_marked_with_v0_51_0():
    body = ROADMAP.read_text(encoding="utf-8")
    line = next(l for l in body.splitlines() if l.startswith("| 51 "))
    assert "DONE" in line
    assert "v0.51.0" in line


def test_doctrine_documents_governance_gate_and_violation():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert "GovernanceGate" in body
    assert "GovernanceViolation" in body
    assert "GovernanceDecision" in body
