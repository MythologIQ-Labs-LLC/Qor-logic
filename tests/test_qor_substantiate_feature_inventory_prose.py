"""Phase 73 P3: qor-substantiate Step 6 FEATURE_INDEX prose surface."""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-substantiate/SKILL.md")


def _step_6_region(text: str) -> str:
    if "### Step 6:" not in text:
        raise AssertionError("missing Step 6 heading")
    start = text.index("### Step 6:")
    rest = text[start + len("### Step 6:"):]
    next_h3 = rest.find("\n### Step ")
    return text[start: start + len("### Step 6:") + (next_h3 if next_h3 != -1 else len(rest))]


def test_step_6_verification_pass():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_6_region(text)
    assert "FEATURE_INDEX" in region, "Step 6 must reference FEATURE_INDEX verification"
    lowered = region.lower()
    assert "verify" in lowered, "Step 6 must describe the verification pass"


def test_step_6_names_ledger_counts_surface():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_6_region(text)
    for token in ("verified", "unverified", "n/a"):
        assert token in region.lower(), (
            f"Step 6 must surface count of {token!r} in seal ledger entry"
        )
    assert "Total" in region or "total" in region.lower(), (
        "Step 6 must surface a Total count in the seal entry body"
    )
