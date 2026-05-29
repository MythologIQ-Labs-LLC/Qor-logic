"""Phase 110 (#137): /qor-plan Step 5 cascade-discipline checklist bullet.

Invokes a parser over the qor-plan SKILL.md Step 5 checklist and asserts a
bullet covers caller (cross-file) + persistence enumeration and cites
SG-AffectedFilesContract-A. Fails if the bullet is absent.
"""
from __future__ import annotations

import re
from pathlib import Path

_SKILL = Path(__file__).resolve().parent.parent / "qor" / "skills" / "sdlc" / "qor-plan" / "SKILL.md"


def _checklist_bullets(text: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"^- \[ \]\s+(.*)$", text, re.MULTILINE)]


def test_step5_has_cascade_discipline_bullet():
    bullets = _checklist_bullets(_SKILL.read_text(encoding="utf-8"))
    matches = [
        b
        for b in bullets
        if "caller" in b.lower()
        and "persistence" in b.lower()
        and "SG-AffectedFilesContract-A" in b
    ]
    assert matches, "Step 5 must carry a cascade-discipline bullet citing SG-AffectedFilesContract-A"
