"""Phase 72 P3: SG-CitationDrift-A doctrine entry."""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _sg_section(text: str) -> str:
    marker = "## SG-CitationDrift-A"
    if marker not in text:
        raise AssertionError(f"missing doctrine entry: {marker}")
    start = text.index(marker)
    rest = text[start + len(marker):]
    next_h2 = rest.find("\n## ")
    return text[start: start + len(marker) + (next_h2 if next_h2 != -1 else len(rest))]


def test_doctrine_carries_sg_citation_drift_a():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    lowered = section.lower()
    assert "pattern" in lowered, "SG entry must define the pattern"
    assert "citation" in lowered and ("cross-iteration" in lowered or "iter-n" in lowered or "across iterations" in lowered), (
        "Pattern description must name cross-iteration unverified citation drift"
    )
    assert "originating recurrence" in lowered, (
        "SG entry must include an Originating recurrence section"
    )


def test_doctrine_cites_countermeasures():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    assert "Infrastructure Citation Inventory" in section, (
        "SG entry must reference P1 (Infrastructure Citation Inventory)"
    )
    assert "re-walk" in section.lower() or "rewalk" in section.lower(), (
        "SG entry must reference P2 (full-plan re-walk on iter-N>1)"
    )
    assert "/qor-plan" in section and "/qor-audit" in section, (
        "SG entry must cite both /qor-plan and /qor-audit as countermeasure surfaces"
    )
