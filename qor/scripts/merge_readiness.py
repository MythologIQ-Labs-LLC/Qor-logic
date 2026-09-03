#!/usr/bin/env python3
"""Merge-readiness guard (Phase 257).

Closes the severity-3 `merge-on-green` gate_override of 2026-08-17: a pull
request was admin-merged while CI checks were still pending, the pending run
failed after the merge, and `main` went red with the release refused.

The remedy on that record -- "never admin-merge with any check pending; admin
flag is for ruleset-blocked GREEN runs only" -- is a question a person answers by
reading a list, at the moment of least patience in the cycle. This answers it in
one command.

Not a preventive control, and does not claim to be: ``gh pr merge --admin``
exists to bypass branch protection, so no CI job can gate the flag whose purpose
is to ignore CI jobs. This is the detective and procedural half. The downstream
consequence is separately gated by ``release_ci_gate`` (Phase 163), which refuses
a publish whose SHA is not green.

The decision logic is a pure function over the parsed check list so the rule is
testable offline; only ``main`` touches the network, shelling out to ``gh`` in
list form as ``ac_close_guard`` does. No forge SDK is imported.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from enum import Enum

# Positively recognized as "not a reason to wait". Everything outside these sets
# blocks -- see Readiness.UNRECOGNIZED for why the default is deny.
_OK_BUCKETS = frozenset({"pass", "skipping"})
_DEFERRED_STATES = frozenset({"WAITING"})
_RUNNING_STATES = frozenset({"QUEUED", "IN_PROGRESS", "PENDING"})
_FAIL_BUCKET = "fail"


class Readiness(Enum):
    """Outcome of a merge-readiness classification.

    ``READY`` is not the fall-through case. It is reached only when every check
    is positively recognized, which is what keeps an unfamiliar state from
    reading as green.
    """

    READY = "READY"
    RUNNING = "RUNNING"
    FAILING = "FAILING"
    NO_CHECKS = "NO_CHECKS"
    UNRECOGNIZED = "UNRECOGNIZED"

    @property
    def mergeable(self) -> bool:
        return self is Readiness.READY


def unrecognized(checks: list[dict]) -> list[dict]:
    """Return the checks whose bucket and state the rule does not understand."""
    return [
        c for c in checks
        if c.get("bucket") not in _OK_BUCKETS
        and c.get("bucket") != _FAIL_BUCKET
        and c.get("state") not in _DEFERRED_STATES
        and c.get("state") not in _RUNNING_STATES
    ]


def deferred(checks: list[dict]) -> list[dict]:
    """Return checks waiting on a human rather than on a machine."""
    return [c for c in checks if c.get("state") in _DEFERRED_STATES]


def classify(checks: list[dict]) -> Readiness:
    """Decide whether a pull request's checks permit a merge.

    Blocking conditions are evaluated before acceptance, and acceptance requires
    positive recognition of every check. An empty list is ``NO_CHECKS``: absence
    of evidence is not evidence of health, and merging before a workflow is
    scheduled is the sibling of merging while one runs.
    """
    if not checks:
        return Readiness.NO_CHECKS
    if any(c.get("bucket") == _FAIL_BUCKET for c in checks):
        return Readiness.FAILING
    if any(c.get("state") in _RUNNING_STATES for c in checks):
        return Readiness.RUNNING
    if unrecognized(checks):
        return Readiness.UNRECOGNIZED
    return Readiness.READY


def fetch_checks(pr: str) -> list[dict]:
    """Read the check list for a pull request via the gh CLI."""
    result = subprocess.run(
        ["gh", "pr", "checks", pr, "--json", "name,state,bucket"],
        capture_output=True, text=True, timeout=60, check=False,
    )
    # gh exits non-zero when any check is failing or pending, which are states
    # this tool exists to report rather than to treat as an invocation error.
    if not result.stdout.strip():
        raise RuntimeError(f"gh returned no check data for {pr!r}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _describe(verdict: Readiness, checks: list[dict]) -> str:
    if verdict is Readiness.NO_CHECKS:
        return "no checks reported; absence of evidence is not evidence of health"
    if verdict is Readiness.FAILING:
        names = [c["name"] for c in checks if c.get("bucket") == _FAIL_BUCKET]
        return "failing: " + ", ".join(names)
    if verdict is Readiness.RUNNING:
        names = [c["name"] for c in checks if c.get("state") in _RUNNING_STATES]
        return "still running: " + ", ".join(names)
    if verdict is Readiness.UNRECOGNIZED:
        pairs = [f"{c['name']} (bucket={c.get('bucket')!r} state={c.get('state')!r})"
                 for c in unrecognized(checks)]
        return "unrecognized, blocking to fail safe: " + ", ".join(pairs)
    waiting = [c["name"] for c in deferred(checks)]
    tail = f"; deferred on approval: {', '.join(waiting)}" if waiting else ""
    return f"{len(checks)} check(s) accounted for{tail}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pr", required=True, help="pull request number or URL")
    args = parser.parse_args(argv)

    checks = fetch_checks(args.pr)
    verdict = classify(checks)
    print(f"{verdict.value}: {_describe(verdict, checks)}")
    if not verdict.mergeable:
        print("Do not merge. --admin is for ruleset-blocked GREEN runs only.",
              file=sys.stderr)
    return 0 if verdict.mergeable else 1


if __name__ == "__main__":
    raise SystemExit(main())
