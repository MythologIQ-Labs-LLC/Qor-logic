"""Prose-not-behavior test-source lint (Phase 116 #170; hardened Phase 117 #174).

Flags tests whose only assertion is substring membership in a SKILL.md prompt --
the presence-not-behavior anti-pattern from #56/#58/#83 that ``plan_test_lint``
(plan-text only) could not catch. Operates on actual ``tests/*.py`` source via AST.

Hardened heuristic (Phase 117): a finding is raised only when an
``assert "<literal>" in <X>`` membership check has ``<X>`` tracing to a SKILL.md
read -- a local variable assigned from a ``.read_text()`` whose path mentions
``SKILL.md``, or an inline ``...SKILL.md...read_text()`` call. This eliminates the
false positives where ``<X>`` is subprocess stderr, a non-SKILL.md source file,
or an emitted dict, even when the function happens to mention ``SKILL.md``.

Allowlist: an assertion carrying a trailing ``# prose-lint: ok=<reason>`` comment
(non-empty reason) is recorded as *exempted* rather than *unexplained*. Legitimate
prose-contract checks on prompt instructions are exempted with a stated reason.

``--enforce`` exits non-zero only when UNEXPLAINED findings remain (exempted ones
do not block). Wired into ``/qor-audit`` Test Functionality Pass.
Doctrine: ``qor/references/doctrine-verification-closure-integrity.md``. Stdlib-only.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

_ALLOW_RE = re.compile(r"#\s*prose-lint:\s*ok=(\S.*?)\s*$")


def _module_skill_consts(tree: ast.Module) -> set[str]:
    """Module-level names bound to a path expression that mentions ``SKILL.md``
    (e.g. ``SUBSTANTIATE_SKILL = REPO_ROOT / 'qor' / ... / 'SKILL.md'``)."""
    out: set[str] = set()
    for node in getattr(tree, "body", []):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        value = node.value
        if value is None:
            continue
        try:
            if "SKILL.md" in ast.unparse(value):
                for t in targets:
                    if isinstance(t, ast.Name):
                        out.add(t.id)
        except Exception:  # noqa: BLE001
            continue
    return out


def _skill_read(node: ast.AST, consts: set[str] = frozenset()) -> bool:
    """True if ``node`` reads a SKILL.md: an inline ``...SKILL.md...read_text()``,
    or a ``<const>.read_text()`` where ``<const>`` is a module-level SKILL.md path."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "read_text" and isinstance(node.func.value, ast.Name) \
            and node.func.value.id in consts:
        return True
    try:
        src = ast.unparse(node)
    except Exception:  # noqa: BLE001
        return False
    return "read_text" in src and "SKILL.md" in src


def _doc_vars(fn: ast.AST, consts: set[str]) -> set[str]:
    """Names within ``fn`` bound from a SKILL.md read."""
    out: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and _skill_read(node.value, consts):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
        elif isinstance(node, ast.AnnAssign) and node.value is not None \
                and _skill_read(node.value, consts):
            if isinstance(node.target, ast.Name):
                out.add(node.target.id)
    return out


def _membership_substring(node: ast.AST, doc_vars: set[str], consts: set[str]) -> str | None:
    """Return the literal substring if ``node`` is ``assert "<str>" in <doc-var
    or inline SKILL.md read>``; else None."""
    if not (isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare)):
        return None
    cmp = node.test
    if not any(isinstance(op, ast.In) for op in cmp.ops):
        return None
    left = cmp.left
    if not (isinstance(left, ast.Constant) and isinstance(left.value, str)):
        return None
    for comparator in cmp.comparators:
        if isinstance(comparator, ast.Name) and comparator.id in doc_vars:
            return left.value
        if _skill_read(comparator, consts):
            return left.value
    return None


def _allowlist_reason(lines: list[str], node: ast.AST) -> str | None:
    start = getattr(node, "lineno", 1)
    end = getattr(node, "end_lineno", start) or start
    for i in range(start - 1, min(end, len(lines))):
        m = _ALLOW_RE.search(lines[i])
        if m:
            return m.group(1).strip()
    return None


def scan_source(src: str, filename: str = "<test>") -> list[dict]:
    """Return findings (dicts: file, function, line, text, exempted, reason)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    lines = src.splitlines()
    consts = _module_skill_consts(tree)
    findings: list[dict] = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not fn.name.startswith("test"):
            continue
        doc_vars = _doc_vars(fn, consts)
        for node in ast.walk(fn):
            sub = _membership_substring(node, doc_vars, consts)
            if sub is None:
                continue
            reason = _allowlist_reason(lines, node)
            findings.append({
                "file": filename, "function": fn.name,
                "line": getattr(node, "lineno", 0), "text": sub[:60],
                "exempted": reason is not None, "reason": reason,
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
                        help="exit non-zero when UNEXPLAINED findings remain")
    args = parser.parse_args(argv)
    findings = scan_dir(args.tests_dir)
    unexplained = [f for f in findings if not f["exempted"]]
    exempted = [f for f in findings if f["exempted"]]
    for f in unexplained:
        print(f"  WARN [presence-only] {f['file']}:{f['line']} {f['function']} "
              f"-> assert \"{f['text']}\" in <SKILL.md text>")
    if exempted:
        print(f"prose_test_lint: {len(exempted)} exempted (allowlisted with reason)")
    if unexplained:
        print(f"prose_test_lint: {len(unexplained)} UNEXPLAINED presence-only assertion(s)")
        if args.enforce:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
