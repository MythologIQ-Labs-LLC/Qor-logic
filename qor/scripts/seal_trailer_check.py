"""Seal-commit trailer guard: verify a commit carries the full canonical trailer (Phase 85).

Reads a commit message via ``git log -1 --format=%B <commit>`` (list-form
argv, no shell) and verifies it contains the full canonical attribution
trailer per ``qor.scripts.attribution.message_has_full_trailer``. Wired into
``/qor-substantiate`` Step 9.5.4 as an ABORT gate after the seal commit.

Closes GH #96 FIX A: the phase 82/83 seal commits were created with only the
compact ``Co-Authored-By:`` line, missing the ``Authored via [Qor-logic SDLC]``
line. This guard makes that omission unrepeatable.

Security: ``--commit`` is rejected when it starts with ``-`` (git would parse
a leading-dash value as an option). List-form argv closes shell injection.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from qor.scripts.attribution import message_has_full_trailer


def commit_message(commit: str, repo_root: Path | None = None) -> str:
    """Return the full message body of ``commit``. List-form argv; no shell."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B", commit],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=repo_root,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git log failed for commit {commit!r}: {result.stderr.strip()}"
        )
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.seal_trailer_check")
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.commit.startswith("-"):
        print(
            "ERROR [seal-trailer-check] --commit value must not start with '-'",
            file=sys.stderr,
        )
        return 1
    try:
        message = commit_message(args.commit, args.repo_root)
    except RuntimeError as exc:
        print(f"ERROR [seal-trailer-check] {exc}", file=sys.stderr)
        return 1
    if message_has_full_trailer(message):
        return 0
    print(
        f"ERROR [seal-trailer-check] commit {args.commit} is missing the full "
        f"canonical trailer. A seal commit MUST contain both the "
        f"'Authored via [Qor-logic SDLC]' line and a 'Co-Authored-By:' line "
        f"(the full qor.scripts.attribution.commit_trailer() output). Amend "
        f"the seal commit with the full trailer, then re-run /qor-substantiate.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
