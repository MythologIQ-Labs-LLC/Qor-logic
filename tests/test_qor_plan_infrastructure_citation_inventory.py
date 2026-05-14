"""Phase 72 P1: qor-plan Step 2 Infrastructure Citation Inventory."""
from pathlib import Path

import pytest

SKILL = Path("qor/skills/sdlc/qor-plan/SKILL.md")


def _step_2_region(text: str) -> str:
    start = text.index("### Step 2: Research Existing Code")
    end = text.index("### Step 3: Create Plan File", start)
    return text[start:end]


def _section_text(region: str, heading: str) -> str:
    if heading not in region:
        raise AssertionError(f"missing heading {heading!r} in Step 2 region")
    start = region.index(heading)
    return region[start:]


def test_step_2_names_citation_inventory():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_2_region(text)
    body = _section_text(region, "Infrastructure Citation Inventory")
    assert "sealed infrastructure" in body.lower(), (
        "Infrastructure Citation Inventory must describe sealed-infrastructure scope"
    )
    citation_kinds = ["migration", "function signature", "file:line", "schema", "env"]
    hits = sum(1 for k in citation_kinds if k in body.lower())
    assert hits >= 3, (
        f"Inventory section must enumerate sealed-infrastructure citation kinds; "
        f"found only {hits}/{len(citation_kinds)} of {citation_kinds}"
    )


def test_step_2_requires_grep_evidence():
    text = SKILL.read_text(encoding="utf-8")
    body = _section_text(_step_2_region(text), "Infrastructure Citation Inventory")
    assert "grep-evidence" in body.lower(), (
        "section must require grep-evidence statements"
    )
    assert "git show" in body and "grep" in body, (
        "section must show the canonical evidence form 'git show ... grep ...'"
    )


def test_step_2_routes_unverified_to_open_questions():
    text = SKILL.read_text(encoding="utf-8")
    body = _section_text(_step_2_region(text), "Infrastructure Citation Inventory")
    assert "Open Questions" in body, (
        "unverified citations must be routed to Open Questions before /qor-audit"
    )
    assert "/qor-audit" in body, "must name /qor-audit as the gate boundary"
