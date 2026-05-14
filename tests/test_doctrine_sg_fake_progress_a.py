"""Phase 74 P3: SG-FakeProgress-A doctrine entry."""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _sg_section(text: str) -> str:
    marker = "## SG-FakeProgress-A"
    if marker not in text:
        raise AssertionError(f"missing doctrine entry: {marker}")
    start = text.index(marker)
    rest = text[start + len(marker):]
    next_h2 = rest.find("\n## ")
    return text[start: start + len(marker) + (next_h2 if next_h2 != -1 else len(rest))]


def test_doctrine_carries_sg_fake_progress_a():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    lowered = section.lower()
    assert "pattern" in lowered, "SG entry must define the pattern"
    assert "fake-jump" in lowered or ("0%" in section and "100%" in section), (
        "Pattern description must name fake-jump (0%->100% without intermediate state)"
    )
    assert "originating recurrence" in lowered, (
        "SG entry must include an Originating recurrence section"
    )
    assert "failsafe" in lowered, (
        "Originating recurrence must name FailSafe install-skills-card source incident"
    )


def test_doctrine_cites_countermeasure():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    assert "Live-Progress Invariant" in section, (
        "SG entry must cross-reference the Live-Progress Invariant countermeasure"
    )
    assert "/qor-audit" in section and "Ghost UI Pass" in section, (
        "SG entry must name /qor-audit Ghost UI Pass as countermeasure surface"
    )
