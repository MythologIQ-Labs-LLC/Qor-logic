"""Phase 49 (GH #47): heuristic detector for filter-stage ordering inversions.

Walks Python source via stdlib ast. For each function:
- Detects pipeline patterns: 2+ chained .filter() method calls; or 2+ sequential
  `if ...: continue` blocks inside a single `for`; or 2+ early-return guards.
- Extracts attribute/subscript field names referenced in filter predicates.
- Detects validator functions in the same module: name starts with
  `validate`/`check`/`verify`/`is_valid`. Extracts the field names those
  functions reference.
- Emits a finding when a pipeline references at least one field that also
  appears in a validator AND no validator-shaped call is made first in the
  pipeline function.

Findings are advisory: the operator (or Judge at audit time) confirms whether
the actual code order is a topological sort of the invariant dependency graph.
The lint cannot prove ordering by itself; it surfaces the question.

Stdlib-only. CLI: python -m qor.scripts.pipeline_inversion_lint [--check FILE | --repo-root DIR] [--include-tests]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

_VALIDATOR_NAME = re.compile(r"^(validate|check|verify|is_valid)", re.IGNORECASE)


@dataclass(frozen=True)
class PipelineFinding:
    file: str
    function: str
    line: int
    stage_descriptors: tuple[str, ...]
    validator_function: str | None
    shared_fields: tuple[str, ...]
    message: str


def _is_validator_name(name: str) -> bool:
    return bool(_VALIDATOR_NAME.match(name))


def _attr_names(node: ast.AST) -> set[str]:
    """Collect attribute / subscript field names referenced in node."""
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute):
            names.add(sub.attr)
        elif isinstance(sub, ast.Subscript):
            sl = sub.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                names.add(sl.value)
    return names


def _filter_chain_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    count = 0
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Attribute) and func.attr == "filter":
                count += 1
            elif isinstance(func, ast.Name) and func.id == "filter":
                count += 1
    return count


def _sequential_guard_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    count = 0
    for sub in ast.walk(node):
        if isinstance(sub, ast.For):
            body = sub.body
            for stmt in body:
                if isinstance(stmt, ast.If):
                    if any(isinstance(child, (ast.Continue, ast.Return)) for child in stmt.body):
                        count += 1
    return count


def _is_pipeline_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return _filter_chain_count(node) >= 2 or _sequential_guard_count(node) >= 2


def _filter_predicate_fields(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    fields: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            is_filter_call = (
                (isinstance(func, ast.Attribute) and func.attr == "filter")
                or (isinstance(func, ast.Name) and func.id == "filter")
            )
            if is_filter_call and sub.args:
                fields |= _attr_names(sub.args[0])
        if isinstance(sub, ast.For):
            for stmt in sub.body:
                if isinstance(stmt, ast.If):
                    if any(isinstance(c, (ast.Continue, ast.Return)) for c in stmt.body):
                        fields |= _attr_names(stmt.test)
    return fields


def _validator_calls_first(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True when the function's first non-docstring statement contains a
    call whose target name matches a validator-shaped name. Heuristic: catches
    `if not validate(...): raise/return` at the top of the function body."""
    body = list(node.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    if not body:
        return False
    head = body[0]
    for sub in ast.walk(head):
        if isinstance(sub, ast.Call):
            target = sub.func
            name: str | None = None
            if isinstance(target, ast.Name):
                name = target.id
            elif isinstance(target, ast.Attribute):
                name = target.attr
            if name and _is_validator_name(name):
                return True
    return False


def _module_validators(tree: ast.Module) -> dict[str, set[str]]:
    """Return {validator_function_name: set_of_field_names_it_references}."""
    out: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_validator_name(node.name):
            out[node.name] = _attr_names(node)
    return out


def _function_descriptors(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    descs: list[str] = []
    chain = _filter_chain_count(node)
    if chain >= 2:
        descs.append(f".filter() chain ({chain} stages)")
    seq = _sequential_guard_count(node)
    if seq >= 2:
        descs.append(f"sequential if-continue/return guards ({seq} stages)")
    return tuple(descs)


def scan_source(path: Path, source: str) -> list[PipelineFinding]:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    validators = _module_validators(tree)
    if not validators:
        return []
    validator_fields = set().union(*validators.values()) if validators else set()
    findings: list[PipelineFinding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _is_validator_name(node.name):
            continue
        if not _is_pipeline_function(node):
            continue
        pred_fields = _filter_predicate_fields(node)
        shared = pred_fields & validator_fields
        if not shared:
            continue
        if _validator_calls_first(node):
            continue
        validator_name = next(
            (vname for vname, vfields in validators.items() if vfields & shared),
            None,
        )
        findings.append(PipelineFinding(
            file=str(path),
            function=node.name,
            line=node.lineno,
            stage_descriptors=_function_descriptors(node),
            validator_function=validator_name,
            shared_fields=tuple(sorted(shared)),
            message=(
                f"function {node.name!r} runs a filter pipeline referencing field(s) "
                f"{sorted(shared)} that also appear in validator {validator_name!r}; "
                "confirm validator runs before the pipeline."
            ),
        ))
    return findings


def scan(path: Path) -> list[PipelineFinding]:
    return scan_source(path, path.read_text(encoding="utf-8"))


def scan_repo(repo_root: Path, include_tests: bool = False) -> list[PipelineFinding]:
    findings: list[PipelineFinding] = []
    for py in repo_root.rglob("*.py"):
        rel = py.relative_to(repo_root)
        parts = rel.parts
        if not include_tests and "tests" in parts:
            continue
        if any(p.startswith(".") for p in parts):
            continue
        findings.extend(scan(py))
    return findings


def _format(finding: PipelineFinding) -> str:
    descs = ", ".join(finding.stage_descriptors) or "(unknown pattern)"
    return (
        f"  {finding.file}:{finding.line}  function {finding.function!r}\n"
        f"    pattern: {descs}\n"
        f"    validator: {finding.validator_function}; shared fields: {list(finding.shared_fields)}\n"
        f"    {finding.message}"
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipeline_inversion_lint")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", help="single python file to scan")
    group.add_argument("--repo-root", help="directory to recursively scan")
    parser.add_argument("--include-tests", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.check:
        p = Path(args.check)
        if not p.exists():
            print(f"pipeline_inversion_lint: no such file: {p}", file=sys.stderr)
            return 2
        findings = scan(p)
    else:
        root = Path(args.repo_root)
        if not root.exists():
            print(f"pipeline_inversion_lint: no such directory: {root}", file=sys.stderr)
            return 2
        findings = scan_repo(root, include_tests=args.include_tests)
    if not findings:
        return 0
    print("pipeline_inversion_lint: composition-defect candidate(s) detected", file=sys.stderr)
    for f in findings:
        print(_format(f), file=sys.stderr)
    print(f"exit: 1 ({len(findings)} finding(s))", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
