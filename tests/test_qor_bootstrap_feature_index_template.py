"""Phase 80 P1: qor-bootstrap FEATURE_INDEX.md template section (GH #73)."""
from pathlib import Path

TEMPLATES = Path("qor/skills/meta/qor-bootstrap/references/qor-bootstrap-templates.md")


def test_templates_define_feature_index_section():
    text = TEMPLATES.read_text(encoding="utf-8")
    assert "## FEATURE_INDEX.md Template" in text, (
        "templates file must define FEATURE_INDEX.md Template section"
    )
    # Region extends from the FEATURE_INDEX heading to the next top-level
    # template heading. Use the known successor heading (Final Report
    # Template) to bound the region; the intervening h2 headings live inside
    # the fenced markdown code block.
    start = text.index("## FEATURE_INDEX.md Template")
    end_marker = "## Final Report Template"
    end_idx = text.find(end_marker, start)
    region = text[start: end_idx if end_idx != -1 else start + 4000]
    assert "{project_name}" in region, (
        "template must use {project_name} placeholder"
    )
    assert "Coverage Summary" in region, (
        "template must include Coverage Summary block"
    )
    assert "| ID | Feature | Doc | Code | Test | Status | Notes |" in region, (
        "template must include the canonical 7-column table header"
    )
    assert "Gaps Surfaced" in region, (
        "template must include Gaps Surfaced section"
    )
    assert "/qor-implement" in region, (
        "template must reference /qor-implement as the consumer of FEATURE_INDEX.md"
    )
