"""CHANGELOG stamp primitive.

Renames the ``## [Unreleased]`` section to ``## [X.Y.Z] - YYYY-MM-DD`` on
seal and inserts a fresh empty ``## [Unreleased]`` above it. Authors populate
``Unreleased`` during implementation; ``/qor-substantiate`` Step 7.6 calls
``apply_stamp`` after the version bump.

Pure: ``stamp_unreleased`` returns a new string with no I/O. ``apply_stamp``
writes atomically (temp-file + ``os.replace``).
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path


_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_UNRELEASED = "## [Unreleased]"
_FRESH_UNRELEASED = "## [Unreleased]\n\n"


def _validate_version(version: str) -> None:
    if not _SEMVER.match(version):
        raise ValueError(f"invalid SemVer version: {version!r}")


def _validate_date(date: str) -> None:
    if not _DATE.match(date):
        raise ValueError(f"invalid date (expected YYYY-MM-DD): {date!r}")


def _find_next_version_header(text: str, after: int) -> int:
    """Return the index of the next `## [X.Y.Z] -` header after ``after``,
    or ``len(text)`` if none."""
    match = re.search(r"^## \[[0-9]+\.[0-9]+\.[0-9]+\] -", text[after:], re.MULTILINE)
    return after + match.start() if match else len(text)


def _extract_unreleased_body(text: str) -> tuple[int, int, str]:
    """Return (start, end, body) for the Unreleased section."""
    start = text.find(_UNRELEASED)
    if start < 0:
        raise ValueError(f"missing {_UNRELEASED!r} header")
    body_start = start + len(_UNRELEASED)
    body_end = _find_next_version_header(text, body_start)
    return start, body_end, text[body_start:body_end]


def stamp_unreleased(text: str, version: str, date: str) -> str:
    """Rename Unreleased to [version] - date and insert a fresh Unreleased."""
    _validate_version(version)
    _validate_date(date)
    if f"## [{version}]" in text:
        raise ValueError(f"version [{version}] already present in changelog")
    start, body_end, body = _extract_unreleased_body(text)
    if not any(ln.strip().startswith("- ") for ln in body.splitlines()):
        raise ValueError("Unreleased section is empty (no bullets); refusing to stamp")
    new_section = f"{_FRESH_UNRELEASED}## [{version}] - {date}{body.rstrip()}\n\n"
    return text[:start] + new_section + text[body_end:]


def apply_stamp(path: Path | str, version: str, date: str, dry_run: bool = False) -> Path:
    """Read ``path``, stamp it, write atomically. Returns the path.

    With dry_run (Phase 167; GH #250) all validation still runs and raises
    identically; only the write is suppressed, with a '[dry]' preview line.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    stamped = stamp_unreleased(p.read_text(encoding="utf-8"), version, date)
    if dry_run:
        print(f"[dry] would stamp {p} version={version} date={date}")
        return p
    tmp_fd, tmp_name = tempfile.mkstemp(dir=p.parent, prefix=p.name, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            fh.write(stamped)
        os.replace(tmp_name, p)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return p
