"""Phase 76 P3: qor-substantiate Step 7/7.7 entry_id prose."""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-substantiate/SKILL.md")


def _step_region(text: str, heading: str, length: int = 3000) -> str:
    if heading not in text:
        raise AssertionError(f"missing heading: {heading!r}")
    i = text.index(heading)
    return text[i: i + length]


def test_step_7_names_entry_id_derivation():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_region(text, "### Step 7:", length=4000)
    assert "entry_id" in region.lower() and "derive_entry_id" in region, (
        "Step 7 must reference entry_id.derive_entry_id"
    )
    assert "**Entry ID**" in region, "Step 7 must specify the **Entry ID** body-line format"


def test_step_7_7_names_previous_hash_uniqueness_check():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_region(text, "### Step 7.7:", length=2500)
    assert "previous_hash uniqueness" in region.lower() or "previous-hash uniqueness" in region.lower(), (
        "Step 7.7 must reference previous_hash uniqueness check"
    )
    assert "SG-ConcurrentLedgerRace-A" in region, (
        "Step 7.7 must cross-reference SG-ConcurrentLedgerRace-A"
    )
