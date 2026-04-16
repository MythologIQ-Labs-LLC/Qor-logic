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
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from qor import workdir as _workdir

MARKER_PATH = _workdir.root() / ".qor" / "current_session"
SESSION_TTL = timedelta(hours=24)

SESSION_ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{4}-[0-9a-f]{6}$")


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


def _marker_fresh(path: Path, now: datetime) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return (now - mtime) < SESSION_TTL


def get_or_create(marker: Path | None = None, now: datetime | None = None) -> str:
    if marker is None:
        marker = MARKER_PATH
    now = now or datetime.now(timezone.utc)
    if _marker_fresh(marker, now):
        content = marker.read_text(encoding="utf-8").strip()
        if SESSION_ID_PATTERN.match(content):
            return content
    new_id = generate_id(now)
    _atomic_write(marker, new_id + "\n")
    return new_id


def current(marker: Path | None = None, now: datetime | None = None) -> str | None:
    if marker is None:
        marker = MARKER_PATH
    now = now or datetime.now(timezone.utc)
    if not _marker_fresh(marker, now):
        return None
    content = marker.read_text(encoding="utf-8").strip()
    return content if SESSION_ID_PATTERN.match(content) else None


def end_session(marker: Path | None = None) -> None:
    if marker is None:
        marker = MARKER_PATH
    if marker.exists():
        marker.unlink()


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
