"""Row-shaped equivalents of the `### Step 4.6.x` section helpers (Phase 222).

Eight wiring-test files each carried a private `_section(text, r"Step 4\\.6\\.N")`
that returned the prose block under a heading, plus a strip-and-fail negative and
a positional guard. Phase 222 (GH #327) collapsed those ten headings into ten
rows of one table, so the anchor moved.

These helpers keep the three primitives and change only where they read from.
Every retargeted assertion still matches the same literal -- a rewording of a
gate command fails the tests, which is the point of the guardrails and the
reason none of them were relaxed.

`section` returns commands UNESCAPED: a markdown cell writes `||` as `\\|\\|`,
and the posture assertions (`"|| true" in section`, `"|| ABORT" in section`) are
about the shell operator, not the table escape.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import substantiate_gates as sg

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)


def rows(text: str | None = None) -> list[sg.GateRow]:
    if text is None:
        return sg.parse_ladder(SUBSTANTIATE_SKILL)
    return sg.parse_ladder_text(text)


def row(step: str, text: str | None = None) -> sg.GateRow | None:
    return next((r for r in rows(text) if r.step == step), None)


def section(step: str, text: str | None = None) -> str:
    """The row rendered as a searchable block, standing in for the old section.

    Empty when the step has no row, which preserves the `assert section` shape
    the wiring tests use as their precondition.
    """
    r = row(step, text)
    if r is None:
        return ""
    return "\n".join([f"Step {r.step}: {r.gate}", *r.commands, r.records, r.notes])


def order_index(step: str, text: str | None = None) -> int:
    """Position of a step in ladder order; -1 when absent.

    Replaces the old character-offset heading comparison. Row order IS document
    order, so an index comparison asserts the same property with no regex.
    """
    steps = [r.step for r in rows(text)]
    return steps.index(step) if step in steps else -1


def without_row(step: str, text: str | None = None) -> str:
    """The skill text with one ladder row deleted.

    Feeds the strip-and-fail negatives: re-parsing the result must no longer
    surface the step's invocation. Without this, a helper that returned the
    whole file would satisfy every positive assertion.
    """
    body = SUBSTANTIATE_SKILL.read_text(encoding="utf-8") if text is None else text
    keep = [ln for ln in body.splitlines(keepends=True)
            if not ln.lstrip().startswith(f"| {step} |")]
    return "".join(keep)
