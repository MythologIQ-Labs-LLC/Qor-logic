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

# Phase 84 (GH #84): closed-enum taxonomy inverse-coverage detection.
_CANONICAL_TUPLE_RE = re.compile(r"\bCANONICAL_[A-Z][A-Z0-9_]*VALUES\b")
_NORMALIZE_FN_RE = re.compile(r"\bnormalize[A-Za-z][A-Za-z0-9_]*\b")
_INVERSE_SIGNAL_RE = re.compile(r"\binverse\b|\breachable\b", re.IGNORECASE)


def _inverse_coverage_warnings(text: str, plan_path: Path) -> list[LintWarning]:
    """Flag a plan that declares a closed-enum taxonomy (a CANONICAL_*_VALUES
    constant plus a normalize* function) whose test list carries no
    inverse-coverage assertion. Per qor/references/doctrine-test-functionality.md
    inverse-coverage discipline (SG-InverseCoverageGapTaxonomy-A)."""
    lines = text.splitlines()
    taxonomy_line = 0
    for line_no, line in enumerate(lines, start=1):
        if _CANONICAL_TUPLE_RE.search(line):
            taxonomy_line = line_no
            break
    if not taxonomy_line or not _NORMALIZE_FN_RE.search(text):
        return []
    for line in lines:
        if line.lstrip().startswith(("- ", "* ")) and _INVERSE_SIGNAL_RE.search(line):
            return []
    return [LintWarning(
        plan=str(plan_path), line=taxonomy_line,
        pattern="inverse-coverage-missing",
        excerpt=lines[taxonomy_line - 1].strip()[:120],
    )]


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
    warnings.extend(_inverse_coverage_warnings(text, plan_path))
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
        f"\n{len(warnings)} test-list issue(s) detected (presence-only "
        f"descriptions and/or missing inverse coverage). See "
        f"qor/references/doctrine-test-functionality.md.",
        file=sys.stderr,
    )
    return 0  # WARN-only


if __name__ == "__main__":
    raise SystemExit(main())
