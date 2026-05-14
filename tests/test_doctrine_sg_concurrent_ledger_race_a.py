"""Phase 76 P3: SG-ConcurrentLedgerRace-A doctrine entry."""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-shadow-genome-countermeasures.md")


def _sg_section(text: str) -> str:
    marker = "## SG-ConcurrentLedgerRace-A"
    if marker not in text:
        raise AssertionError(f"missing doctrine entry: {marker}")
    start = text.index(marker)
    rest = text[start + len(marker):]
    next_h2 = rest.find("\n## ")
    return text[start: start + len(marker) + (next_h2 if next_h2 != -1 else len(rest))]


def test_doctrine_carries_sg_concurrent_ledger_race_a():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    lowered = section.lower()
    assert "pattern" in lowered, "SG entry must define the pattern"
    # Originating recurrence must name at least one of the duplicate entries
    assert ("#16" in section or "#17" in section or "#18" in section), (
        "Originating recurrence must reference Entry #16/17/18 duplicates"
    )
    assert "previous_hash uniqueness" in lowered or "previous-hash uniqueness" in lowered, (
        "Countermeasure must name previous_hash uniqueness detection"
    )


def test_doctrine_forbids_retroactive_renumber():
    text = DOCTRINE.read_text(encoding="utf-8")
    section = _sg_section(text)
    lowered = section.lower()
    assert "retroactive" in lowered or "history-rewrite" in lowered or "past sealed" in lowered, (
        "SG entry must explicitly forbid retroactive renumbering of past sealed entries"
    )
    assert "forbid" in lowered or "prohibit" in lowered or "not permit" in lowered, (
        "SG entry must contain explicit prohibition language"
    )
