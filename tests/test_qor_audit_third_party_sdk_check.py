"""Phase 74 P1: qor-audit Infrastructure Alignment sixth-bullet (GH #49)."""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-audit/SKILL.md")


def _alignment_region(text: str) -> str:
    start = text.index("#### Infrastructure Alignment Pass")
    end = text.index("#### Orphan Detection", start)
    return text[start:end]


def test_infrastructure_alignment_names_third_party_sdk_check():
    text = SKILL.read_text(encoding="utf-8")
    region = _alignment_region(text)
    lowered = region.lower()
    assert "third-party sdk" in lowered, (
        "Infrastructure Alignment Pass must name third-party SDK citation requirement"
    )
    assert "node_modules" in region or "type declarations" in lowered or ".d.ts" in region, (
        "Pass must reference type-declaration or SDK installation evidence form"
    )
    assert "documentation" in lowered and ("quoted" in lowered or "citation" in lowered), (
        "Pass must accept documentation URL + quoted text as evidence form"
    )


def test_infrastructure_alignment_names_behavioral_semantics_claim():
    text = SKILL.read_text(encoding="utf-8")
    region = _alignment_region(text)
    lowered = region.lower()
    assert "behavioral-semantics" in lowered or "behavioral semantics" in lowered, (
        "Pass must name behavioral-semantics claim category"
    )
    semantic_kinds = ["durability", "transaction", "concurrency", "trigger", "lock"]
    hits = sum(1 for k in semantic_kinds if k in lowered)
    assert hits >= 2, (
        f"Pass body must enumerate behavioral-semantics claim kinds; found only "
        f"{hits}/{len(semantic_kinds)} of {semantic_kinds}"
    )
