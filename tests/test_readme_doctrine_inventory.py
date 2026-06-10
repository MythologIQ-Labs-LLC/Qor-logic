"""Phase 160: README doctrine-inventory currency enforcement.

`badge_currency` checks the Doctrines badge NUMBER against the file count but
never inspects the README's prose doctrine table, so the table can drift (Phase
158 shipped `doctrine-provenance-binding.md` without a README row, and the badge
stayed coincidentally correct). These tests pin the README doctrine inventory to
the on-disk `qor/references/doctrine-*.md` corpus, bidirectionally.

Behavioral: each test parses the README + globs the corpus and asserts on the
computed set relationship, not on artifact presence.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_DOCTRINE_LINK_RE = re.compile(r"doctrine-([a-z0-9-]+)\.md")


def _doctrine_files() -> set[str]:
    return {
        p.name[len("doctrine-"):-len(".md")]
        for p in (REPO_ROOT / "qor" / "references").glob("doctrine-*.md")
    }


def _readme_listed() -> set[str]:
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    return set(_DOCTRINE_LINK_RE.findall(text))


def test_readme_lists_every_doctrine_file():
    files = _doctrine_files()
    listed = _readme_listed()
    missing = files - listed
    assert missing == set(), (
        f"README does not reference these doctrine files: {sorted(missing)}"
    )


def test_readme_doctrine_table_has_no_phantom_entries():
    files = _doctrine_files()
    listed = _readme_listed()
    phantom = listed - files
    assert phantom == set(), (
        f"README references doctrines with no file on disk: {sorted(phantom)}"
    )
