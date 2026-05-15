"""Phase 80 P2: glossary FEATURE_INDEX.md genesis seed (GH #73)."""
from pathlib import Path

GLOSSARY = Path("qor/references/glossary.md")


def test_glossary_defines_feature_index_seed_term():
    text = GLOSSARY.read_text(encoding="utf-8")
    assert "term: FEATURE_INDEX.md genesis seed" in text, (
        "glossary must define `FEATURE_INDEX.md genesis seed`"
    )
    assert "introduced_in_plan: phase80-bootstrap-feature-index" in text, (
        "Phase 80 glossary entry must carry the introduced_in_plan slug"
    )
