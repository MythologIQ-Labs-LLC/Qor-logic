"""Phase 71 (#52): qor-implement Step 8.5 Documentation Sync.

Closes the procedural failure where documentation updates are
backloaded to /qor-substantiate (Steps 4.7, 6, 6.5, 4.6.6) by which
time the implementing agent has lost the context to write accurate
docs. Step 8.5 between Step 8 (Post-Build Cleanup) and Step 9
(Complexity Self-Check) keeps documentation authoring in the phase
where context is fullest.
"""
from __future__ import annotations

from pathlib import Path

SKILL_PATH = Path("qor/skills/sdlc/qor-implement/SKILL.md")


def _text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _step_8_5_region(text: str) -> str:
    """Return the body of Step 8.5 up to Step 9."""
    start = text.find("### Step 8.5:")
    assert start >= 0, "Step 8.5 heading missing"
    end = text.find("### Step 9:", start + 10)
    return text[start:end] if end > 0 else text[start:]


def test_step_8_5_documentation_sync_exists():
    body = _text()
    start = body.find("### Step 8.5:")
    assert start >= 0, (
        "qor-implement SKILL.md must include `### Step 8.5:` "
        "(Phase 71; GH #52)"
    )
    assert "Documentation Sync" in body[start:start + 100], (
        "Step 8.5 heading must include 'Documentation Sync' literal"
    )


def test_step_8_5_names_four_doc_surfaces():
    """Step 8.5 must enumerate the four documentation surfaces from Issue #52."""
    block = _step_8_5_region(_text())
    surfaces = {
        "ARCHITECTURE_PLAN.md": False,
        "architecture docs / architecture.md": "architecture" in block.lower(),
        "operations docs / operations.md": "operations" in block.lower(),
        "schema docs / migrations": "schema" in block.lower() or "migration" in block.lower(),
    }
    assert "ARCHITECTURE_PLAN.md" in block or "ARCHITECTURE_PLAN" in block, (
        "Step 8.5 must reference ARCHITECTURE_PLAN.md file tree"
    )
    assert "architecture" in block.lower(), (
        "Step 8.5 must reference architecture docs"
    )
    assert "operations" in block.lower(), (
        "Step 8.5 must reference operations docs"
    )
    assert "schema" in block.lower() or "migration" in block.lower(), (
        "Step 8.5 must reference schema docs / migrations"
    )


def test_step_8_5_doc_tier_conditional_semantics():
    """Step 8.5 must distinguish minimal (skip/WARN) from standard/system (required)."""
    block = _step_8_5_region(_text())
    assert "doc_tier" in block, (
        "Step 8.5 must reference the doc_tier field"
    )
    # Must name at least one of the tier values + a conditional semantic
    has_minimal = "minimal" in block
    has_standard_or_system = "standard" in block or "system" in block
    has_warn_or_skip = (
        "warn" in block.lower() or "skip" in block.lower()
        or "WARN" in block or "skipped" in block.lower()
    )
    assert has_minimal and has_standard_or_system and has_warn_or_skip, (
        "Step 8.5 must distinguish minimal (skip/WARN) from standard/system "
        "(required updates)"
    )


def test_step_8_5_precedes_step_9_complexity_self_check():
    """Step 8.5 must be placed between Step 8 and Step 9 per Issue #52 spec."""
    body = _text()
    pos_8 = body.find("### Step 8:")
    pos_8_5 = body.find("### Step 8.5:")
    pos_9 = body.find("### Step 9:")
    assert pos_8 >= 0, "Step 8 heading missing"
    assert pos_8_5 >= 0, "Step 8.5 heading missing"
    assert pos_9 >= 0, "Step 9 heading missing"
    assert pos_8 < pos_8_5 < pos_9, (
        f"Step 8.5 (offset {pos_8_5}) must sit between Step 8 ({pos_8}) "
        f"and Step 9 ({pos_9}) per Issue #52 spec"
    )
