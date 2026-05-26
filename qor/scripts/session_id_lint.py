"""Phase 106: WARN when the active session ID doesn't match SESSION_ID_PATTERN.

Wired into /qor-substantiate Step 4.6 (WARN-only). Catches the fall-through-to-
'default' pattern where intent_lock + procedural_fidelity events fragment under
the default session because the operator-supplied marker doesn't match the
canonical 6-hex slug format.

Non-blocking: always exits 0. The stderr WARN names the canonical pattern and
points operators at session.rotate() for compliant generation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qor.scripts.session import SESSION_ID_PATTERN


def lint(marker_path: Path) -> tuple[bool, str | None]:
    """Returns (conforming, message). Pure; one filesystem read."""
    if not marker_path.is_file():
        return True, None
    content = marker_path.read_text(encoding="utf-8").strip()
    if SESSION_ID_PATTERN.match(content):
        return True, None
    msg = (
        f"WARN: session ID {content!r} does not match SESSION_ID_PATTERN "
        f"{SESSION_ID_PATTERN.pattern!r}; intent_lock + procedural_fidelity "
        f"fall through to 'default'. Use session.rotate() to generate a compliant ID."
    )
    return False, msg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--marker", default=".qor/session/current")
    args = p.parse_args(argv)
    _, msg = lint(Path(args.marker))
    if msg:
        print(msg, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
