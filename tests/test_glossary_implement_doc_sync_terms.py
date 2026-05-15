"""Phase 79 P3: glossary terms for implement documentation sync (GH #52)."""
from pathlib import Path

GLOSSARY = Path("qor/references/glossary.md")


def test_glossary_defines_implement_doc_sync_terms():
    text = GLOSSARY.read_text(encoding="utf-8")
    assert "term: implement documentation sync" in text, (
        "glossary must define `implement documentation sync`"
    )
    assert "term: SG-DocsBackloadedToSubstantiate-A" in text, (
        "glossary must define `SG-DocsBackloadedToSubstantiate-A`"
    )
    assert text.count("introduced_in_plan: phase79-implement-doc-sync") >= 2, (
        "both Phase 79 glossary entries must carry the introduced_in_plan slug"
    )
