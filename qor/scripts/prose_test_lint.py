"""Prose-not-behavior test-source lint (Phase 116, GH #170).

Flags tests whose only assertion is substring membership in a SKILL.md (or
similar doc) -- the presence-not-behavior anti-pattern that shipped in #56/#58/
#83 and that ``plan_test_lint`` (plan-text only) could not catch. Operates on
actual ``tests/*.py`` source via AST.

Heuristic (low false-positive, WARN-first): within a test function, if the
function reads a ``SKILL.md`` (a ``.read_text()`` call and the token ``SKILL.md``
both appear) AND contains an ``assert "<literal>" in <...>`` membership check,
the assertion is flagged as presence-only. Genuine behavioral tests (which call
the unit and assert on its output) do not read a SKILL.md and are not flagged.

Reuses the spirit of ``plan_test_lint._PRESENCE_PATTERNS`` at the test-source
level. WARN-first when wired into ``/qor-audit`` Test Functionality Pass.
Doctrine: ``qor/references/doctrine-verification-closure-integrity.md``.
Stdlib-only.
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProseFinding:
    file: str
    function: str
    line: int
    text: str


def _fn_reads_skill_md(fn: ast.AST) -> bool:
    try:
        src = ast.unparse(fn)
    except Exception:  # noqa: BLE001 - unparse failure -> treat as not-reading
        return False
    return "read_text" in src and "SKILL.md" in src


def _is_str_in_membership(node: ast.AST) -> str | None:
    """Return the literal substring if ``node`` is ``assert "<str>" in <...>``."""
    if not (isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare)):
        return None
    cmp = node.test
    if not any(isinstance(op, ast.In) for op in cmp.ops):
        return None
    left = cmp.left
    if isinstance(left, ast.Constant) and isinstance(left.value, str):
        return left.value
    return None


def scan_source(src: str, filename: str = "<test>") -> list[dict]:
    """Scan test source; return findings (dicts) for presence-only assertions."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    findings: list[dict] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not fn.name.startswith("test"):
            continue
        if not _fn_reads_skill_md(fn):
            continue
        for node in ast.walk(fn):
            sub = _is_str_in_membership(node)
            if sub is not None:
                findings.append({
                    "file": filename, "function": fn.name,
                    "line": getattr(node, "lineno", 0), "text": sub[:60],
                })
    return findings


def scan_dir(tests_dir: str = "tests") -> list[dict]:
    out: list[dict] = []
    for path in sorted(Path(tests_dir).glob("test_*.py")):
        out.extend(scan_source(path.read_text(encoding="utf-8"), filename=str(path)))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.prose_test_lint")
    parser.add_argument("--tests-dir", default="tests")
    parser.add_argument("--enforce", action="store_true",
                        help="exit non-zero when findings exist (graduated V2)")
    args = parser.parse_args(argv)
    findings = scan_dir(args.tests_dir)
    for f in findings:
        print(f"  WARN [presence-only] {f['file']}:{f['line']} {f['function']} "
              f"-> assert \"{f['text']}\" in <SKILL.md text>")
    if findings:
        print(f"prose_test_lint: {len(findings)} presence-only assertion(s)")
        if args.enforce:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
