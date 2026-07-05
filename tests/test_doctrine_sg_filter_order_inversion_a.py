"""Phase 78 P2: SG-FilterOrderInversion-A doctrine entry (GH #47).

doctrine-shadow-genome-countermeasures.md must carry the SG entry with the
canonical pattern description (pipeline filter stages composed out of
dependency order; stage-by-stage review passes; composition defect) and the
countermeasure cross-reference to /qor-audit Step 3 Filter-Stage Ordering
Coherence sub-pass.
"""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _sg_region(text: str) -> str:
    needle = "SG-FilterOrderInversion-A"
    if needle not in text:
        raise AssertionError(
            "missing SG-FilterOrderInversion-A entry in doctrine-shadow-genome-countermeasures.md"
        )
    start = text.index("## " + needle)
    rest = text[start:]
    end = rest.find("\n---", 10)
    return rest[: end if end != -1 else 6000]


def test_doctrine_carries_sg_filter_order_inversion_a():
    text = DOCTRINE.read_text(encoding="utf-8")
    region = _sg_region(text)
    assert "Phase 78" in region, "SG entry must be tagged Phase 78"
    lowered = region.lower()
    assert "pipeline" in lowered and "filter" in lowered, (
        "SG entry must describe pipeline-shaped filter stages"
    )
    assert "dependency order" in lowered or "dependency graph" in lowered, (
        "SG entry must name dependency-order semantics"
    )
    assert "composition" in lowered, (
        "SG entry must distinguish composition defect from stage defect"
    )


def test_doctrine_cites_countermeasure():
    text = DOCTRINE.read_text(encoding="utf-8")
    region = _sg_region(text)
    assert "Filter-Stage Ordering Coherence" in region, (
        "SG entry must cross-reference Filter-Stage Ordering Coherence sub-pass"
    )
    assert "/qor-audit" in region and "Step 3" in region, (
        "SG entry must locate the countermeasure at /qor-audit Step 3"
    )
    assert "filter-order-inversion" in region, (
        "SG entry must name the VETO sub-tag filter-order-inversion"
    )
    assert "skill_forge" in region or "dispatcher" in region, (
        "SG entry must cite the Skill-Forge dispatcher originating recurrence"
    )
