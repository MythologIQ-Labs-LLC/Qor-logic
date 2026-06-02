"""Pluggable changelog backends (Phase 133; GH #163).

Detects the changelog format and stamps a release section accordingly:
keepachangelog (a `## [Unreleased]` section present) delegates to the existing
`changelog_stamp.apply_stamp`; otherwise a generic `prepend` backend inserts a
`## v<version> - <date>` section near the top. Closes #38's deferred Option 2
changelog half.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from qor.scripts import changelog_stamp

_UNRELEASED_RE = re.compile(r"^##\s*\[Unreleased\]", re.MULTILINE | re.IGNORECASE)
_FIRST_HEADING_RE = re.compile(r"^#\s+.*$", re.MULTILINE)


def detect_changelog_format(text: str) -> str:
    return "keepachangelog" if _UNRELEASED_RE.search(text) else "prepend"


def _prepend(text: str, version: str, date: str) -> str:
    section = f"## v{version} - {date}\n\n"
    m = _FIRST_HEADING_RE.search(text)
    if m:
        insert_at = m.end()
        # skip the blank line(s) right after the title
        rest = text[insert_at:]
        lead = len(rest) - len(rest.lstrip("\n"))
        pos = insert_at + lead
        return text[:pos] + ("\n" if lead == 0 else "") + section + text[pos:]
    return section + text


def stamp(path: Path, version: str, date: str) -> str:
    """Stamp the changelog with a release section. Returns the format used
    ('keepachangelog' | 'prepend')."""
    text = path.read_text(encoding="utf-8")
    fmt = detect_changelog_format(text)
    if fmt == "keepachangelog":
        changelog_stamp.apply_stamp(path, version, date)
        return "keepachangelog"
    new_text = _prepend(text, version, date)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    os.replace(tmp, path)
    return "prepend"
