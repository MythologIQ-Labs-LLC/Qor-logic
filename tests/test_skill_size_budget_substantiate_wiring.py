"""Phase 95: wiring tests for /qor-substantiate Step 4.6.9 (GH #92)."""
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


def test_step_4_6_9_invokes_skill_size_budget_lint():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 4\.6\.9")
    assert section
    assert "qor.scripts.skill_size_budget_lint" in section
    assert "|| true" in section


def test_step_4_6_9_section_removed_breaks_assertion():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    section = _section(text, r"Step 4\.6\.9")
    assert section
    stripped = text.replace(section, "")
    section_after = _section(stripped, r"Step 4\.6\.9")
    assert "qor.scripts.skill_size_budget_lint" not in section_after


def test_step_4_6_9_positioned_between_4_6_8_and_4_7():
    text = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")

    def _pos(pat: str) -> int:
        m = re.search(pat, text, re.MULTILINE)
        assert m, f"heading not found: {pat}"
        return m.start()

    pos_468 = _pos(r"^### Step 4\.6\.8\b")
    pos_469 = _pos(r"^### Step 4\.6\.9\b")
    pos_47 = _pos(r"^### Step 4\.7\b")
    assert pos_468 < pos_469 < pos_47, (
        f"Step 4.6.9 must be between 4.6.8 and 4.7; "
        f"positions: 4.6.8={pos_468} 4.6.9={pos_469} 4.7={pos_47}"
    )
