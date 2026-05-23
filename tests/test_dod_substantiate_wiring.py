"""Phase 92: wiring tests for /qor-substantiate Step 4.6.7 dod_check (GH #86).

Anchored to the Step 4.6.7 section header in qor-substantiate SKILL.md,
paired with a strip-and-fail negative and a positional guard. Mirrors
the Phase 84 / Phase 87 / Phase 89 wiring-test convention.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)


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


def test_step_4_6_7_invokes_dod_check():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 4\.6\.7")
    assert section, "qor-substantiate SKILL.md has no '### Step 4.6.7' section"
    assert "qor.scripts.dod_check" in section, (
        "Step 4.6.7 missing the qor.scripts.dod_check invocation"
    )
    # WARN-only contract: same `|| true` guard convention as Step 0.6 lints.
    assert "|| true" in section, (
        "Step 4.6.7 missing the '|| true' WARN-only guard convention"
    )


def test_step_4_6_7_section_removed_breaks_assertion():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 4\.6\.7")
    assert section, "precondition: Step 4.6.7 section must exist"
    stripped = text.replace(section, "")
    section_after = _section(stripped, r"Step 4\.6\.7")
    assert "qor.scripts.dod_check" not in section_after


def test_step_4_6_7_positioned_between_4_6_6_and_4_7():
    """Step 4.6.7 must appear AFTER Step 4.6.6 (procedural-fidelity) and
    BEFORE Step 4.7 (documentation integrity) in document order. Guards
    against future renumbering that breaks the substantiate sequence."""
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")

    def _heading_pos(pattern: str) -> int:
        m = re.search(pattern, text, re.MULTILINE)
        assert m, f"heading not found: {pattern}"
        return m.start()

    pos_4_6_6 = _heading_pos(r"^### Step 4\.6\.6\b")
    pos_4_6_7 = _heading_pos(r"^### Step 4\.6\.7\b")
    pos_4_7 = _heading_pos(r"^### Step 4\.7\b")
    assert pos_4_6_6 < pos_4_6_7 < pos_4_7, (
        f"Step 4.6.7 must be ordered between 4.6.6 and 4.7; "
        f"positions: 4.6.6={pos_4_6_6}, 4.6.7={pos_4_6_7}, 4.7={pos_4_7}"
    )
