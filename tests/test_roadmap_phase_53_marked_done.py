"""Phase 53 roadmap status update."""
from __future__ import annotations

from pathlib import Path

ROADMAP = Path(__file__).resolve().parent.parent / "docs" / "roadmap-prompt-compiler.md"


def test_roadmap_phase_53_marked_with_v0_53_0():
    body = ROADMAP.read_text(encoding="utf-8")
    line = next(l for l in body.splitlines() if l.startswith("| 53 "))
    assert "DONE" in line
    assert "v0.53.0" in line
