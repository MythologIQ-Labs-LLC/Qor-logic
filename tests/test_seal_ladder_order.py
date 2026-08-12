"""Phase 221: the seal gate ladder must be reachable in reading order.

Step 4.6.12 -- a fail-closed execution-continuity receipt gate -- was placed
inside `## Failure Scenarios` at 92% of the file, after the templates and
immediately before `## Constraints`. An operator executing the ladder in order
reaches 4.6.14, then 4.7, and never sees it.

It had not fired only because no plan since Phase 216 declared
`execution_continuity`, so the defect was latent rather than harmless -- the same
shape as GH #314 itself: a declared gate providing no coverage.

Introduced by the author in Phase 216 while placing a step under size pressure.

Retargeted at Phase 222 (GH #327): the ten `### Step 4.6.x` headings became ten
rows of one table. The properties are unchanged and the assertions read the same
tokens from the new canonical location. One position now covers all ten gates,
which is why the table is a stronger answer to this defect than the ordering
discipline it replaces -- there is no longer a per-step placement to get wrong.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import substantiate_gates as sg

REPO_ROOT = Path(__file__).resolve().parents[1]
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"

_TABLE_HEADER = "| Step | Gate | Command | Policy | Records | Notes |"


def _body() -> str:
    return SEAL_SKILL.read_text(encoding="utf-8")


def _step_keys() -> list[tuple[tuple[int, ...], str]]:
    """Order steps by integer tuple, not by decimal encoding.

    Packing the sub-step into a decimal makes 4.6.9 (4.69) sort after 4.6.10
    (4.61), which would fail on a correctly ordered ladder. Tuples compare
    component-wise and stay right past nine sub-steps.
    """
    return [(tuple(int(p) for p in r.step.split(".")), r.step)
            for r in sg.parse_ladder(SEAL_SKILL)]


def test_ladder_steps_appear_in_numeric_order():
    steps = _step_keys()
    keys = [k for k, _ in steps]

    assert keys == sorted(keys), (
        "gate ladder is out of order: " + " -> ".join(label for _, label in steps)
    )


def test_no_ladder_step_sits_after_failure_scenarios():
    """The sharper assertion: position, not numbering.

    A gate placed after the failure-scenario templates is unreachable to a
    reader following the ladder, whatever number it carries. Under one table
    this is a single check rather than ten.
    """
    body = _body()
    boundary = body.find("## Failure Scenarios")
    assert boundary != -1, "expected a Failure Scenarios section"

    table = body.find(_TABLE_HEADER)
    assert table != -1, "no gate ladder table found"
    assert table < boundary, (
        "the gate ladder table sits after '## Failure Scenarios' and is "
        "unreachable in reading order"
    )


def test_relocation_preserved_the_step_body():
    """A move must not become a rewrite.

    The receipt gate's fail-closed language is what makes it a gate; if the
    relocation dropped it, the step would still be present and no longer
    binding. Read from the 4.6.12 row rather than from a prose block.
    """
    row = next(r for r in sg.parse_ladder(SEAL_SKILL) if r.step == "4.6.12")

    assert "execution_continuity" in row.notes
    assert row.policy == "ABORT", "the receipt gate must remain fail-closed"
    assert "inconclusive" in row.notes, "the three-outcome distinction must survive"


def test_every_gate_declares_a_halt_policy():
    """New under the table: previously a step could describe its policy in
    prose, or forget to. A row cannot."""
    rows = sg.parse_ladder(SEAL_SKILL)
    assert rows
    assert all(r.policy in sg.POLICY_VALUES for r in rows)
