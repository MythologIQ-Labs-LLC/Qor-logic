"""Pre-audit lint: detect presence-only test descriptions in plan files (Phase 55).

Walks ``docs/plan-qor-phase*.md``; greps test description bullets for the
four canonical presence-only patterns. Emits warnings with file/line numbers
and suggested reformulation. WARN-only at ``/qor-audit`` Step 0.5; the
existing Test Functionality Pass at Step 3 issues binding VETOs.

Closes the cross-session recurrence pattern flagged in Phase 53/54/55 first
audits per ``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-PreAuditLintGap-A.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LintWarning:
    plan: str
    line: int
    pattern: str
    excerpt: str


_PRESENCE_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("substring-presence",
     re.compile(r"asserts.*\bcontains\b.*\bliteral\b", re.IGNORECASE)),
    ("section-exists",
     re.compile(r"asserts.*\bsection\b.*\b(?:exists?|present)\b", re.IGNORECASE)),
    ("substring-in-file",
     re.compile(r"\bin\s+<file_text>|\bin\s+body\b|assert\s+\"[^\"]+\"\s+in\s+<", re.IGNORECASE)),
    ("path-exists",
     re.compile(r"\bassert\s+(?:path\.exists|os\.path\.exists)\b")),
)


def check_plan(plan_path: Path) -> list[LintWarning]:
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    warnings: list[LintWarning] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.lstrip().startswith(("- ", "  - ")):
            continue
        for pattern_name, pattern in _PRESENCE_PATTERNS:
            if pattern.search(line):
                warnings.append(LintWarning(
                    plan=str(plan_path), line=line_no,
                    pattern=pattern_name, excerpt=line.strip()[:120],
                ))
                break
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_test_lint")
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)

    warnings = check_plan(args.plan)
    if not warnings:
        return 0
    for w in warnings:
        print(
            f"WARN [plan-test-lint] {w.plan}:{w.line} [{w.pattern}] {w.excerpt}",
            file=sys.stderr,
        )
    print(
        f"\n{len(warnings)} presence-only test descriptions detected. "
        f"Reform as conditional co-occurrence behavior invariants per "
        f"qor/references/doctrine-test-functionality.md.",
        file=sys.stderr,
    )
    return 0  # WARN-only


if __name__ == "__main__":
    raise SystemExit(main())
