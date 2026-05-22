"""Phase 88: wiring tests for /qor-research Step 2.5 issue-state pre-check (GH #80).

Anchored to the section header, paired with a strip-and-fail negative so the
assertion cannot decay into a presence-only check that a stray keyword would
satisfy. Per qor/references/doctrine-test-functionality.md and the
established Phase 84 wiring-test pattern at
tests/test_audit_skill_iteration_lint_wiring.py.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESEARCH_SKILL = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-research" / "SKILL.md"


def _section(text: str, header_pattern: str) -> str:
    """Body of the first '### ' section whose header matches header_pattern,
    up to the next '### ' header."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("### ") and re.search(header_pattern, line):
            start = i
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start + 1:]:
        if line.startswith("### "):
            break
        body.append(line)
    return "\n".join(body)


def test_step_2_5_anchored_in_qor_research_skill():
    text = RESEARCH_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 2\.5")
    assert section, "qor-research SKILL.md has no '### Step 2.5' section"
    # First gh pr list invocation: literal '#<N>' search form.
    assert 'gh pr list --state all --search "#' in section, (
        "Step 2.5 missing the literal '#<N>' gh pr list invocation"
    )
    # Second gh pr list invocation: body-search form.
    assert "in:body" in section, (
        "Step 2.5 missing the 'in:body' body-search gh pr list invocation"
    )
    # Operative directive on hit: surface a MERGED PR to the operator.
    assert "MERGED" in section, "Step 2.5 missing 'MERGED' operative term"
    assert "surface" in section, "Step 2.5 missing 'surface' operative verb"


def test_step_2_5_section_removed_breaks_anchored_assertions():
    text = RESEARCH_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 2\.5")
    assert section, "precondition: Step 2.5 section must exist for negative test"
    stripped = text.replace(section, "")
    section_after = _section(stripped, r"Step 2\.5")
    # After removal, none of the operative substrings should remain in the
    # isolated section (the section is empty / non-existent).
    assert 'gh pr list --state all --search "#' not in section_after
    assert "in:body" not in section_after
    # MERGED + surface are operative-verb anchors specific to Step 2.5; their
    # absence is also load-bearing.
    assert "MERGED" not in section_after
    assert "surface" not in section_after


def test_step_2_5_scope_conditional_language_present():
    """Guard: Step 2.5 must be scope-conditional (only fires for issue targets).

    Without the scope-narrowing language the prose would direct the skill to
    run `gh pr list` on every research target — including API surfaces and
    dependencies where no issue number applies — burning gh API calls and
    surfacing spurious PR matches.
    """
    text = RESEARCH_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 2\.5")
    assert section, "qor-research SKILL.md has no '### Step 2.5' section"
    assert "existing GH issue" in section, (
        "Step 2.5 missing the 'existing GH issue' scope-conditional language; "
        "prose risks unconditional firing on non-issue research targets."
    )
