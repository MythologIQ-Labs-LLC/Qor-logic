"""Phase 72 P2: qor-audit Infrastructure Alignment Pass full re-walk on iter-N>1."""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-audit/SKILL.md")


def _alignment_region(text: str) -> str:
    start = text.index("#### Infrastructure Alignment Pass")
    end = text.index("#### Orphan Detection", start)
    return text[start:end]


def test_infrastructure_alignment_documents_full_rewalk():
    text = SKILL.read_text(encoding="utf-8")
    region = _alignment_region(text)
    lowered = region.lower()
    assert "iter-n>1" in lowered or "iteration > 1" in lowered or "iterations after the first" in lowered, (
        "Infrastructure Alignment Pass must name iter-N>1 semantics explicitly"
    )
    assert "re-walk" in lowered or "rewalk" in lowered, (
        "Pass must use 're-walk' to name the full Locked Decision pass"
    )
    assert "diff" in lowered, (
        "Pass must explicitly contrast full re-walk vs diff-from-iter-N-1"
    )


def test_full_rewalk_cites_sg_citation_drift_a():
    text = SKILL.read_text(encoding="utf-8")
    region = _alignment_region(text)
    assert "SG-CitationDrift-A" in region, (
        "Infrastructure Alignment Pass must name SG-CitationDrift-A as the originating pattern"
    )


def test_full_rewalk_ties_veto_to_infrastructure_mismatch():
    text = SKILL.read_text(encoding="utf-8")
    region = _alignment_region(text)
    assert "infrastructure-mismatch" in region, (
        "iter-N>1 re-walk VETO must use the infrastructure-mismatch findings category"
    )
    assert "VETO" in region, "Pass must name VETO as the binding action"
