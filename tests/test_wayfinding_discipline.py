"""Phase 30 Phase 2: CLAUDE.md and README.md wayfinding discipline.

Closes GAP-REPO-05: CLAUDE.md bare backticks -> markdown links; doctrines
linked from the README so they stop being orphan from the entry point.
"""
from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
README_MD = REPO_ROOT / "README.md"


def test_claude_md_uses_markdown_links_for_doctrines():
    """Bare-backtick paths like `qor/references/doctrine-X.md` are discouraged
    outside fenced code blocks; use [name](path) markdown links instead."""
    body = CLAUDE_MD.read_text(encoding="utf-8")
    # Strip fenced code blocks first -- their backticks are legitimate.
    stripped = re.sub(r"```[\s\S]*?```", "", body)
    # Find bare-backtick doctrine references: `qor/references/doctrine-*.md`
    pattern = re.compile(r"`qor/references/doctrine-[^`]+?\.md`")
    bare = pattern.findall(stripped)
    assert not bare, (
        f"CLAUDE.md has bare-backtick doctrine paths (use markdown links): {bare}"
    )


def test_readme_lists_at_least_ten_doctrines():
    body = README_MD.read_text(encoding="utf-8")
    # Count markdown links to qor/references/*.md (doctrines, patterns, ql, etc.)
    pattern = re.compile(r"\]\((?:\.\/)?qor/references/[^)]+?\.md\)")
    links = pattern.findall(body)
    assert len(links) >= 10, (
        f"README.md must link to >= 10 qor/references/ docs; found {len(links)}"
    )
