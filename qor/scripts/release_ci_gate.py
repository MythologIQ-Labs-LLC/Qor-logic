#!/usr/bin/env python3
"""Phase 163: gate a release publish on the CI workflow's success for the tagged SHA.

`release.yml` had `build -> publish` with no test step, so a publish was coupled
to the tests passing only by operator discipline (verify PR CI before approving
the `pypi` gate). This module is the fail-closed, structural replacement: the
workflow runs the authenticated `gh api .../workflows/ci.yml/runs?head_sha=<SHA>`
call and pipes its JSON to ``main``, which refuses (exit 1) unless a CI run for
that exact commit concluded ``success``.

Pure decision logic (``evaluate``) so it is unit-testable in-process; no network
or ``gh`` dependency lives here. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class GateResult:
    ok: bool
    message: str


def _run_list(runs: object) -> list[dict]:
    """Accept the `gh api` payload (`{"workflow_runs": [...]}`) or a bare list."""
    if isinstance(runs, dict):
        items = runs.get("workflow_runs", [])
    else:
        items = runs or []
    return [r for r in items if isinstance(r, dict)]


def evaluate(runs: object, head_sha: str) -> GateResult:
    """Fail-closed: ok iff at least one run for ``head_sha`` concluded success."""
    matches = [r for r in _run_list(runs) if r.get("head_sha") == head_sha]
    if not matches:
        return GateResult(False, f"no CI run found for {head_sha[:8]}... (refusing release)")
    if any(r.get("conclusion") == "success" for r in matches):
        return GateResult(True, f"CI succeeded for {head_sha[:8]}...")
    states = sorted({f"{r.get('status')}/{r.get('conclusion')}" for r in matches})
    return GateResult(
        False,
        f"no successful CI run for {head_sha[:8]}...; observed {states} (refusing release)",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sha", required=True, help="the tagged commit SHA to gate on")
    args = ap.parse_args(argv)
    try:
        runs = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"REFUSE: could not parse CI runs JSON from stdin: {exc}")
        return 1
    res = evaluate(runs, args.sha)
    print(("OK: " if res.ok else "REFUSE: ") + res.message)
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
