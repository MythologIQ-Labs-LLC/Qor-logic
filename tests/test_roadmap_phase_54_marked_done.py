"""Phase 54 roadmap close test."""
from __future__ import annotations

from pathlib import Path

ROADMAP = Path(__file__).resolve().parent.parent / "docs" / "roadmap-prompt-compiler.md"


def test_roadmap_phase_54_marked_with_v0_54_0():
    body = ROADMAP.read_text(encoding="utf-8")
    line = next(l for l in body.splitlines() if l.startswith("| 54 "))
    assert "DONE" in line
    assert "v0.54.0" in line


def test_roadmap_marked_complete_after_phase_54():
    body = ROADMAP.read_text(encoding="utf-8")
    assert "Roadmap COMPLETE" in body
    assert "all 5 sub-phases" in body.lower() or "all 5 sub-phases of GH #39 delivered" in body


def test_all_five_phases_now_marked_done():
    body = ROADMAP.read_text(encoding="utf-8")
    for phase in ("50", "51", "52", "53", "54"):
        line = next(l for l in body.splitlines() if l.startswith(f"| {phase} "))
        assert "DONE" in line, f"phase {phase} still not marked DONE"
