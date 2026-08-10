"""Publication-boundary scan of this repository's GitHub surface (Phase 211).

`publication_boundary_lint` enumerates tracked files. Issue and pull-request
titles, bodies, and comments are not files, so they were never in scope: the
surface was cleaned by hand twice, and one issue title survived a body-only
anonymization performed the same day.

Scanning is pure over already-fetched items and delegates to
`publication_boundary_lint.scan_text`, so both surfaces share one detector set
and one `boundary-lint: ok=<reason>` exemption idiom rather than growing a
second dialect. Fetching is a thin, injectable seam, so no test needs a network.

Read-only by design. A finding is reported for a human to anonymize; rewriting
an operator's issue text unattended is not a decision a lint should make.

Runs on a schedule rather than in the fail-closed pull-request job: that job
runs on forks with no token, where an authenticated scan would fail for reasons
unrelated to the boundary. An unattended run cannot read the gitignored terms
overlay, so it applies structural detectors only -- and says so, because a bare
"clean" would overstate what was checked.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts.publication_boundary_lint import _load_terms, scan_text


@dataclass(frozen=True)
class SurfaceItem:
    """One scannable piece of GitHub text."""

    kind: str      # "issue" | "pr"
    number: int
    field: str     # "title" | "body" | "comment"
    text: str
    author: str = ""


def is_machine_author(login: str) -> bool:
    """True for machine authors, whose dependency PRs name upstream by purpose.

    Same reasoning as `pr_citation_lint.is_exempt_actor`, and covers both login
    forms GitHub emits: the `dependabot[bot]` trailer form and the
    `app/dependabot` form `gh pr list --json author` returns.
    """
    actor = login.strip().lower()
    return actor.endswith("[bot]") or actor.startswith("app/")


def scan_surface(items, terms: list[str]) -> list[str]:
    """Return boundary findings across already-fetched surface items.

    Machine-authored items are skipped: a dependency bump names the upstream
    repository it bumps, which is the entire content of such a pull request.
    Reporting those would bury real findings under automation noise and make
    the control unusable -- the failure mode this project already diagnosed in
    a control that could not express its own exceptions.
    """
    findings: list[str] = []
    for item in items:
        if is_machine_author(item.author or ""):
            continue
        ref = f"{item.kind} #{item.number} ({item.field})"
        findings.extend(scan_text(ref, item.text or "", terms))
    return findings


def _gh_json(args: list[str]) -> list:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed (exit {result.returncode}): "
            f"{result.stderr.strip() or '<empty>'}"
        )
    return json.loads(result.stdout or "[]")


def fetch_surface(repo: str) -> list[SurfaceItem]:
    """Fetch issue and pull-request titles, bodies, and issue comments."""
    items: list[SurfaceItem] = []
    for kind, lister in (("issue", "issue"), ("pr", "pr")):
        rows = _gh_json([
            lister, "list", "--repo", repo, "--state", "all",
            "--limit", "200", "--json", "number,title,body,author",
        ])
        for row in rows:
            who = (row.get("author") or {}).get("login", "")
            items.append(SurfaceItem(kind, row["number"], "title", row.get("title") or "", who))
            items.append(SurfaceItem(kind, row["number"], "body", row.get("body") or "", who))
    for item in [i for i in items
                 if i.kind == "issue" and i.field == "title"
                 and not is_machine_author(i.author)]:
        for row in _gh_json([
            "api", f"repos/{repo}/issues/{item.number}/comments", "--jq", "[.[].body]",
        ]):
            items.append(
                SurfaceItem("issue", item.number, "comment", row or "", item.author)
            )
    return items


def main(argv: list[str] | None = None, fetcher=fetch_surface) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", required=True, help="owner/name of the repository to scan")
    ap.add_argument("--terms-file", type=Path, default=None,
                    help="operator-local identity terms (gitignored; absent in CI)")
    args = ap.parse_args(argv)

    terms = _load_terms(args.terms_file) if args.terms_file else []
    try:
        items = fetcher(args.repo)
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"ERROR [github-surface] could not read the surface: {exc}", file=sys.stderr)
        return 2

    findings = scan_surface(items, terms)
    for finding in findings[:200]:
        print(finding)
    coverage = f"terms overlay: {len(terms)} terms" if terms else "structural only"
    print(f"github_surface: {len(findings)} finding(s) ({coverage})")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
