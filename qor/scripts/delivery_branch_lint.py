"""Pre-audit lint: verify a plan's declared delivery branch exists on origin (Phase 83).

Reads a plan markdown file and extracts the optional ``**pr_target**:``
front-matter value. The Phase 37 Infrastructure Alignment Pass grep-verifies
cited infrastructure against the branch the plan NAMES but never challenges
whether that branch is still a valid, open merge target. This lint surfaces a
``pr_target`` that does not exist on the remote. Closes GH #87.

Security: ``pr_target`` is allowlist-validated against a conservative
branch-name pattern BEFORE any subprocess call. A value that is empty,
``-``-prefixed, or out-of-charset is reported as a finding and never passed to
``git`` -- a ``-``-prefixed value would otherwise be parsed by git as an
option (e.g. the command-specifying ``--upload-pack``). List-form argv closes
shell injection; the allowlist closes argument injection.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BranchResolver = Callable[[str], bool]


@dataclass(frozen=True)
class LintWarning:
    plan: str
    pr_target: str
    reason: str


# Conservative git ref-name allowlist: alphanumerics plus . _ / - , never
# leading with '-' (git would parse a leading-dash value as an option).
_BRANCH_NAME_RE = re.compile(r"^[A-Za-z0-9._/][A-Za-z0-9._/-]*$")
_PR_TARGET_RE = re.compile(r"^\*\*pr_target\*\*:\s*(\S.*?)\s*$", re.MULTILINE)


def _default_resolver(branch: str, cwd: Path | None = None) -> bool:
    """Return True if ``branch`` exists on origin. List-form argv; no shell."""
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        capture_output=True, text=True, cwd=cwd,
    )
    return result.returncode == 0 and result.stdout.strip() != ""


def _extract_pr_target(text: str) -> str | None:
    match = _PR_TARGET_RE.search(text)
    return match.group(1).strip() if match else None


def check_delivery_branch(
    plan_path: Path,
    branch_resolver: BranchResolver = _default_resolver,
) -> list[LintWarning]:
    """Return delivery-branch findings for ``plan_path`` (empty list when clean).

    No-op when the plan declares no ``pr_target``. An invalid ``pr_target`` is
    reported without ever invoking ``branch_resolver`` -- the value never
    reaches ``git``.
    """
    plan_path = Path(plan_path)
    if not plan_path.exists():
        return []
    pr_target = _extract_pr_target(
        plan_path.read_text(encoding="utf-8", errors="replace")
    )
    if pr_target is None:
        return []
    if not _BRANCH_NAME_RE.match(pr_target):
        return [LintWarning(
            plan=str(plan_path), pr_target=pr_target,
            reason="pr_target is not a well-formed branch name; not passed to git",
        )]
    if not branch_resolver(pr_target):
        return [LintWarning(
            plan=str(plan_path), pr_target=pr_target,
            reason="pr_target branch not found on origin",
        )]
    return []


def _select_resolver(repo_root: Path | None) -> BranchResolver:
    """Resolve the branch resolver. ``QOR_DELIVERY_BRANCH_LINT_FAKE`` is a test
    seam overriding the real git call with a deterministic stub."""
    fake = os.environ.get("QOR_DELIVERY_BRANCH_LINT_FAKE")
    if fake == "absent":
        return lambda _branch: False
    if fake == "present":
        return lambda _branch: True
    if repo_root is not None:
        return lambda branch: _default_resolver(branch, cwd=repo_root)
    return _default_resolver


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.delivery_branch_lint")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    warnings = check_delivery_branch(args.plan, _select_resolver(args.repo_root))
    if not warnings:
        return 0
    for w in warnings:
        print(
            f"WARN [delivery-branch-lint] {w.plan} [pr_target={w.pr_target}] {w.reason}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
