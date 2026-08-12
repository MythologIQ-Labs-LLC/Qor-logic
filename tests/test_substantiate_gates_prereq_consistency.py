"""Phase 222 (GH #327): two tables, one fact, checked rather than merged.

`SKILL.md` carries a Step Prerequisites table (parsed since Phase 75 by
`substantiate_capability.parse_step_prerequisites`) and, as of this phase, a gate
ladder table. Both mention module prerequisites for the 4.6.x steps.

Merging them would rewrite the host-capability consumers and is deliberately out
of scope. Instead the duplication is made safe by a check: whatever a ladder row
says about its module must agree with the prerequisites table. A fact with two
homes and no cross-check is how the two drift.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import substantiate_capability as sc
from qor.scripts import substantiate_gates as sg

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def test_every_ladder_module_appears_in_the_prerequisites_table():
    """Every `module:` a ladder row names is declared for the same step."""
    findings = sg.check_prereq_consistency(
        sg.parse_ladder(SEAL_SKILL),
        sc.parse_step_prerequisites(SEAL_SKILL),
    )
    assert findings == [], "ladder and prerequisites table disagree: " + "; ".join(findings)


def test_a_prerequisite_drift_is_detected():
    """THE COUNTERFACTUAL.

    The fixture's prerequisites table names a truncated variant of the module
    its ladder row names. A check that returns [] on the live file forever would
    satisfy the test above without ever comparing anything.
    """
    fixture = FIXTURES / "seal_ladder_prereq_drift.md"
    findings = sg.check_prereq_consistency(
        sg.parse_ladder(fixture),
        sc.parse_step_prerequisites(fixture),
    )
    assert findings, "expected the truncated module spelling to be reported"
    assert "4.6.5" in " ".join(findings)


def test_consistency_check_ignores_rows_that_declare_no_module():
    """Not every gate has a module prerequisite; absence is not disagreement."""
    rows = sg.parse_ladder(FIXTURES / "seal_ladder_complete.md")
    assert sg.check_prereq_consistency(rows, []) == []
