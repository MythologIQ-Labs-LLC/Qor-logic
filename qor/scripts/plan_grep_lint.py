"""Pre-audit lint: detect infrastructure-mismatch citations in plan files (Phase 55).

Walks a plan file; extracts cited Python module paths
(``qor.scripts.<name>``, ``qor.policy.<name>``, etc.) and skill paths
(``qor/skills/**/*.md``); verifies each cited path resolves at HEAD.
References declared as NEW in the plan's Affected Files block are excluded.

Closes the Phase 53/54/55 recurring infrastructure-mismatch pattern at the
pre-audit lint layer per ``qor/references/doctrine-shadow-genome-countermeasures.md``
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
    citation: str
    reason: str


_MODULE_RE = re.compile(r"\bqor\.(?:scripts|policy|reliability|cli_handlers)\.([\w_]+)")
_SKILL_PATH_RE = re.compile(r"qor/skills/(?:[\w_-]+/)+SKILL\.md")
_REFERENCE_PATH_RE = re.compile(r"qor/references/[\w_-]+\.md")
_NEW_DECLARATION_RE = re.compile(
    r"^[-*]\s+`(?P<path>[^`]+)`.*\bNEW\b", re.MULTILINE,
)


def _module_to_path(module_segment: str, repo_root: Path) -> Path:
    """qor.scripts.foo → qor/scripts/foo.py"""
    parts = module_segment.split(".")
    return repo_root.joinpath(*parts).with_suffix(".py")


def _new_paths(text: str) -> set[str]:
    """Paths the plan declares as NEW in any Affected Files block."""
    return {m.group("path") for m in _NEW_DECLARATION_RE.finditer(text)}


def check_plan(plan_path: Path, repo_root: Path) -> list[LintWarning]:
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    new_paths = _new_paths(text)
    warnings: list[LintWarning] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in re.finditer(r"\bqor\.(scripts|policy|reliability|cli_handlers)\.([\w_]+)\b", line):
            module_name = match.group(2)
            # Skip placeholder-style citations and explicit test-fixture names.
            if len(module_name) <= 1 or (module_name.isupper() and len(module_name) <= 3):
                continue
            if any(token in module_name.lower() for token in ("fake", "nonexistent", "synthetic", "fixture", "new_helper", "new_module")):
                continue
            module = f"qor.{match.group(1)}.{module_name}"
            full_path = repo_root / "qor" / match.group(1) / f"{module_name}.py"
            if any(full_path.as_posix().endswith(p) for p in new_paths):
                continue
            if any(p.endswith(f"qor/{match.group(1)}/{module_name}.py") for p in new_paths):
                continue
            if not full_path.exists():
                warnings.append(LintWarning(
                    plan=str(plan_path), line=line_no,
                    citation=module,
                    reason=f"module path {full_path.relative_to(repo_root)} does not exist",
                ))

        for match in _SKILL_PATH_RE.finditer(line):
            skill_path = match.group(0)
            if skill_path in new_paths:
                continue
            # Skip placeholder/test-fixture skill paths.
            if any(token in skill_path.lower() for token in ("fake-", "synthetic-", "nonexistent-")):
                continue
            full_path = repo_root / skill_path
            if not full_path.exists():
                warnings.append(LintWarning(
                    plan=str(plan_path), line=line_no,
                    citation=skill_path,
                    reason="skill path does not exist",
                ))

    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_grep_lint")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or Path.cwd()
    warnings = check_plan(args.plan, repo_root)
    if not warnings:
        return 0
    for w in warnings:
        print(
            f"WARN [plan-grep-lint] {w.plan}:{w.line} [{w.citation}] {w.reason}",
            file=sys.stderr,
        )
    print(
        f"\n{len(warnings)} infrastructure-mismatch citations detected. "
        f"Either declare the cited path as NEW in Affected Files, or fix "
        f"the citation to match an existing repo path.",
        file=sys.stderr,
    )
    return 0  # WARN-only


if __name__ == "__main__":
    raise SystemExit(main())
