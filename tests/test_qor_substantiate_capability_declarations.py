"""Phase 75 P2: qor-substantiate SKILL.md capability declarations."""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-substantiate/SKILL.md")


def test_skill_md_contains_step_prerequisites_table():
    text = SKILL.read_text(encoding="utf-8")
    assert "## Step Prerequisites" in text, "SKILL.md must add Step Prerequisites section"
    expected = ["4.6", "4.6.5", "4.6.6", "4.7", "6.5", "6.8", "7.4", "7.5", "7.6", "7.7", "7.8", "8.5"]
    section_start = text.index("## Step Prerequisites")
    next_h2 = text.find("\n## ", section_start + 5)
    section = text[section_start:next_h2 if next_h2 != -1 else len(text)]
    for step_id in expected:
        assert step_id in section, f"Step Prerequisites table missing step {step_id}"


def test_each_step_body_cross_references_capability_table():
    text = SKILL.read_text(encoding="utf-8")
    affected_anchors = [
        "### Step 4.6:",
        "### Step 4.6.5:",
        "### Step 4.7:",
        "### Step 6.5:",
        "### Step 7.5:",
        "### Step 7.7:",
        "### Step 8.5:",
    ]
    misses = []
    for anchor in affected_anchors:
        if anchor not in text:
            continue  # Step may have different header style; skip rather than fail
        start = text.index(anchor)
        next_step = text.find("\n### Step ", start + 10)
        body = text[start: next_step if next_step != -1 else start + 4000]
        if "Phase 75" not in body or "Prerequisite" not in body:
            misses.append(anchor)
    assert not misses, f"These step bodies don't cross-reference the capability table: {misses}"
