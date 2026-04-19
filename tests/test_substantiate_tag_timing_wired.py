"""Rule 4 structural lint: verify /qor-substantiate SKILL.md wires the
seal-tag creation AFTER the seal commit (Phase 33).

These tests check the skill prose directly, without executing it, to
prevent regression to the Phase 13 timing bug.
"""
from __future__ import annotations

import re
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parents[1] / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


_STEP_HEADER_RE = re.compile(r"^###\s+Step\s+([0-9]+(?:\.[0-9]+)+):", re.MULTILINE)


def _step_section(text: str, step_prefix: str) -> str:
    """Return the body of the section whose header starts with step_prefix.

    The body runs from the header to the next step header or end of file.
    """
    matches = list(_STEP_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        if m.group(1) == step_prefix:
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            return text[start:end]
    return ""


def test_skill_creates_tag_after_seal_commit():
    text = SKILL_PATH.read_text(encoding="utf-8")
    step_7_5 = _step_section(text, "7.5")
    assert "create_seal_tag(" not in step_7_5, (
        "Step 7.5 must not create the tag; tagging runs after the seal commit"
    )
    late_step = _step_section(text, "9.5.5")
    assert late_step, "Step 9.5.5 (post-commit tag wiring) is missing"
    assert "create_seal_tag(" in late_step


def test_skill_step_7_5_bumps_version_only():
    text = SKILL_PATH.read_text(encoding="utf-8")
    step = _step_section(text, "7.5")
    assert "bump_version(" in step
    assert "create_seal_tag(" not in step


def test_skill_step_9_5_5_captures_commit_and_tags():
    text = SKILL_PATH.read_text(encoding="utf-8")
    step = _step_section(text, "9.5.5")
    assert step, "Step 9.5.5 section missing"
    assert "git rev-parse HEAD" in step, (
        "Step 9.5.5 must capture the seal commit via `git rev-parse HEAD`"
    )
    assert re.search(r"create_seal_tag\([^)]*commit\s*=", step, re.DOTALL), (
        "Step 9.5.5 must invoke create_seal_tag with commit= keyword"
    )
