"""Phase 95: wiring tests for /qor-substantiate Step 4.6.9 (GH #92)."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)

from tests import ladder_helpers as lh


# --- Phase 222 (GH #327): retargeted from `### Step 4.6.9` heading to the
# --- gate ladder row. Same literals, new canonical location.

def test_step_4_6_9_invokes_skill_size_budget_lint():
    sec = lh.section("4.6.9")
    assert sec, "no gate ladder row for Step 4.6.9"
    assert ("qor.scripts.skill_size_budget_lint" in sec or "qor-logic scripts skill_size_budget_lint" in sec), (
        "Step 4.6.9 missing the skill_size_budget_lint invocation"
    )
    assert "|| true" in sec, "Step 4.6.9 missing the '|| true' posture guard"


def test_step_4_6_9_row_removed_breaks_assertion():
    """THE COUNTERFACTUAL: delete the row and the invocation must vanish."""
    stripped = lh.without_row("4.6.9")
    assert "skill_size_budget_lint" not in lh.section("4.6.9", stripped)


def test_step_4_6_9_positioned_between_4_6_8_and_4_7():
    """Row order is document order, so an index comparison replaces the old
    character-offset heading search. The 4.7 half of the old assertion is now
    structural: every ladder row precedes Step 4.7 by construction, and
    `test_seal_ladder_order` holds the table ahead of the file's tail."""
    assert lh.order_index("4.6.8") >= 0, "Step 4.6.8 row is missing"
    assert lh.order_index("4.6.9") >= 0, "Step 4.6.9 row is missing"
    assert lh.order_index("4.6.8") < lh.order_index("4.6.9")
