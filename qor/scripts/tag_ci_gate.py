#!/usr/bin/env python3
"""Phase 290: gate the /qor-substantiate Step 9.7 seal-tag push on a green CI
run for the exact tagged SHA, not merely ancestor-reachability from origin/main.

GH #482: a commit stacked on the phase branch after the seal commit (Step
9.5.5) moves the pushed branch head past the seal commit. Step 9.7's ancestor
check (`git merge-base --is-ancestor "$SEAL_COMMIT" origin/main`) still passes
once the branch merges, but GitHub only runs CI on pushed branch heads, so no
CI run for the seal commit's own SHA exists or ever will. `release.yml`'s
`release_ci_gate` (Phase 163) then refuses the publish in a separate, unread
workflow run. This module closes the gap at Step 9.7 by requiring both:
ancestor-reachability (the caller's own `git merge-base` result, passed in --
not re-run here) AND a green CI run for that exact SHA (delegated to the
already-tested `release_ci_gate.evaluate`).

Pure decision logic (`evaluate`) so it is unit-testable in-process; no network
or `gh` dependency lives here, matching `release_ci_gate`'s own split. Stdlib
only.
"""
from __future__ import annotations

import argparse
import json
import sys

from qor.scripts.release_ci_gate import GateResult, evaluate as ci_evaluate


def evaluate(ancestor_ok: bool, runs: object, head_sha: str) -> GateResult:
    """Ready to push the tag iff the seal commit is on origin/main AND has its
    own green CI run. `ancestor_ok` is the caller's `git merge-base
    --is-ancestor` result -- not recomputed here."""
    if not ancestor_ok:
        return GateResult(
            False,
            f"seal commit {head_sha[:8]}... not yet on origin/main; tag held local",
        )
    ci = ci_evaluate(runs, head_sha)
    if not ci.ok:
        return GateResult(
            False,
            f"seal commit {head_sha[:8]}... is on origin/main but has no green CI "
            f"run of its own ({ci.message}); a commit likely landed on the branch "
            "after the seal -- re-seal or trigger CI for this SHA before pushing "
            "the tag (GH #482)",
        )
    return GateResult(True, f"seal commit on origin/main with green CI ({ci.message})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sha", required=True, help="the tagged seal-commit SHA to gate on")
    ap.add_argument(
        "--on-main",
        action="store_true",
        help="the caller already confirmed `git merge-base --is-ancestor` for --sha",
    )
    args = ap.parse_args(argv)
    if not args.on_main:
        res = evaluate(False, None, args.sha)
        print(("OK: " if res.ok else "REFUSE: ") + res.message)
        return 0 if res.ok else 1
    try:
        runs = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"REFUSE: could not parse CI runs JSON from stdin: {exc}")
        return 1
    res = evaluate(True, runs, args.sha)
    print(("OK: " if res.ok else "REFUSE: ") + res.message)
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
