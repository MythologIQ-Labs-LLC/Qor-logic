"""Phase 73 P3: qor-plan Step 5 Feature Inventory Touches prose."""
from pathlib import Path

SKILL = Path("qor/skills/sdlc/qor-plan/SKILL.md")


def _step_5_region(text: str) -> str:
    if "### Step 5:" not in text:
        raise AssertionError("missing Step 5 heading")
    start = text.index("### Step 5:")
    rest = text[start + len("### Step 5:"):]
    next_h3 = rest.find("\n### Step ")
    return text[start: start + len("### Step 5:") + (next_h3 if next_h3 != -1 else len(rest))]


def test_step_5_names_feature_inventory_touches():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_5_region(text)
    assert "Feature Inventory Touches" in region, (
        "Step 5 must require Feature Inventory Touches section"
    )
    lowered = region.lower()
    assert "src/" in region or "touches src" in lowered, (
        "Step 5 must describe the src/-touch trigger condition"
    )


def test_step_5_links_doctrine_feature_tdd():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_5_region(text)
    assert "doctrine-feature-tdd" in region, (
        "Step 5 must cite the per-feature TDD doctrine"
    )
