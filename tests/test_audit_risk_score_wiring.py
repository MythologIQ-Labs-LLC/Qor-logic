"""Phase 87: wiring tests for the /qor-audit Step 1 author-momentum auto-dispatch (GH #82).

Anchored to the Step 1 section, paired with a strip-and-fail negative per
qor/references/doctrine-test-functionality.md.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"


def _md_section(text: str, header_substr: str) -> str:
    """Body of the first '##'..'####' section whose header contains header_substr,
    up to the next header of equal-or-shallower depth. Lines inside ``` fenced
    blocks are not treated as headers."""
    lines = text.splitlines()
    start = None
    start_level = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m and header_substr in m.group(2):
            start = i
            start_level = len(m.group(1))
            break
    if start is None:
        return ""
    body = []
    in_fence = False
    for line in lines[start + 1:]:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            body.append(line)
            continue
        if not in_fence:
            m = re.match(r"^(#{2,4})\s+", line)
            if m and len(m.group(1)) <= start_level:
                break
        body.append(line)
    return "\n".join(body)


def test_step_1_invokes_audit_risk_score_and_mandates_option_b():
    section = _md_section(AUDIT_SKILL.read_text(encoding="utf-8"), "Step 1:")
    assert section, "qor-audit SKILL.md has no Step 1 section"
    assert ("qor.scripts.audit_risk_score" in section or "qor-logic scripts audit_risk_score" in section)
    assert "option_b_required" in section
    assert "mandatory" in section.lower() and "Option B" in section


def test_step_1_directive_fails_when_stripped():
    section = _md_section(AUDIT_SKILL.read_text(encoding="utf-8"), "Step 1:")
    assert section
    kept = "\n".join(
        ln for ln in section.splitlines() if "audit_risk_score" not in ln
    )
    assert "qor.scripts.audit_risk_score" not in kept and "qor-logic scripts audit_risk_score" not in kept
