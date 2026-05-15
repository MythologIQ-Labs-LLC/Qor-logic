"""Phase 78 P1: qor-audit Step 3 Filter-Stage Ordering Coherence sub-pass (GH #47).

The audit SKILL.md must declare the sub-pass with the 4-step procedure
(preconditions / invariants / dependency graph / topological sort) and name
the VETO sub-tag `filter-order-inversion` cross-referenced to
SG-FilterOrderInversion-A.
"""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-audit/SKILL.md")


def _filter_stage_region(text: str) -> str:
    needle = "Filter-Stage Ordering Coherence"
    if needle not in text:
        raise AssertionError(
            "missing Filter-Stage Ordering Coherence sub-pass in qor-audit SKILL.md"
        )
    start = text.index(needle)
    rest = text[start:]
    next_h4 = rest.find("\n#### ", 10)
    return rest[: next_h4 if next_h4 != -1 else 4000]


def test_step3_names_filter_stage_ordering_coherence():
    text = SKILL.read_text(encoding="utf-8")
    region = _filter_stage_region(text)
    assert "Phase 78" in region, "sub-pass must be tagged Phase 78"
    assert "GH #47" in region, "sub-pass must cross-reference GH #47"
    lowered = region.lower()
    assert "pipeline" in lowered and "filter" in lowered, (
        "sub-pass body must describe pipeline-shaped filter stages"
    )
    assert "topological sort" in lowered, (
        "sub-pass body must require topological-sort verification"
    )


def test_step3_lists_four_step_procedure():
    text = SKILL.read_text(encoding="utf-8")
    region = _filter_stage_region(text)
    lowered = region.lower()
    assert "precondition" in lowered, "Step 1 of procedure must name preconditions"
    assert "invariant" in lowered, "Step 2 of procedure must name invariants"
    assert "dependency graph" in lowered, "Step 3 of procedure must name dependency graph"
    assert "topological sort" in lowered, "Step 4 of procedure must name topological sort"


def test_step3_names_filter_order_inversion_subtag():
    text = SKILL.read_text(encoding="utf-8")
    region = _filter_stage_region(text)
    assert "filter-order-inversion" in region, (
        "sub-pass must name the VETO sub-tag filter-order-inversion"
    )
    assert "SG-FilterOrderInversion-A" in region, (
        "sub-pass must cross-reference SG-FilterOrderInversion-A doctrine entry"
    )
    assert "composition" in region.lower(), (
        "sub-pass must name `composition` VETO category"
    )
