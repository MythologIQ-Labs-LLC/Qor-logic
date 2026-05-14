"""Phase 73 P3: qor-audit Feature Test Coverage Pass prose."""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-audit/SKILL.md")


def _step_3_region(text: str) -> str:
    if "### Step 3:" not in text:
        raise AssertionError("missing Step 3 heading")
    start = text.index("### Step 3:")
    rest = text[start + len("### Step 3:"):]
    next_h3 = rest.find("\n### Step ")
    return text[start: start + len("### Step 3:") + (next_h3 if next_h3 != -1 else len(rest))]


def test_step_3_names_feature_test_coverage_pass():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_3_region(text)
    assert "Feature Test Coverage Pass" in region, (
        "Step 3 must add the Feature Test Coverage Pass"
    )
    assert "test descriptor" in region.lower() or "Feature Inventory Touches" in region, (
        "Pass body must reference the plan's Feature Inventory Touches descriptors"
    )


def test_step_3_ties_veto_to_feature_test_undeclared():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_3_region(text)
    assert "feature-test-undeclared" in region, (
        "Pass must name the feature-test-undeclared VETO category"
    )
    assert "VETO" in region, "Pass must name VETO as binding action"
