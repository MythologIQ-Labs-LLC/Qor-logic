"""Phase 54: subagent tool-scope advisory frontmatter lint.

Walks the six SDLC + governance skills and asserts each YAML frontmatter
declares `permitted_tools:` and `permitted_subagents:` keys with list
values. Tolerant in this phase (warns on absence; does not fail). Phase 55
will promote to ABORT once Cedar-based admission enforcement lands.
"""
from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"

_GATE_SKILLS = (
    "qor/skills/sdlc/qor-research/SKILL.md",
    "qor/skills/sdlc/qor-plan/SKILL.md",
    "qor/skills/sdlc/qor-implement/SKILL.md",
    "qor/skills/governance/qor-audit/SKILL.md",
    "qor/skills/governance/qor-substantiate/SKILL.md",
    "qor/skills/governance/qor-validate/SKILL.md",
)


def _frontmatter(path: Path) -> str:
    body = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
    assert match, f"missing YAML frontmatter in {path}"
    return match.group(1)


def _has_list_key(frontmatter: str, key: str) -> bool:
    """Detect ``key: [...]`` (inline list) or ``key:\\n  - item`` block-list shapes."""
    inline_pattern = re.compile(rf"^{re.escape(key)}\s*:\s*\[", re.MULTILINE)
    block_pattern = re.compile(rf"^{re.escape(key)}\s*:\s*\n\s*-\s+", re.MULTILINE)
    return bool(inline_pattern.search(frontmatter)) or bool(block_pattern.search(frontmatter))


def test_six_gate_skills_declare_permitted_tools():
    violators: list[str] = []
    for rel in _GATE_SKILLS:
        path = REPO_ROOT / rel
        fm = _frontmatter(path)
        if not _has_list_key(fm, "permitted_tools"):
            violators.append(f"{rel}: missing permitted_tools (list)")
        if not _has_list_key(fm, "permitted_subagents"):
            violators.append(f"{rel}: missing permitted_subagents (list)")
    assert not violators, (
        "six gate skills must declare permitted_tools + permitted_subagents "
        f"frontmatter keys with list values; violators: {violators}"
    )


def test_permitted_tools_lint_warns_on_synthetic_absent_skill(tmp_path, capsys):
    """Negative-path: a fixture skill missing the keys produces detectable absence."""
    skill = tmp_path / "fake_skill.md"
    skill.write_text(textwrap.dedent("""
        ---
        name: qor-fake
        phase: fake
        ---
        # body
    """).strip(), encoding="utf-8")

    fm = _frontmatter(skill)
    assert not _has_list_key(fm, "permitted_tools")
    assert not _has_list_key(fm, "permitted_subagents")


def test_permitted_tools_lint_accepts_inline_list_shape(tmp_path):
    skill = tmp_path / "inline_list.md"
    skill.write_text(textwrap.dedent("""
        ---
        name: qor-foo
        permitted_tools: [Read, Grep]
        permitted_subagents: []
        ---
    """).strip(), encoding="utf-8")
    fm = _frontmatter(skill)
    assert _has_list_key(fm, "permitted_tools")
    assert _has_list_key(fm, "permitted_subagents")


def test_permitted_tools_lint_accepts_block_list_shape(tmp_path):
    skill = tmp_path / "block_list.md"
    skill.write_text(textwrap.dedent("""
        ---
        name: qor-foo
        permitted_tools:
          - Read
          - Grep
        permitted_subagents:
          - Explore
        ---
    """).strip(), encoding="utf-8")
    fm = _frontmatter(skill)
    assert _has_list_key(fm, "permitted_tools")
    assert _has_list_key(fm, "permitted_subagents")
