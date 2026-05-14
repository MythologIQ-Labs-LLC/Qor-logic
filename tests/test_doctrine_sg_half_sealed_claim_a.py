"""Phase 75 P3: SG-HalfSealedClaim-A doctrine entry."""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _sg_section(text: str) -> str:
    marker = "## SG-HalfSealedClaim-A"
    if marker not in text:
        raise AssertionError(f"missing doctrine entry: {marker}")
    start = text.index(marker)
    rest = text[start + len(marker):]
    next_h2 = rest.find("\n## ")
    return text[start: start + len(marker) + (next_h2 if next_h2 != -1 else len(rest))]


def test_doctrine_carries_sg_half_sealed_claim_a():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    lowered = section.lower()
    assert "pattern" in lowered, "SG entry must define the pattern"
    assert "half-checked" in lowered or "claims coverage" in lowered or "silently fail" in lowered, (
        "Pattern description must name the half-checked / coverage-claim semantics"
    )
    assert "originating recurrence" in lowered, "SG entry must include an Originating recurrence section"
    assert "2026-05-06" in section, "Originating recurrence must reference the 2026-05-06 incident"


def test_doctrine_cites_substantiate_capability_cli():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    assert "substantiate-capability" in section, (
        "SG entry must cite the qor-logic substantiate-capability CLI as countermeasure surface"
    )
