"""Phase 89: wiring tests for /qor-audit Step 0.6 ci_coverage_lint (GH #91).

Anchored to the Step 0.6 section header in qor-audit SKILL.md, paired with
a strip-and-fail negative per qor/references/doctrine-test-functionality.md
and the established Phase 84 / Phase 87 / Phase 88 wiring-test pattern.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"


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


def test_step_0_6_invokes_ci_coverage_lint():
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 0\.6")
    assert section, "qor-audit SKILL.md has no '### Step 0.6' section"
    assert "qor.scripts.ci_coverage_lint" in section, (
        "Step 0.6 missing the ci_coverage_lint module invocation"
    )
    # WARN-only contract: paired with the existing `|| true` guard form
    # used by the other Step 0.6 lints.
    assert "|| true" in section, (
        "Step 0.6 missing the '|| true' WARN-only guard convention"
    )


def test_step_0_6_assertion_fails_when_section_removed():
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 0\.6")
    assert section, "precondition: Step 0.6 section must exist for negative test"
    stripped = text.replace(section, "")
    section_after = _section(stripped, r"Step 0\.6")
    assert "qor.scripts.ci_coverage_lint" not in section_after
    assert "|| true" not in section_after
