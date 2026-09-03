"""Phase 255: qor/references citations in plans are resolved by an actual check.

Closes the unaddressed severity-4 `hallucination` event of 2026-08-12, whose
recorded remedy was "wire _REFERENCE_PATH_RE or delete it". A doctrine path that
did not exist was asserted to the operator as fact and written into a plan as an
Affected File, and no check read that path family -- the regex was defined and
never used, while its `_MODULE_RE` and `_SKILL_PATH_RE` siblings each drove a
loop.
"""
from __future__ import annotations

import re
from pathlib import Path

from qor.scripts import plan_grep_lint as pgl

REPO = Path(__file__).resolve().parents[1]
_ALLOW = re.compile(r"grep-lint:\s*ok=(\S[^\s>]*)")


def _plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "docs" / "plan-qor-phase999-probe.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _kinds(warnings) -> list[str]:
    return [w.kind for w in warnings]


def test_unresolvable_reference_is_reported(tmp_path):
    """The exact path from the event.

    Red before the fix, and red for the reason the event records: nothing read
    the `qor/references` family at all.
    """
    plan = _plan(tmp_path, "## Affected Files\n\n- qor/references/doctrine-citation-pairing.md\n")

    warnings = pgl.check_plan(plan, tmp_path)

    assert "reference-path-missing" in _kinds(warnings)
    hit = next(w for w in warnings if w.kind == "reference-path-missing")
    assert hit.citation == "qor/references/doctrine-citation-pairing.md"
    assert hit.line == 3


def test_resolvable_reference_is_silent():
    """A doctrine that exists must not be reported, or the check is noise."""
    plan = REPO / "docs" / "plan-qor-phase255-reference-path-resolution.md"

    warnings = pgl.check_plan(plan, REPO)

    assert "reference-path-missing" not in _kinds(warnings), (
        f"this plan must pass its own check: "
        f"{[w.citation for w in warnings if w.kind == 'reference-path-missing']}"
    )


def test_new_declared_reference_is_exempt(tmp_path):
    """A doctrine the plan declares it will create is not a broken citation.

    Without this the check fires on every phase that introduces a doctrine --
    three did so in the same week as this one.
    """
    plan = _plan(
        tmp_path,
        "## Affected Files\n\n"
        "- `qor/references/doctrine-new-thing.md` - NEW. The doctrine this phase adds.\n",
    )

    warnings = pgl.check_plan(plan, tmp_path)

    assert "reference-path-missing" not in _kinds(warnings)


def test_placeholder_reference_is_skipped(tmp_path):
    """Matches how the skill-path sibling treats its own placeholders."""
    plan = _plan(
        tmp_path,
        "## Notes\n\n"
        "Cite a doctrine as qor/references/foo.md or qor/references/doctrine-foo.md.\n",
    )

    warnings = pgl.check_plan(plan, tmp_path)

    assert "reference-path-missing" not in _kinds(warnings)


def test_allow_marker_suppresses_and_requires_a_reason(tmp_path):
    """Tribunal ground V-1 (entry #715).

    A plan discussing a broken path is indistinguishable from one citing it. The
    marker is the exemption; an empty reason must not silence the control, which
    is what keeps it evidence rather than a mute button.
    """
    marked = _plan(
        tmp_path,
        "## Notes\n\nqor/references/doctrine-absent-thing.md "
        "<!-- grep-lint: ok=discussing-not-citing -->\n",
    )
    assert "reference-path-missing" not in _kinds(pgl.check_plan(marked, tmp_path))

    empty = _plan(
        tmp_path,
        "## Notes\n\nqor/references/doctrine-absent-thing.md <!-- grep-lint: ok= -->\n",
    )
    assert "reference-path-missing" in _kinds(pgl.check_plan(empty, tmp_path)), (
        "an empty reason must not suppress the finding"
    )


def test_live_plan_corpus_has_exactly_the_known_findings():
    """Anti-recurrence binding over all 277 plan documents.

    Two genuine broken citations exist and are left as historical record; a
    future doctrine rename that orphans another citation makes this fail.
    """
    found: dict[str, list[str]] = {}
    for plan in sorted((REPO / "docs").glob("plan-*.md")):
        hits = [
            w.citation
            for w in pgl.check_plan(plan, REPO)
            if w.kind == "reference-path-missing"
        ]
        if hits:
            found[plan.name] = sorted(hits)

    assert found == {
        "plan-qor-phase244-qor-harden.md": [
            "qor/references/doctrine-implementation-quality.md"
        ],
        "plan-qor-phase28-documentation-integrity.md": ["qor/references/README.md"],
    }, found
