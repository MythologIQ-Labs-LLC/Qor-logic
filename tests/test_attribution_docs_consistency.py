"""Phase 45 Phase 2: drift guards between attribution helper and docs."""
from __future__ import annotations

from pathlib import Path

from qor.scripts import attribution

REPO = Path(__file__).resolve().parent.parent
ATTRIBUTION_MD = REPO / "ATTRIBUTION.md"
DOCTRINE_MD = REPO / "qor" / "references" / "doctrine-attribution.md"
CLAUDE_MD = REPO / "CLAUDE.md"


def test_root_attribution_md_contains_canonical_commit_trailer():
    trailer = attribution.commit_trailer(model="Claude Opus 4.7 (1M context)")
    assert trailer in ATTRIBUTION_MD.read_text(encoding="utf-8")


def test_root_attribution_md_contains_canonical_changelog_line():
    line = attribution.changelog_attribution_line()
    assert line in ATTRIBUTION_MD.read_text(encoding="utf-8")


def test_doctrine_file_contains_canonical_commit_trailer():
    trailer = attribution.commit_trailer(model="Claude Opus 4.7 (1M context)")
    assert trailer in DOCTRINE_MD.read_text(encoding="utf-8")


def test_claude_md_authority_line_links_doctrine_attribution():
    text = CLAUDE_MD.read_text(encoding="utf-8")
    assert "[attribution](qor/references/doctrine-attribution.md)" in text


def test_pr_footer_template_in_doctrine_uses_placeholders():
    text = DOCTRINE_MD.read_text(encoding="utf-8")
    assert "{defects_list}" in text
    assert "{comparison_doc_path}" in text
