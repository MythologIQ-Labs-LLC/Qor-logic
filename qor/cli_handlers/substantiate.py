"""Phase 75: substantiate-capability CLI handler.

Prints a markdown table of per-step prerequisite status, paste-able into the
SESSION SEAL entry body. Operators on non-Python hosts use the report to
identify which substantiate steps will skip on their archetype.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qor.scripts import substantiate_capability as sc


def do_substantiate_capability(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    skill_md = repo_root / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
    if not skill_md.is_file():
        print(f"ERROR: qor-substantiate SKILL.md not found at {skill_md}", file=sys.stderr)
        return 2

    reports = sc.collect_all_reports(skill_md, repo_root)
    print("| Step | Requires | Present | Evidence |")
    print("|---|---|---|---|")
    for r in reports:
        marker = "PRESENT" if r.present else "ABSENT"
        ev = r.evidence.replace("|", "\\|")
        print(f"| {r.step_id} | {r.requires} | {marker} | {ev} |")
    return 0


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "substantiate-capability",
        help="Print per-step substantiate prerequisite status (Phase 75; GH #38)",
    )
    p.add_argument("--repo-root", default=".", help="Repository root (default: cwd)")
    p.set_defaults(func=do_substantiate_capability)
