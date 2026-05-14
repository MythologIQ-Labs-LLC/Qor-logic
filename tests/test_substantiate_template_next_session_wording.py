"""Phase 65 (#57): substantiate template Next Session wording.

Locks the contract that the substantiate skill's "Next Session"
recommendation routes operators to /qor-ideate (concept) or /qor-plan
(implementation planning), NOT /qor-bootstrap (genesis only).

Acceptance question for each test: "If the unit's behavior were silently
broken but the artifact still existed, would this test fail?" - yes.
Reverting the template wording to the pre-Phase-65 phrasing fails the
first two tests; failing to regenerate dist variants fails the third.
"""
from __future__ import annotations

from pathlib import Path

import pytest

CANONICAL_TEMPLATE = Path(
    "qor/skills/governance/qor-substantiate/references/qor-substantiate-templates.md"
)
DIST_VARIANT_TEMPLATES = (
    Path("qor/dist/variants/claude/skills/qor-substantiate/references/qor-substantiate-templates.md"),
    Path("qor/dist/variants/codex/skills/qor-substantiate/references/qor-substantiate-templates.md"),
    Path("qor/dist/variants/kilo-code/skills/qor-substantiate/references/qor-substantiate-templates.md"),
    # Gemini emits a single qor-substantiate.toml command rather than a skill
    # directory with references/; it has no separate template file to verify.
)


def _next_session_lines(path: Path) -> list[str]:
    """Return all lines in ``path`` mentioning 'Next Session'.

    Filters to behavioral evidence: the test inspects the actual sentences
    the substantiate skill emits in its final report, not just whether
    /qor-ideate appears anywhere in the file.
    """
    text = path.read_text(encoding="utf-8")
    return [line for line in text.splitlines() if "Next Session" in line]


def test_canonical_template_recommends_ideate_for_new_concept():
    lines = _next_session_lines(CANONICAL_TEMPLATE)
    assert lines, f"no 'Next Session' line found in {CANONICAL_TEMPLATE}"
    matching = [ln for ln in lines if "/qor-ideate" in ln]
    assert matching, (
        f"Next Session line(s) must recommend /qor-ideate for new concepts; "
        f"got: {lines}"
    )


def test_canonical_template_does_not_misroute_to_bootstrap():
    lines = _next_session_lines(CANONICAL_TEMPLATE)
    misroutes = [ln for ln in lines if "/qor-bootstrap for new feature" in ln]
    assert not misroutes, (
        f"Next Session line must not misroute to '/qor-bootstrap for new "
        f"feature' (bootstrap is for genesis only; new feature work goes "
        f"through /qor-ideate or /qor-plan). Offending line(s): {misroutes}"
    )


@pytest.mark.parametrize("variant_path", DIST_VARIANT_TEMPLATES)
def test_dist_variants_propagate_template_fix(variant_path):
    assert variant_path.exists(), f"variant file missing: {variant_path}"
    lines = _next_session_lines(variant_path)
    assert lines, f"no 'Next Session' line in variant {variant_path}"
    matching = [ln for ln in lines if "/qor-ideate" in ln]
    assert matching, (
        f"variant {variant_path} must propagate /qor-ideate recommendation; "
        f"run `python -m qor.scripts.dist_compile`. Got: {lines}"
    )
