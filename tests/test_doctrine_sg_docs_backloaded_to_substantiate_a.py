"""Phase 79 P2: SG-DocsBackloadedToSubstantiate-A doctrine entry (GH #52)."""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _sg_region(text: str) -> str:
    needle = "SG-DocsBackloadedToSubstantiate-A"
    if needle not in text:
        raise AssertionError(
            "missing SG-DocsBackloadedToSubstantiate-A entry in doctrine"
        )
    start = text.index("## " + needle)
    rest = text[start:]
    end = rest.find("\n---", 10)
    return rest[: end if end != -1 else 6000]


def test_doctrine_carries_sg_docs_backloaded_to_substantiate_a():
    text = DOCTRINE.read_text(encoding="utf-8")
    region = _sg_region(text)
    assert "Phase 79" in region, "SG entry must be tagged Phase 79"
    lowered = region.lower()
    assert "backloaded" in lowered or "deferred" in lowered, (
        "SG entry must describe doc lifecycle being backloaded/deferred to substantiate"
    )
    assert "verification" in lowered and "authoring" in lowered, (
        "SG entry must distinguish verification gate from authoring phase"
    )
    assert "warn" in lowered, (
        "SG entry must name WARN-only post-hoc detection"
    )


def test_doctrine_cites_countermeasure():
    text = DOCTRINE.read_text(encoding="utf-8")
    region = _sg_region(text)
    assert "Step 8.5" in region, (
        "SG entry must cross-reference Step 8.5 countermeasure"
    )
    assert "/qor-implement" in region, (
        "SG entry must locate the countermeasure at /qor-implement"
    )
    assert "Documentation Sync" in region, (
        "SG entry must name the countermeasure step title"
    )
    assert "GH #52" in region or "Issue #52" in region, (
        "SG entry must cross-reference Issue #52"
    )
