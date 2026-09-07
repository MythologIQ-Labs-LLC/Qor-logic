#!/usr/bin/env python3
r"""Assert a plan's fenced code block matches the source it describes.

Phase 268. The seal content-hashes a plan as the description of the work, so a
code block that has drifted from the shipped source seals a description of
something that does not exist. This phase shipped such a drift: the plan's
`_OWNER_PREFIX_RE` read `[\/]` where the source read `[\\/]`, a one-character
difference that disables the backslash guard on a fail-closed detector.

It was missed by a check asserting the IDENTIFIER appeared in both places, which
is true whichever definition is present. This compares bodies instead: every
non-elided line of the block must appear in the source, whitespace-normalised.

Run it at the seal, not only when the block is written -- both sides remain
editable until the commit, and "these two drifted and nobody looked" is the
whole class it exists to catch.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_FENCE_RE = re.compile(r"```python\n(.*?)```", re.S)
_ELISION = ("...", "findings.append(...)")


def drifted(plan_text: str, source_text: str, section: str) -> list[str]:
    """Return block lines absent from the source. Empty means parity."""
    start = plan_text.find(section)
    if start == -1:
        raise ValueError(f"section not found in plan: {section!r}")
    fence = _FENCE_RE.search(plan_text, start)
    if fence is None:
        raise ValueError(f"no python fence after {section!r}")
    flat = re.sub(r"\s+", " ", source_text)
    missing = []
    for raw in fence.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line in _ELISION:
            continue
        if re.sub(r"\s+", " ", line) not in flat:
            missing.append(line)
    return missing


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--section", default="### D1:")
    args = ap.parse_args(argv)
    missing = drifted(
        args.plan.read_text(encoding="utf-8"),
        args.source.read_text(encoding="utf-8"),
        args.section,
    )
    if missing:
        print(f"FAIL: {args.plan} {args.section} has drifted from {args.source}:")
        for line in missing:
            print(f"  absent from source: {line}")
        return 1
    print(f"OK: {args.section} matches {args.source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
