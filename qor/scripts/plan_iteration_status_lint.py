"""Pre-audit lint: short-circuit when a plan declares itself not audit-ready (Phase 84).

Detects three pre-audit self-declaration signals in a plan file:
  - an ``**iteration**:`` value containing ``draft`` or ``pre-audit``;
  - an "Operator Decisions Required Before Audit" heading;
  - an Open Questions bullet ending "Operator confirms before audit".

Exits non-zero on any hit. Wired into ``/qor-audit`` Step 0.3 as a hard
short-circuit: a plan that declares itself not-ready is not a candidate for
adversarial review, and triggering audit on it burns an audit-iteration slot.

Closes ``SG-PreAuditDraftSubmission-A`` per
``qor/references/doctrine-shadow-genome-countermeasures.md``.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReadinessFinding:
    plan: str
    line: int
    signal: str
    excerpt: str


_ITERATION_RE = re.compile(
    r"^\s*\*\*iteration\*\*\s*:\s*(?P<value>.+?)\s*$", re.IGNORECASE)
_DECISIONS_HEADING_RE = re.compile(
    r"^\s*#{1,6}\s+.*operator decisions required before audit", re.IGNORECASE)
_CONFIRMS_BULLET_RE = re.compile(
    r"^\s*[-*]\s+.*operator confirms before audit\s*[.)\s]*$", re.IGNORECASE)
_DRAFT_TOKENS = ("draft", "pre-audit")


def check_plan(plan_path: Path) -> list[ReadinessFinding]:
    """Return one ReadinessFinding per pre-audit self-declaration signal."""
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    findings: list[ReadinessFinding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        iteration = _ITERATION_RE.match(line)
        if iteration and any(
            token in iteration.group("value").lower() for token in _DRAFT_TOKENS
        ):
            findings.append(_finding(plan_path, line_no, "draft-iteration", line))
            continue
        if _DECISIONS_HEADING_RE.match(line):
            findings.append(
                _finding(plan_path, line_no, "operator-decisions-section", line))
            continue
        if _CONFIRMS_BULLET_RE.match(line):
            findings.append(
                _finding(plan_path, line_no, "operator-confirms-oq", line))
    return findings


def _finding(plan_path: Path, line_no: int, signal: str, line: str) -> ReadinessFinding:
    return ReadinessFinding(
        plan=str(plan_path), line=line_no, signal=signal,
        excerpt=line.strip()[:120],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_iteration_status_lint")
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)

    findings = check_plan(args.plan)
    if not findings:
        return 0
    for f in findings:
        print(
            f"ERROR [plan-iteration-status-lint] {f.plan}:{f.line} "
            f"[{f.signal}] {f.excerpt}",
            file=sys.stderr,
        )
    print(
        f"\n{len(findings)} pre-audit readiness signal(s) detected. Resolve the "
        f"operator-decision items, bump the plan past its pre-audit state, then "
        f"re-run /qor-audit.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
