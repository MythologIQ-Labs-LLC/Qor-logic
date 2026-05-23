"""Phase 94: wiring tests for /qor-audit Step 0.6 workspace_fragility_check (GH #90)."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"


def _section(text: str, header_pattern: str) -> str:
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


def test_step_0_6_invokes_workspace_fragility_check():
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 0\.6")
    assert section
    assert "qor.scripts.workspace_fragility_check" in section, (
        "Step 0.6 missing workspace_fragility_check invocation"
    )
    assert "|| true" in section, "Step 0.6 missing WARN-only guard"


def test_step_0_6_section_removed_breaks_assertion():
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 0\.6")
    assert section
    stripped = text.replace(section, "")
    section_after = _section(stripped, r"Step 0\.6")
    assert "qor.scripts.workspace_fragility_check" not in section_after


def test_step_0_6_fragility_check_appears_after_ci_coverage_lint():
    """Positional guard: workspace_fragility_check must be the SIXTH lint,
    after the existing ci_coverage_lint line (Phase 89 wiring)."""
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 0\.6")
    ci_idx = section.find("ci_coverage_lint")
    fragility_idx = section.find("workspace_fragility_check")
    assert ci_idx >= 0, "Step 0.6 missing ci_coverage_lint (precondition)"
    assert fragility_idx >= 0, "Step 0.6 missing workspace_fragility_check"
    assert ci_idx < fragility_idx, (
        f"workspace_fragility_check must appear AFTER ci_coverage_lint; "
        f"got ci_coverage={ci_idx} fragility={fragility_idx}"
    )
