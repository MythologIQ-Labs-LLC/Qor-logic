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

import argparse
import re
import sys


# Phase 252 (GH #413): the `plan-qor-phase<NN>` convention is this repository's
# own and never described what a governance plan is. A consumer naming plans
# after the work satisfies the citation; `docs/plan.md` and `docs/planning.md`
# still do not, because the hyphen-slug shape is what distinguishes a plan.
_PLAN_PATTERN = re.compile(r"docs/plan-[a-z0-9][a-z0-9-]*\.md")
_BRIEF_PATTERN = re.compile(r"docs/research-brief-[a-z0-9-]+\.md")

# Paths that are governance records rather than product source. A diff touching
# anything else demands the full citation triple regardless of which gate
# artifacts accompany it -- otherwise the artifact set becomes a label an author
# could set to the least demanding value (tribunal ground V-2, entry #699).
_GOVERNANCE_PREFIXES = (".qor/", "docs/")
_ENTRY_PATTERN = re.compile(r"(?:entry|ledger)[^#]{0,40}#\d+", re.IGNORECASE)
_SEAL_PATTERN = re.compile(r"\b[0-9a-f]{64}\b")


def required_citations(changed_files: list[str] | None) -> tuple[str, ...]:
    """Which citations this PR must carry, derived from what it changes.

    Phase 252 (GH #413). A research-phase record has no plan artifact and no
    Merkle seal, so demanding all three made a legitimate governance PR
    unpassable. The requirement now follows the evidence:

    - touches non-governance source  -> full triple, whatever artifacts ride along
    - carries a substantiate artifact -> full triple (a seal PR cites everything)
    - carries a plan artifact         -> plan + entry
    - carries only a research artifact-> brief + entry
    - no artifacts at all             -> full triple

    Deriving from the artifact set ALONE would make that set a settable label,
    which is the hazard a self-declared phase label was rejected for -- hence the
    first rule.
    """
    full = ("plan", "entry", "seal")
    if not changed_files:
        return full
    if any(
        not f.replace("\\", "/").startswith(_GOVERNANCE_PREFIXES)
        for f in changed_files
    ):
        return full
    joined = " ".join(f.replace("\\", "/") for f in changed_files)
    if "substantiate.json" in joined:
        return full
    if "plan.json" in joined:
        return ("plan", "entry")
    if "research.json" in joined:
        return ("brief", "entry")
    return full


def check_pr_body(body: str, changed_files: list[str] | None = None) -> list[str]:
    """Return list of missing citations. Empty list means all present.

    Per doctrine-governance-enforcement §6, scoped by `required_citations`.
    Callers passing no file list keep the historical strict behavior.
    """
    required = required_citations(changed_files)
    checks = {
        "plan": (_PLAN_PATTERN, "plan file path (docs/plan-<slug>.md)"),
        "brief": (_BRIEF_PATTERN, "research brief path (docs/research-brief-<slug>.md)"),
        "entry": (_ENTRY_PATTERN, "ledger entry reference (entry/ledger + #<n>)"),
        "seal": (_SEAL_PATTERN, "Merkle seal hash (64 hex chars)"),
    }
    return [label for key in required
            for pattern, label in [checks[key]]
            if not pattern.search(body)]


def is_exempt_actor(actor: str) -> bool:
    """True for machine authors (login ending in '[bot]', e.g. dependabot[bot]).

    Their PRs are dependency/automation bumps with no plan/ledger/Merkle-seal
    to cite, so the doctrine §6 citation requirement does not apply to them.
    """
    return actor.strip().lower().endswith("[bot]")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pr_citation_lint")
    parser.add_argument("--actor", default="",
                        help="PR author login; '*[bot]' authors are exempt")
    parser.add_argument("--changed-files", default="",
                        help="newline- or comma-separated changed paths; scopes "
                             "which citations are required (GH #413)")
    args = parser.parse_args(argv)
    if is_exempt_actor(args.actor):
        print(f"SKIP: actor '{args.actor}' is a bot; citation lint exempt "
              "(machine-generated PR has no ledger entry to cite)")
        return 0
    body = sys.stdin.read()
    raw = args.changed_files.replace(",", "\n").splitlines()
    changed = [f.strip() for f in raw if f.strip()] or None
    missing = check_pr_body(body, changed_files=changed)
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
