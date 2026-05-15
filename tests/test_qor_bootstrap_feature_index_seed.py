"""Phase 80 P1: qor-bootstrap Step 6.6 FEATURE_INDEX.md seed (GH #73)."""
from pathlib import Path

SKILL = Path("qor/skills/meta/qor-bootstrap/SKILL.md")


def test_step_6_6_seeds_feature_index_with_phase73_cross_reference():
    text = SKILL.read_text(encoding="utf-8")
    needle = "### Step 6.6: Seed FEATURE_INDEX.md"
    assert needle in text, "qor-bootstrap must declare Step 6.6 Seed FEATURE_INDEX.md"
    start = text.index(needle)
    rest = text[start:]
    end = rest.find("\n### Step ", 10)
    region = rest[: end if end != -1 else 4000]
    assert "Phase 80" in region, "Step 6.6 must be tagged Phase 80"
    assert "GH #73" in region, "Step 6.6 must cross-reference GH #73"
    assert "FEATURE_INDEX.md" in region, "Step 6.6 must name FEATURE_INDEX.md"
    assert "Phase 73" in region, "Step 6.6 must cross-reference Phase 73 obligation"
    lowered = region.lower()
    assert "chicken-and-egg" in lowered or "first cycle" in lowered, (
        "Step 6.6 must name the chicken-and-egg / first-cycle rationale"
    )
    assert "step 12.5" in lowered, (
        "Step 6.6 must reference /qor-implement Step 12.5 staging gate"
    )


def test_success_criteria_lists_feature_index_seed():
    text = SKILL.read_text(encoding="utf-8")
    assert "FEATURE_INDEX.md exists with seed scaffold" in text, (
        "Success Criteria must list FEATURE_INDEX.md seed scaffold bullet"
    )
