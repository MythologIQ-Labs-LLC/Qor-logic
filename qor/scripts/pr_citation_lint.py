"""PR citation lint (Phase 31 Phase 3).

Enforces doctrine-governance-enforcement.md §6: PR descriptions must cite
plan file path + ledger entry + Merkle seal hash.

Usage:
    echo "$PR_BODY" | python qor/scripts/pr_citation_lint.py
    # exit 0 -> all citations present
    # exit 1 -> at least one missing; stdout names which

Invoked by .github/workflows/pr-lint.yml on pull_request events.
"""
from __future__ import annotations

import re
import sys


_PLAN_PATTERN = re.compile(r"docs/plan-qor-phase\d+[a-z0-9-]*\.md")
_ENTRY_PATTERN = re.compile(r"(?:entry|ledger)[^#]{0,40}#\d+", re.IGNORECASE)
_SEAL_PATTERN = re.compile(r"\b[0-9a-f]{64}\b")


def check_pr_body(body: str) -> list[str]:
    """Return list of missing citations. Empty list means all present.

    Required per doctrine-governance-enforcement §6:
    - plan file path (docs/plan-qor-phase<NN>-<slug>.md)
    - ledger entry reference (#<n>, case-insensitive adjacent to 'entry'/'ledger')
    - Merkle seal hash (64 hex chars)
    """
    missing: list[str] = []
    if not _PLAN_PATTERN.search(body):
        missing.append("plan file path (docs/plan-qor-phase<NN>-<slug>.md)")
    if not _ENTRY_PATTERN.search(body):
        missing.append("ledger entry reference (entry/ledger + #<n>)")
    if not _SEAL_PATTERN.search(body):
        missing.append("Merkle seal hash (64 hex chars)")
    return missing


def main() -> int:
    body = sys.stdin.read()
    missing = check_pr_body(body)
    if not missing:
        print("OK: PR body has all required citations per doctrine-governance-enforcement §6")
        return 0
    print("FAIL: PR body is missing the following required citations:")
    for m in missing:
        print(f"  - {m}")
    print("")
    print("See qor/references/doctrine-governance-enforcement.md §6 for the template.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
