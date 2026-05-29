"""Authoritative active-phase reporter (Phase 111, #138 Layer 2).

Reports the true active SDLC phase from the newest-mtime gate artifact under
``.qor/gates/<session_id>/`` -- a non-leaking source a status surface can read
instead of the ambient ``$QOR_SKILL_ACTIVE`` env var (which can go stale on
Windows/Git Bash inline shell prefixes).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qor.scripts import session as _session


def latest_gate_phase(session_id: str, repo_root: Path = Path(".")) -> str | None:
    """Return the ``phase`` field of the newest-mtime ``*.json`` gate artifact in
    the session's gate dir, or None when the dir is empty/absent/unreadable.
    ``audit_history.jsonl`` is excluded (not a ``*.json`` singleton)."""
    gate_dir = Path(repo_root) / ".qor" / "gates" / session_id
    if not gate_dir.is_dir():
        return None
    candidates = list(gate_dir.glob("*.json"))
    if not candidates:
        return None
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        return json.loads(newest.read_text(encoding="utf-8")).get("phase")
    except (OSError, json.JSONDecodeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.active_phase")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--session", default=None, help="session id (default: current)")
    args = parser.parse_args(argv)
    sid = args.session or _session.current()
    phase = latest_gate_phase(sid, Path(args.repo_root)) if sid else None
    print(phase if phase else "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
