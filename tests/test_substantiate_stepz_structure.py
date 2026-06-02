"""Phase 136: qor-substantiate Step 4.5 / Step Z structural correctness.

The pre-existing defect: the entire `### Step Z` gate-write body (including
`session.rotate()`) was pasted INSIDE the Step 4.5 "Skill File Integrity Check"
required-sections list. These tests pin the corrected structure by comparing
character offsets, so a regression that re-tangles the block into Step 4.5 or
moves `session.rotate()` early (which would corrupt SESSION_ID mid-seal) flips
the comparisons and fails.
"""
from __future__ import annotations

from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _region(text: str, start_marker: str, end_marker: str) -> str:
    i = text.index(start_marker)
    j = text.index(end_marker, i + len(start_marker))
    return text[i:j]


def test_step_4_5_has_no_embedded_codefence() -> None:
    region = _region(_text(), "### Step 4.5", "### Step 4.6")
    assert "```python" not in region, "Step 4.5 still embeds a python code fence"
    assert "write_gate_artifact(" not in region, "gate-write code still tangled in Step 4.5"


def test_step_4_5_region_is_compact() -> None:
    # The malformed region (~1.5 KB, holding the whole Step Z body) collapses
    # to a short checklist once the block is extracted.
    region = _region(_text(), "### Step 4.5", "### Step 4.6")
    assert len(region) < 900, f"Step 4.5 region still bloated ({len(region)} chars)"


def test_single_step_z_heading_with_provenance() -> None:
    text = _text()
    # Count heading lines only (the Step 4.5 checklist references the name inline).
    headings = [ln for ln in text.splitlines() if ln.startswith("### Step Z: Write Gate Artifact")]
    assert len(headings) == 1, f"expected exactly one Step Z heading, got {len(headings)}"
    # Anchor on the heading line (newline-prefixed) -- the Step 4.5 list references
    # the name inline (backtick-prefixed) and would otherwise match first.
    step_z = _region(text + "\n### __END__", "\n### Step Z: Write Gate Artifact", "\n### ")
    assert "gate_chain.write_gate_artifact(" in step_z
    assert "ai_provenance.build_manifest(" in step_z


def test_step_z_write_precedes_completeness_check() -> None:
    text = _text()
    assert text.index("### Step Z") < text.index("### Step 7.8"), (
        "substantiate.json write (Step Z) must precede the Step 7.8 completeness check"
    )


def test_session_rotate_is_final_action() -> None:
    text = _text()
    assert "### Step 9.8" in text, "expected a final Step 9.8 session-rotation section"
    assert text.index("### Step 9.8") > text.index("### Step 9.7")
    assert text.index("session.rotate()") > text.index("### Step 7.8"), (
        "session.rotate() must run as the final action, not mid-seal (Step 4.5)"
    )


def test_required_sections_list_intact() -> None:
    region = _region(_text(), "### Step 4.5", "### Step 4.6")
    for name in ("`<skill>`", "## Execution Protocol", "### Step Z", "## Constraints", "## Next Step"):
        assert name in region, f"Step 4.5 required-sections list missing {name!r}"
