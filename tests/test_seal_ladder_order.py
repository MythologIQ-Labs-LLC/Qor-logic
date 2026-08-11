"""Phase 221: the seal gate ladder must be reachable in reading order.

Step 4.6.12 -- a fail-closed execution-continuity receipt gate -- was placed
inside `## Failure Scenarios` at 92% of the file, after the templates and
immediately before `## Constraints`. An operator executing the ladder in order
reaches 4.6.14, then 4.7, and never sees it.

It had not fired only because no plan since Phase 216 declared
`execution_continuity`, so the defect was latent rather than harmless -- the same
shape as GH #314 itself: a declared gate providing no coverage.

Introduced by the author in Phase 216 while placing a step under size pressure.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEAL_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"

_STEP_RE = re.compile(r"^### Step (4\.6(?:\.\d+)?):", re.MULTILINE)


def _body() -> str:
    return SEAL_SKILL.read_text(encoding="utf-8")


def _step_numbers_in_file_order() -> list[tuple[tuple[int, ...], str]]:
    """Order steps by integer tuple, not by decimal encoding.

    Packing the sub-step into a decimal makes 4.6.9 (4.69) sort after 4.6.10
    (4.61), which would fail on a correctly ordered ladder. Tuples compare
    component-wise and stay right past nine sub-steps.
    """
    out = []
    for m in _STEP_RE.finditer(_body()):
        label = m.group(1)
        out.append((tuple(int(part) for part in label.split(".")), label))
    return out


def test_ladder_steps_appear_in_numeric_order():
    """THE COUNTERFACTUAL. Fails at HEAD, where 4.6.12 follows 4.6.14."""
    steps = _step_numbers_in_file_order()
    keys = [k for k, _ in steps]

    assert keys == sorted(keys), (
        "gate ladder is out of order: "
        + " -> ".join(label for _, label in steps)
    )


def test_no_ladder_step_sits_after_failure_scenarios():
    """The sharper assertion: position, not numbering.

    A gate placed after the failure-scenario templates is unreachable to a
    reader following the ladder, whatever number it carries.
    """
    body = _body()
    boundary = body.find("## Failure Scenarios")
    assert boundary != -1, "expected a Failure Scenarios section"

    stranded = [m.group(1) for m in _STEP_RE.finditer(body) if m.start() > boundary]

    assert stranded == [], (
        f"gate step(s) {stranded} sit after '## Failure Scenarios' and are "
        "unreachable in reading order"
    )


def test_relocation_preserved_the_step_body():
    """A move must not become a rewrite.

    The receipt gate's fail-closed language is what makes it a gate; if the
    relocation dropped it, the step would still be present and no longer
    binding.
    """
    body = _body()
    start = body.index("### Step 4.6.12")
    step = body[start:start + 600]

    assert "execution_continuity" in step
    assert "ABORT" in step, "the receipt gate must remain fail-closed"
    assert "inconclusive" in step, "the three-outcome distinction must survive"
