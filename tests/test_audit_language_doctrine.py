"""Phase 26 Phase 2: audit language doctrine cross-check."""
from __future__ import annotations

from pathlib import Path

import pytest


DOCTRINE = Path(__file__).resolve().parent.parent / "qor" / "references" / "doctrine-audit-report-language.md"

CANONICAL_GROUND_CLASSES = {
    "Section 4 Razor": "/qor-refactor",
    "Orphan file / Macro-arch breach": "/qor-organize",
    "Plan-text": "Governor",
    "Process-level": "/qor-remediate",
    "Code-logic defect": "/qor-debug",
}


def test_doctrine_file_exists():
    assert DOCTRINE.exists(), f"missing doctrine: {DOCTRINE}"


def test_doctrine_lists_every_ground_class():
    text = DOCTRINE.read_text(encoding="utf-8")
    for ground_class in CANONICAL_GROUND_CLASSES:
        assert ground_class in text, f"doctrine missing ground class: {ground_class}"


def test_doctrine_names_correct_skill_per_ground():
    text = DOCTRINE.read_text(encoding="utf-8")
    for ground_class, skill in CANONICAL_GROUND_CLASSES.items():
        # Each ground-class/skill pair must co-occur within the doctrine text.
        assert ground_class in text
        assert skill in text


def test_doctrine_lists_repeated_veto_pattern_event():
    text = DOCTRINE.read_text(encoding="utf-8")
    assert "repeated_veto_pattern" in text
    assert "severity: 3" in text or "severity 3" in text
    assert "/qor-remediate" in text


def test_doctrine_cites_delegation_table():
    text = DOCTRINE.read_text(encoding="utf-8")
    assert "qor/gates/delegation-table.md" in text, (
        "doctrine must cite delegation-table as upstream authority"
    )


def test_every_named_skill_exists():
    """For every /qor-* skill referenced in the doctrine, verify it exists.

    Excludes path fragments (e.g. ``.../qor-audit-templates.md``) which are
    not skill invocations but file references.
    """
    text = DOCTRINE.read_text(encoding="utf-8")
    import re
    # Match /qor-<name> but NOT when the name is followed by .md (filepath).
    skill_re = re.compile(r"/qor-[a-z-]+(?![\w.-]*\.md)")
    skills = set(skill_re.findall(text))
    skills_root = DOCTRINE.parent.parent / "skills"
    extant: set[str] = set()
    for skill_md in skills_root.rglob("SKILL.md"):
        extant.add(f"/{skill_md.parent.name}")
    for loose in skills_root.rglob("*.md"):
        if loose.name != "SKILL.md" and "/references/" not in loose.as_posix():
            extant.add(f"/{loose.stem}")
    for s in skills:
        assert s in extant, f"doctrine references non-existent skill: {s}"
