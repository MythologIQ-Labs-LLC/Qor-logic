"""Phase 52 roadmap status update."""
from __future__ import annotations

from pathlib import Path

ROADMAP = Path(__file__).resolve().parent.parent / "docs" / "roadmap-prompt-compiler.md"


def test_roadmap_phase_52_marked_with_v0_52_0():
    body = ROADMAP.read_text(encoding="utf-8")
    line = next(l for l in body.splitlines() if l.startswith("| 52 "))
    assert "DONE" in line
    assert "v0.52.0" in line
