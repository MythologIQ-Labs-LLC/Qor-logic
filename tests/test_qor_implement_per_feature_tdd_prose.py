"""Phase 73 P3: qor-implement per-feature TDD prose surface."""
from pathlib import Path

SKILL = Path("qor/skills/sdlc/qor-implement/SKILL.md")


def _step_region(text: str, heading: str) -> str:
    if heading not in text:
        raise AssertionError(f"missing {heading!r}")
    start = text.index(heading)
    rest = text[start + len(heading):]
    next_h3 = rest.find("\n### Step ")
    return text[start: start + len(heading) + (next_h3 if next_h3 != -1 else len(rest))]


def test_step_5_expands_to_per_feature_scope():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_region(text, "### Step 5: TDD-Light")
    lowered = region.lower()
    assert "per-feature" in lowered, "Step 5 must name per-feature TDD expansion"
    assert "feature inventory touches" in lowered, (
        "Step 5 must cross-link to the plan's Feature Inventory Touches"
    )
    assert "fail" in lowered and ("then" in lowered or "before" in lowered), (
        "Step 5 must describe failing-test-before-code sequencing"
    )


def test_step_12_5_names_feature_index_update_obligation():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_region(text, "### Step 12.5: Implementation Staging")
    assert "FEATURE_INDEX" in region, (
        "Step 12.5 must name FEATURE_INDEX update obligation"
    )
    lowered = region.lower()
    assert "append" in lowered or "update" in lowered, (
        "Step 12.5 must describe append/update semantics"
    )
