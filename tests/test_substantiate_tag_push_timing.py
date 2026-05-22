"""Phase 86: wiring tests for post-merge seal-tag push (GH #98).

The seal tag is CREATED at /qor-substantiate Step 9.5.5 (pre-merge) but must
be PUSHED only at Step 9.7 (post-merge), so release.yml's build-and-publish
guard does not fail on the seal PR. These anchored-prose assertions are each
paired with a strip-and-fail negative per qor/references/doctrine-test-functionality.md.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


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


def test_step_9_6_pushes_branch_only_not_tags():
    section = _md_section(SUBSTANTIATE.read_text(encoding="utf-8"), "Step 9.6")
    assert section, "qor-substantiate SKILL.md has no Step 9.6 section"
    assert "--tags" not in section, (
        "Step 9.6 must not push the tag with the branch (--tags)"
    )


def test_step_9_6_defers_tag_push_to_post_merge():
    section = _md_section(SUBSTANTIATE.read_text(encoding="utf-8"), "Step 9.6")
    assert section
    assert "Step 9.7" in section
    assert "branch only" in section.lower()


def test_step_9_6_defer_assertion_fails_when_directive_stripped():
    section = _md_section(SUBSTANTIATE.read_text(encoding="utf-8"), "Step 9.6")
    assert section
    stripped = "\n".join(
        ln for ln in section.splitlines() if "Step 9.7" not in ln
    )
    assert "Step 9.7" not in stripped


def test_step_9_7_pushes_tag_gated_on_origin_main_reachability():
    section = _md_section(SUBSTANTIATE.read_text(encoding="utf-8"), "Step 9.7")
    assert section, "qor-substantiate SKILL.md has no Step 9.7 section"
    assert "git push origin" in section and "SEAL_TAG" in section
    assert "merge-base --is-ancestor" in section
    assert "origin/main" in section


def test_step_9_7_assertion_fails_when_section_removed():
    text = SUBSTANTIATE.read_text(encoding="utf-8")
    section = _md_section(text, "Step 9.7")
    assert section
    stripped = text.replace(section, "")
    assert not _md_section(stripped, "Step 9.7").strip()
