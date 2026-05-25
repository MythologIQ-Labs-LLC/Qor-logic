"""Phase 101 (GH #118 P0): configure GitHub `pypi` environment protection rules.

Idempotent gh-api wrapper. Sets required reviewers, tag-only deployment-branch
policy, prevents self-review. Admin-bypass disable is not exposed via the
environment PUT body in the current GitHub REST API and must be set once
via the repo settings UI as a P1 follow-up.

Usage:
    python -m qor.scripts.configure_pypi_environment \\
        --repo MythologIQ-Labs-LLC/Qor-logic \\
        --reviewer-id 12345 --reviewer-type User \\
        [--reviewer-id 67890 --reviewer-type Team ...] \\
        [--dry-run]

The PUT body is built by `build_put_body(...)`; the tag-only branch policy
body by `build_branch_policy_body()`. Both are pure factories with unit
tests in `tests/test_configure_pypi_environment.py`.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def build_put_body(reviewer_ids: list[int], reviewer_types: list[str]) -> dict:
    """Pure factory: gh-api PUT body for the `pypi` environment.

    Same inputs always produce the same dict (idempotent).
    """
    assert len(reviewer_ids) == len(reviewer_types), (
        "reviewer_ids and reviewer_types must have equal length"
    )
    assert len(reviewer_ids) >= 1, "at least one reviewer is required"
    return {
        "wait_timer": 0,
        "prevent_self_review": True,
        "reviewers": [
            {"type": t, "id": i}
            for t, i in zip(reviewer_types, reviewer_ids)
        ],
        "deployment_branch_policy": {
            "protected_branches": False,
            "custom_branch_policies": True,
        },
    }


def build_branch_policy_body() -> dict:
    """Pure factory: tag-only deployment-branch policy body."""
    return {"name": "v*.*.*", "type": "tag"}


def _run_gh_api(method: str, endpoint: str, body: dict) -> None:
    subprocess.run(
        ["gh", "api", "-X", method, endpoint, "--input", "-"],
        input=json.dumps(body),
        text=True,
        check=True,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", required=True, help="owner/name")
    p.add_argument("--reviewer-id", type=int, action="append", required=True)
    p.add_argument(
        "--reviewer-type",
        choices=["User", "Team"],
        action="append",
        required=True,
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    body = build_put_body(args.reviewer_id, args.reviewer_type)
    policy = build_branch_policy_body()

    print("PUT body:", file=sys.stderr)
    print(json.dumps(body, indent=2), file=sys.stderr)
    print("POST branch policy:", file=sys.stderr)
    print(json.dumps(policy, indent=2), file=sys.stderr)

    if args.dry_run:
        print("--dry-run: no API calls made", file=sys.stderr)
        return 0

    _run_gh_api("PUT", f"repos/{args.repo}/environments/pypi", body)
    _run_gh_api(
        "POST",
        f"repos/{args.repo}/environments/pypi/deployment-branch-policies",
        policy,
    )
    print(f"OK: pypi environment configured on {args.repo}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
