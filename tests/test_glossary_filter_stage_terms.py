"""Phase 78 P3: glossary terms for filter-stage ordering (GH #47)."""
from pathlib import Path

GLOSSARY = Path("qor/references/glossary.md")


def test_glossary_defines_filter_stage_terms():
    text = GLOSSARY.read_text(encoding="utf-8")
    assert "term: pipeline stage dependency graph" in text, (
        "glossary must define `pipeline stage dependency graph`"
    )
    assert "term: filter-stage ordering coherence" in text, (
        "glossary must define `filter-stage ordering coherence`"
    )
    assert "term: SG-FilterOrderInversion-A" in text, (
        "glossary must define `SG-FilterOrderInversion-A`"
    )
    # Each entry must declare its home and be tied to Phase 78
    assert text.count("introduced_in_plan: phase78-filter-stage-ordering") >= 3, (
        "all 3 Phase 78 glossary entries must carry the introduced_in_plan slug"
    )
