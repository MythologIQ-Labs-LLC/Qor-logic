"""Phase 93: wiring tests for /qor-substantiate Step 4.6.8 (GH #89).

Anchored + strip-and-fail + positional guard per the Phase 84/87/89/91/92
wiring-test convention.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)

from tests import ladder_helpers as lh


# --- Phase 222 (GH #327): retargeted from `### Step 4.6.8` heading to the
# --- gate ladder row. Same literals, new canonical location.

def test_step_4_6_8_invokes_merge_velocity_check():
    sec = lh.section("4.6.8")
    assert sec, "no gate ladder row for Step 4.6.8"
    assert ("qor.scripts.merge_velocity_check" in sec or "qor-logic scripts merge_velocity_check" in sec), (
        "Step 4.6.8 missing the merge_velocity_check invocation"
    )
    # Phase 129 (GH #153) made this gate fail-closed. Until Phase 222 this test
    # asserted `"|| true" in section` under the message "WARN-only contract",
    # and passed -- because the sentence documenting the REMOVAL of `|| true`
    # contained the literal being searched for. The token matched while the
    # property was false. Assert the shipped posture instead.
    assert "|| ABORT" in sec, "Step 4.6.8 must be fail-closed (Phase 129)"
    assert lh.row("4.6.8").policy == "ABORT"


def test_step_4_6_8_row_removed_breaks_assertion():
    """THE COUNTERFACTUAL: delete the row and the invocation must vanish."""
    stripped = lh.without_row("4.6.8")
    assert "merge_velocity_check" not in lh.section("4.6.8", stripped)


def test_step_4_6_8_positioned_between_4_6_7_and_4_7():
    """Row order is document order, so an index comparison replaces the old
    character-offset heading search. The 4.7 half of the old assertion is now
    structural: every ladder row precedes Step 4.7 by construction, and
    `test_seal_ladder_order` holds the table ahead of the file's tail."""
    assert lh.order_index("4.6.7") >= 0, "Step 4.6.7 row is missing"
    assert lh.order_index("4.6.8") >= 0, "Step 4.6.8 row is missing"
    assert lh.order_index("4.6.7") < lh.order_index("4.6.8")
