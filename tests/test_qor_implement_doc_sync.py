"""Phase 79 P1: /qor-implement Step 8.5 Documentation Sync (GH #52).

qor-implement SKILL.md must declare a Step 8.5 inserted between Step 8
(Post-Build Cleanup) and Step 9 (Complexity Self-Check) with the 4-item
documentation-surface checklist and doc_tier-aware skip semantics.
"""
from pathlib import Path

SKILL = Path("qor/skills/sdlc/qor-implement/SKILL.md")


def _step_8_5_region(text: str) -> str:
    needle = "### Step 8.5: Documentation Sync"
    if needle not in text:
        raise AssertionError(
            "missing Step 8.5 Documentation Sync in qor-implement SKILL.md"
        )
    start = text.index(needle)
    rest = text[start:]
    end = rest.find("\n### Step ", 10)
    return rest[: end if end != -1 else 5000]


def test_step_8_5_exists_between_step_8_and_step_9():
    text = SKILL.read_text(encoding="utf-8")
    idx_8 = text.find("### Step 8: Post-Build Cleanup")
    idx_8_5 = text.find("### Step 8.5: Documentation Sync")
    idx_9 = text.find("### Step 9: Complexity Self-Check")
    assert idx_8 != -1, "Step 8 must exist in qor-implement SKILL.md"
    assert idx_8_5 != -1, "Step 8.5 must exist in qor-implement SKILL.md"
    assert idx_9 != -1, "Step 9 must exist in qor-implement SKILL.md"
    assert idx_8 < idx_8_5 < idx_9, (
        f"Step 8.5 must appear between Step 8 (offset {idx_8}) and Step 9 "
        f"(offset {idx_9}); found at offset {idx_8_5}"
    )


def test_step_8_5_lists_four_item_checklist():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_8_5_region(text)
    assert "Phase 79" in region, "Step 8.5 must be tagged Phase 79"
    assert "GH #52" in region, "Step 8.5 must cross-reference GH #52"
    assert "ARCHITECTURE_PLAN.md" in region, "Step 8.5 must name ARCHITECTURE_PLAN.md file tree"
    lowered = region.lower()
    assert "architecture docs" in lowered or "architecture doc" in lowered, (
        "Step 8.5 must name architecture docs as item 2"
    )
    assert "operations docs" in lowered or "operations doc" in lowered, (
        "Step 8.5 must name operations docs as item 3"
    )
    assert "schema docs" in lowered or "schema doc" in lowered, (
        "Step 8.5 must name schema docs as item 4"
    )


def test_step_8_5_names_doc_tier_aware_skip():
    text = SKILL.read_text(encoding="utf-8")
    region = _step_8_5_region(text)
    lowered = region.lower()
    assert "doc_tier" in lowered, "Step 8.5 must reference doc_tier"
    for tier in ("minimal", "standard", "system"):
        assert tier in lowered, f"Step 8.5 must name doc_tier behavior for `{tier}`"
    # Cross-reference to substantiate verification gates
    assert "step 4.7" in lowered or "step 6.5" in lowered, (
        "Step 8.5 must cross-reference /qor-substantiate verification gates"
    )
    assert "SG-DocsBackloadedToSubstantiate-A" in region, (
        "Step 8.5 must cite SG-DocsBackloadedToSubstantiate-A doctrine entry"
    )
