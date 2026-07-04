"""Operator-facing session inspection/rotation with dry-run (Phase 167; GH #250).

The internal ``session.rotate()`` is called by gate/orchestration automation
where a dry-run signal has no meaning, so it stays mutation-only. This module
gives OPERATORS the safe surface: ``current`` prints the active session id,
``rotate --dry-run`` previews the rotation (old -> new-id shape) without
touching ``.qor/session/current``.
"""
from __future__ import annotations

import argparse

from qor.scripts import session


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("current", help="print the active session id (or 'none')")
    sp_rotate = sub.add_parser("rotate", help="rotate to a fresh session id")
    sp_rotate.add_argument("--dry-run", action="store_true",
                           help="preview the rotation; write nothing")
    args = ap.parse_args(argv)
    if args.command == "current":
        print(session.current() or "none")
        return 0
    old = session.current() or "none"
    if args.dry_run:
        preview = session.generate_id()
        print(f"[dry] would rotate session: {old} -> {preview} (id regenerated on wet run)")
        return 0
    new_id = session.rotate()
    print(f"rotated session: {old} -> {new_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
