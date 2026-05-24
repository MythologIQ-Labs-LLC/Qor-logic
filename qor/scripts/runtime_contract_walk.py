"""Phase 99: audit-side runtime contract walk (GH #108 V2).

Walks the import graph one hop in each direction for any Python module
path cited in a plan's Affected Files or body text:

- Forward (callees): the cited module's own import statements all parse
  without error in the project's actual environment.
- Backward (callers): at least one production (non-test, non-scratch,
  non-doc) caller of the cited module exists and parses without error.

Wired into /qor-audit Step 3 Infrastructure Alignment Pass as a NEW
sub-check. V2 starts WARN-only (--exit-on-any is the operator-opt-in
flag) pending operator evidence on Phase 96 V1 false-positive rate;
a future V2-of-V2 phase converts WARN to hard VETO.

See qor/references/audit-runtime-contract-walk.md for the detailed
protocol and SG-GrepShapedRunclaim-A for the binding doctrine.
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WalkFinding:
    module_path: str
    direction: str  # 'forward' or 'backward'
    detail: str
    severity: str = "warn"


_MODULE_RE = re.compile(r"`(qor(?:\.[a-z_][a-z0-9_]*)+)`")
_FILE_PATH_RE = re.compile(r"`(qor/[a-z0-9_/.\-]+\.py)`", re.IGNORECASE)


def extract_python_modules_from_plan(plan_path: Path) -> list[str]:
    """Parse plan text for cited Python module paths.

    Recognizes:
    - Dotted module references in backticks: `qor.scripts.foo`
    - File paths in backticks: `qor/scripts/foo.py` (converted to dotted)
    """
    text = plan_path.read_text(encoding="utf-8")
    modules: set[str] = set()
    for match in _MODULE_RE.finditer(text):
        modules.add(match.group(1))
    for match in _FILE_PATH_RE.finditer(text):
        path = match.group(1)
        if path.endswith(".py"):
            dotted = path[:-3].replace("/", ".")
            if dotted.startswith("qor."):
                modules.add(dotted)
    return sorted(modules)


def _is_production_caller(rel_path: Path) -> bool:
    parts = set(rel_path.parts)
    if "tests" in parts or "test" in parts:
        return False
    if ".agent" in parts or ".claude" in parts or ".qor" in parts:
        return False
    if "docs" in parts:
        return False
    if rel_path.suffix != ".py":
        return False
    return True


def walk_forward(module_path: str, repo_root: Path) -> list[WalkFinding]:
    """Parse the module's own import statements; flag any that fail."""
    rel = Path(*module_path.split(".")).with_suffix(".py")
    module_file = repo_root / rel
    if not module_file.exists():
        package_init = repo_root / Path(*module_path.split(".")) / "__init__.py"
        if package_init.exists():
            module_file = package_init
        else:
            return [WalkFinding(
                module_path=module_path,
                direction="forward",
                detail=f"module file not found at {rel} (cannot walk forward)",
            )]
    try:
        source = module_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(module_file))
    except (SyntaxError, OSError, UnicodeDecodeError) as exc:
        return [WalkFinding(
            module_path=module_path,
            direction="forward",
            detail=f"cited module fails to parse: {type(exc).__name__}: {exc}",
        )]
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    findings: list[WalkFinding] = []
    for imp in imports:
        if not imp.startswith("qor."):
            continue
        result = subprocess.run(
            [sys.executable, "-c", f"import {imp}"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            stderr_tail = (result.stderr or "").strip().splitlines()[-2:]
            findings.append(WalkFinding(
                module_path=module_path,
                direction="forward",
                detail=f"callee {imp!r} fails import: {' | '.join(stderr_tail)}",
            ))
    return findings


def walk_backward(module_path: str, repo_root: Path) -> list[WalkFinding]:
    """At least one production caller imports the module and parses cleanly."""
    needle = module_path
    self_file = repo_root / Path(*module_path.split(".")).with_suffix(".py")
    self_resolved = self_file.resolve() if self_file.exists() else None
    parseable_caller_found = False
    for py_file in repo_root.rglob("*.py"):
        rel = py_file.relative_to(repo_root)
        if not _is_production_caller(rel):
            continue
        if self_resolved and py_file.resolve() == self_resolved:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle not in text:
            continue
        try:
            ast.parse(text, filename=str(py_file))
        except SyntaxError:
            continue
        parseable_caller_found = True
        break
    if not parseable_caller_found:
        return [WalkFinding(
            module_path=module_path,
            direction="backward",
            detail=f"no production caller imports/invokes {module_path}",
        )]
    return []


def walk_plan(plan_path: Path, repo_root: Path) -> list[WalkFinding]:
    modules = extract_python_modules_from_plan(plan_path)
    findings: list[WalkFinding] = []
    for module in modules:
        findings.extend(walk_forward(module, repo_root))
        findings.extend(walk_backward(module, repo_root))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="runtime_contract_walk")
    parser.add_argument("--plan", type=Path, required=True,
                        help="Path to the plan being audited")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--exit-on-any", action="store_true",
                        help="Exit 1 when any finding (V2 WARN-only by default)")
    args = parser.parse_args(argv)
    findings = walk_plan(args.plan, args.repo_root)
    if not findings:
        print("runtime_contract_walk: 0 finding(s)")
        return 0
    print(f"runtime_contract_walk: {len(findings)} finding(s)")
    for f in findings:
        print(f"  [{f.severity.upper()}] {f.direction}: {f.module_path} -- {f.detail}")
    return 1 if args.exit_on_any else 0


if __name__ == "__main__":
    sys.exit(main())
