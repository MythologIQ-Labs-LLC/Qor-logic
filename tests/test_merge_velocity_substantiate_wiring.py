"""Phase 93: wiring tests for /qor-substantiate Step 4.6.8 (GH #89).

Anchored + strip-and-fail + positional guard per the Phase 84/87/89/91/92
wiring-test convention.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)


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


def test_step_4_6_8_invokes_merge_velocity_check():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 4\.6\.8")
    assert section, "qor-substantiate SKILL.md has no '### Step 4.6.8' section"
    assert "qor.scripts.merge_velocity_check" in section, (
        "Step 4.6.8 missing the merge_velocity_check invocation"
    )
    assert "|| true" in section, (
        "Step 4.6.8 missing '|| true' WARN-only contract"
    )


def test_step_4_6_8_section_removed_breaks_assertion():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 4\.6\.8")
    assert section
    stripped = text.replace(section, "")
    section_after = _section(stripped, r"Step 4\.6\.8")
    assert "qor.scripts.merge_velocity_check" not in section_after


def test_step_4_6_8_positioned_between_4_6_7_and_4_7():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")

    def _pos(pat: str) -> int:
        m = re.search(pat, text, re.MULTILINE)
        assert m, f"heading not found: {pat}"
        return m.start()

    pos_467 = _pos(r"^### Step 4\.6\.7\b")
    pos_468 = _pos(r"^### Step 4\.6\.8\b")
    pos_47 = _pos(r"^### Step 4\.7\b")
    assert pos_467 < pos_468 < pos_47, (
        f"Step 4.6.8 must be between 4.6.7 and 4.7; positions: "
        f"4.6.7={pos_467} 4.6.8={pos_468} 4.7={pos_47}"
    )
