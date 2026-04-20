"""Tests for doctrine-context-discipline.md (Phase 39 B1)."""
from __future__ import annotations

import pathlib


_DOCTRINE = pathlib.Path("qor/references/doctrine-context-discipline.md")
_GOVERNANCE = pathlib.Path("qor/references/doctrine-governance-enforcement.md")


def test_doctrine_file_exists():
    assert _DOCTRINE.is_file()


def test_doctrine_has_five_sections():
    prose = _DOCTRINE.read_text(encoding="utf-8")
    for header in (
        "## 1. The three mechanisms",
        "## 2. Persona as context-prioritization scaffold",
        "## 3. Stance directive discipline",
        "## 4. Subagent invocation rule",
        "## 5. Verification protocol",
    ):
        assert header in prose, f"missing section: {header}"


def test_doctrine_governance_xref():
    prose = _GOVERNANCE.read_text(encoding="utf-8")
    assert "## 11. Context Discipline" in prose
    assert "doctrine-context-discipline.md" in prose
