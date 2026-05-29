"""Pre-audit lint: signature-widening caller-enumeration completeness (Phase 110, #133).

Per ``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-AffectedFilesContract-A (call-graph sub-leaf). When a plan declares a
function signature change, every caller file must appear in the plan's
``### Affected Files`` block or be explicitly exempted; otherwise the
implementer hits compile failures at the unenumerated call sites. WARN-only V1
(exit 0); a future V2 converts to a hard VETO with ``caller-incompleteness``.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts._lint_utils import find_callers

_SIGNATURE_PATTERNS = (
    re.compile(r"widen\s+`(\w+)`(?:\([^)]*\))?\s+to", re.IGNORECASE),
    re.compile(r"change\s+`(\w+)`\s+signature", re.IGNORECASE),
    re.compile(r"add\s+(?:a\s+)?(?:new\s+)?parameter\s+to\s+`(\w+)`", re.IGNORECASE),
    re.compile(r"replace\s+`(\w+)`\s+body", re.IGNORECASE),
)
_STOP_NAMES = frozenset(
    {"new", "next", "default", "clone", "len", "is_empty", "fmt", "drop", "hash", "eq", "partial_cmp", "cmp"}
)
_AFFECTED_FILE_RE = re.compile(r"^[-*]\s+`([^`]+)`", re.MULTILINE)
_EXEMPT_RE = re.compile(r"<!--\s*signature-widening-exempt:\s*(\w+)\s*-->")


@dataclass(frozen=True)
class LintWarning:
    function: str
    caller_file: str
    reason: str


def _min_fn_len() -> int:
    try:
        return int(os.environ.get("QOR_PLAN_LINT_MIN_FN_LEN", "8"))
    except ValueError:
        return 8


def _widened_functions(text: str) -> set[str]:
    names: set[str] = set()
    for pattern in _SIGNATURE_PATTERNS:
        names.update(match.group(1) for match in pattern.finditer(text))
    return names


def _affected_paths(text: str) -> set[str]:
    return {m.group(1) for m in _AFFECTED_FILE_RE.finditer(text)}


def _exempt_functions(text: str) -> set[str]:
    return {m.group(1) for m in _EXEMPT_RE.finditer(text)}


def check_plan(plan_path: Path, repo_root: Path) -> list[LintWarning]:
    plan_path = Path(plan_path)
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    affected = _affected_paths(text)
    exempt = _exempt_functions(text)
    min_len = _min_fn_len()
    warnings: list[LintWarning] = []
    for fn in sorted(_widened_functions(text)):
        if fn in _STOP_NAMES or fn in exempt or len(fn) < min_len:
            continue
        for caller in sorted(find_callers(fn, Path(repo_root))):
            if caller not in affected:
                warnings.append(LintWarning(fn, caller, "caller file not enumerated in Affected Files"))
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_signature_widening_caller_lint")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    warnings = check_plan(args.plan, args.repo_root)
    for w in warnings:
        print(f"WARN [signature-widening]: `{w.function}` caller {w.caller_file} not in Affected Files", file=sys.stderr)
    if warnings:
        print(f"{len(warnings)} unenumerated caller file(s); see SG-AffectedFilesContract-A.", file=sys.stderr)
    return 0  # WARN-only V1


if __name__ == "__main__":
    raise SystemExit(main())
