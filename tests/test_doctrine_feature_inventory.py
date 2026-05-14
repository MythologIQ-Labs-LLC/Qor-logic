"""Phase 73 P1: doctrine-feature-inventory.md tests."""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-feature-inventory.md")


def _section_after_heading(text: str, heading: str, length: int = 2000) -> str:
    if heading not in text:
        raise AssertionError(f"missing heading: {heading!r}")
    i = text.index(heading)
    return text[i: i + length]


def test_documents_index_columns():
    text = DOCTRINE.read_text(encoding="utf-8")
    region = _section_after_heading(text, "FEATURE_INDEX")
    for col in ("ID", "Name", "Source", "Doc citation", "Test path", "Verification status"):
        assert col in region, f"FEATURE_INDEX section must name column {col!r}"


def test_documents_lifecycle_hooks():
    text = DOCTRINE.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "step 12.5" in lowered, "must reference /qor-implement Step 12.5 hook"
    assert "step 6" in lowered, "must reference /qor-substantiate Step 6 hook"
    assert "verify" in lowered and "regression" in lowered, (
        "must describe seal-time verify + regression semantics"
    )
    assert "verified" in lowered and "unverified" in lowered and "n/a" in lowered, (
        "must describe the three status values"
    )
