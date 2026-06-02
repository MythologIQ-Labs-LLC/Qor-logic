"""Phase 84: wiring tests for /qor-audit Step 0.3 pre-audit readiness short-circuit (GH #81).

Anchored to the section header, paired with a strip-and-fail negative so the
assertion cannot decay into a presence-only check that a stray keyword would
satisfy. Per qor/references/doctrine-test-functionality.md.
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
    body = []
    for line in lines[start + 1:]:
        if line.startswith("### "):
            break
        body.append(line)
    return "\n".join(body)


def test_step_0_3_invokes_iteration_lint_and_aborts():
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 0\.3")
    assert section, "qor-audit SKILL.md has no '### Step 0.3' section"
    assert ("qor.scripts.plan_iteration_status_lint" in section or "qor-logic scripts plan_iteration_status_lint" in section)
    assert "|| ABORT" in section
    assert "do NOT emit an audit gate artifact" in section


def test_step_0_3_assertion_fails_when_section_removed():
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 0\.3")
    assert section
    stripped = text.replace(section, "")
    section_after = _section(stripped, r"Step 0\.3")
    assert ("qor.scripts.plan_iteration_status_lint" not in section_after and "qor-logic scripts plan_iteration_status_lint" not in section_after)
