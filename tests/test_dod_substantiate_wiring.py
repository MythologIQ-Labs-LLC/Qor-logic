"""Phase 92: wiring tests for /qor-substantiate Step 4.6.7 dod_check (GH #86).

Anchored to the Step 4.6.7 section header in qor-substantiate SKILL.md,
paired with a strip-and-fail negative and a positional guard. Mirrors
the Phase 84 / Phase 87 / Phase 89 wiring-test convention.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)

from tests import ladder_helpers as lh


# --- Phase 222 (GH #327): retargeted from `### Step 4.6.7` heading to the
# --- gate ladder row. Same literals, new canonical location.

def test_step_4_6_7_invokes_dod_check():
    sec = lh.section("4.6.7")
    assert sec, "no gate ladder row for Step 4.6.7"
    assert ("qor.scripts.dod_check" in sec or "qor-logic scripts dod_check" in sec), (
        "Step 4.6.7 missing the dod_check invocation"
    )
    assert "|| true" in sec, "Step 4.6.7 missing the '|| true' posture guard"


def test_step_4_6_7_row_removed_breaks_assertion():
    """THE COUNTERFACTUAL: delete the row and the invocation must vanish."""
    stripped = lh.without_row("4.6.7")
    assert "dod_check" not in lh.section("4.6.7", stripped)


def test_step_4_6_7_positioned_between_4_6_6_and_4_7():
    """Row order is document order, so an index comparison replaces the old
    character-offset heading search. The 4.7 half of the old assertion is now
    structural: every ladder row precedes Step 4.7 by construction, and
    `test_seal_ladder_order` holds the table ahead of the file's tail."""
    assert lh.order_index("4.6.6") >= 0, "Step 4.6.6 row is missing"
    assert lh.order_index("4.6.7") >= 0, "Step 4.6.7 row is missing"
    assert lh.order_index("4.6.6") < lh.order_index("4.6.7")
