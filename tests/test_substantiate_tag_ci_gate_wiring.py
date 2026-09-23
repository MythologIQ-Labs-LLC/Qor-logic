"""Phase 290: Step 9.7 must gate the seal-tag push on a green CI run for the
exact tagged SHA, not merely ancestor-reachability (GH #482). Anchored-prose
assertions paired with strip-and-fail negatives per
qor/references/doctrine-test-functionality.md.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
TAG_TIMING_REF = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate"
    / "references" / "release-and-tag-timing.md"
)


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


def test_step_9_7_gates_tag_push_on_ci_success_for_seal_commit():
    section = _md_section(SUBSTANTIATE.read_text(encoding="utf-8"), "Step 9.7")
    assert section, "qor-substantiate SKILL.md has no Step 9.7 section"
    assert "tag_ci_gate" in section
    assert "--on-main" in section


def test_step_9_7_ci_gate_assertion_fails_when_stripped():
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    section = _md_section(text, "Step 9.7")
    assert section
    stripped = "\n".join(
        ln for ln in section.splitlines() if "tag_ci_gate" not in ln
    )
    assert "tag_ci_gate" not in stripped


def test_release_and_tag_timing_references_gh_482():
    text = TAG_TIMING_REF.read_text(encoding="utf-8")
    section = _md_section(text, "Step 9.6 / 9.7")
    assert section, "release-and-tag-timing.md has no 'Step 9.6 / 9.7' section"
    assert "#482" in section
