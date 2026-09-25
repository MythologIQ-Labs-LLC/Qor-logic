#!/usr/bin/env python3
"""File-marker session carrier for the Qor gate chain.

session_id format: <YYYY-MM-DDTHHMM>-<6hex>  (e.g. 2026-04-15T1743-a3f9c2)
No colons — safe as a directory name on Windows.

- .qor/current_session holds the current id as a single line
- Regenerated when missing OR mtime older than 24h
- Atomic writes via os.replace (Windows-safe)
"""
from __future__ import annotations

import argparse
import os
import re
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from qor import workdir as _workdir

MARKER_PATH = _workdir.root() / ".qor" / "session" / "current"
SESSION_TTL = timedelta(hours=24)

SESSION_ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$")

# Path-safety validator (GAP-SEC-04/05/07): looser than SESSION_ID_PATTERN so
# legacy/operator session ids still pass, but rejects '/', '\\', and '.' so a
# session_id can never escape .qor/session/ when used as a path segment.
_SESSION_ID_SAFE = re.compile(r"^[\w\-T:]+$")


def validate_session_id(session_id: str) -> None:
    """Raise ``ValueError`` if ``session_id`` is path-unsafe (empty or contains
    anything outside ``[\\w\\-T:]`` -- i.e. any '/', '\\', or '.' traversal)."""
    if not session_id or not _SESSION_ID_SAFE.match(session_id):
        raise ValueError(f"invalid session_id (path-unsafe): {session_id!r}")


def generate_id(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    minute = now.strftime("%Y-%m-%dT%H%M")
    rand = secrets.token_hex(3)
    return f"{minute}-{rand}"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as tf:
        tf.write(content)
        tmp = tf.name
    os.replace(tmp, path)


#: GH #483: gate-phase artifact names checked by _has_unsealed_gate_artifacts.
#: Declared locally (not imported from gate_chain.CHAIN) because gate_chain.py
#: imports this module; importing back would be a cycle.
_GATE_PHASE_ARTIFACTS = ("research.json", "plan.json", "audit.json", "implement.json")
_SEAL_ARTIFACT = "substantiate.json"


def _marker_state(path: Path, now: datetime) -> str:
    """"absent", "stale", or "fresh" for the marker at ``path``.

    GH #483: these were collapsed into one boolean (fresh/not-fresh), so a
    marker whose content was correct but whose mtime alone aged past
    SESSION_TTL was indistinguishable from a marker that was never written.
    """
    if not path.exists():
        return "absent"
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return "fresh" if (now - mtime) < SESSION_TTL else "stale"


def _has_unsealed_gate_artifacts(session_id: str) -> bool:
    """True if this session's gate dir holds phase work and no seal yet.

    GH #483: a stale-but-valid marker naming a session with live, unsealed
    gate artifacts should not be silently rotated out from under them.
    """
    sess_dir = _workdir.gate_dir() / session_id
    if not sess_dir.is_dir() or (sess_dir / _SEAL_ARTIFACT).exists():
        return False
    return any((sess_dir / name).exists() for name in _GATE_PHASE_ARTIFACTS)


def _recoverable_stale_id(marker: Path) -> str | None:
    """The marker's session id, if stale but still naming unsealed live work."""
    content = marker.read_text(encoding="utf-8").strip()
    if not SESSION_ID_PATTERN.match(content):
        return None
    return content if _has_unsealed_gate_artifacts(content) else None


def get_or_create(marker: Path | None = None, now: datetime | None = None) -> str:
    if marker is None:
        marker = MARKER_PATH
    now = now or datetime.now(timezone.utc)
    state = _marker_state(marker, now)
    if state == "fresh":
        content = marker.read_text(encoding="utf-8").strip()
        if SESSION_ID_PATTERN.match(content):
            return content
    elif state == "stale":
        recovered = _recoverable_stale_id(marker)
        if recovered is not None:
            _atomic_write(marker, recovered + "\n")
            return recovered
    new_id = generate_id(now)
    _atomic_write(marker, new_id + "\n")
    return new_id


def current(marker: Path | None = None, now: datetime | None = None) -> str | None:
    if marker is None:
        marker = MARKER_PATH
    now = now or datetime.now(timezone.utc)
    state = _marker_state(marker, now)
    if state == "absent":
        return None
    content = marker.read_text(encoding="utf-8").strip()
    if not SESSION_ID_PATTERN.match(content):
        return None
    if state == "fresh":
        return content
    return content if _has_unsealed_gate_artifacts(content) else None


def end_session(marker: Path | None = None) -> None:
    if marker is None:
        marker = MARKER_PATH
    if marker.exists():
        marker.unlink()


def rotate(now: datetime | None = None) -> str:
    """Write a fresh session_id to MARKER_PATH and return it.

    Used by /qor-substantiate Step Z to close the session-carry-over gap
    that let prior phases' gate artifacts overwrite each other. The previous
    session's .qor/gates/<old_sid>/ directory is preserved; operators prune
    manually.
    """
    new_id = generate_id(now)
    _atomic_write(MARKER_PATH, new_id + "\n")
    return new_id


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("current", help="Print current session id or 'none'")
    sub.add_parser("new", help="Get or create session id")
    sub.add_parser("end", help="End session (remove marker)")
    args = ap.parse_args()

    if args.cmd == "new":
        print(get_or_create())
    elif args.cmd == "current":
        sid = current()
        print(sid if sid else "none")
    elif args.cmd == "end":
        end_session()
        print("Session ended.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
