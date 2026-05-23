"""Phase 96: recon reachability probe (GH #108 V1).

Runs five checks against a recon-style claim and emits findings for
any that fail. WARN-only in V1; the operator (or Phase 99 V2 in
/qor-audit) decides whether a failing probe downgrades a finding from
HIGH to reachability-gap.

The five checks:

1. Importability  -- the symbol can be imported from a clean Python process
2. Test collection -- at least one test exercising the surface collects cleanly
3. Caller graph   -- at least one production code path (non-test, non-scratch)
                     imports/invokes the cited surface
4. Packaging      -- the cited path is in the production build manifest
5. Interface match -- call-site name/signature matches the called module's
                      current export

See qor/references/recon-reachability-probe.md for the detailed protocol.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass(frozen=True)
class Claim:
    """One recon-style claim.

    `module`: dotted module path (e.g. "qor.scripts.reachability_probe").
    `symbol`: optional symbol within the module (e.g. "check_claim").
    `file_path`: path to the file backing the module, relative to repo root.
    `call_site`: optional 'file:line' where the surface is invoked.
    """
    module: str
    symbol: str | None
    file_path: str
    call_site: str | None = None


@dataclass(frozen=True)
class ReachabilityFinding:
    claim_module: str
    claim_symbol: str | None
    category: str
    detail: str
    severity: str = "warn"


# --- check 1: importability -------------------------------------------------

def check_importability(claim: Claim, repo_root: Path) -> ReachabilityFinding | None:
    """Spawn a fresh python process and try the import."""
    if claim.symbol:
        code = f"from {claim.module} import {claim.symbol}"
    else:
        code = f"import {claim.module}"
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-importability-failed",
            detail="import probe timed out after 20s",
        )
    if result.returncode != 0:
        stderr_tail = (result.stderr or "").strip().splitlines()[-3:]
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-importability-failed",
            detail=f"import failed: {' | '.join(stderr_tail)}",
        )
    return None


# --- check 2: test collection -----------------------------------------------

def check_test_collection(claim: Claim, repo_root: Path) -> ReachabilityFinding | None:
    """Look for tests touching the symbol or module; require at least one to collect.

    The test-discovery heuristic: walk tests/ for files importing the module
    or referring to the symbol. Then run `pytest --collect-only` against each
    matching test file; the check passes if at least one collects without
    error.
    """
    tests_dir = repo_root / "tests"
    if not tests_dir.is_dir():
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-test-collection-failed",
            detail="tests/ directory not found",
        )
    needle_module = claim.module
    needle_symbol = claim.symbol or ""
    candidates: list[Path] = []
    for test_file in tests_dir.rglob("test_*.py"):
        try:
            text = test_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle_module in text or (needle_symbol and needle_symbol in text):
            candidates.append(test_file)
    if not candidates:
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-test-collection-failed",
            detail="no test file references this module/symbol",
        )
    for candidate in candidates:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q", str(candidate)],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            continue
        if result.returncode == 0:
            return None
    return ReachabilityFinding(
        claim_module=claim.module,
        claim_symbol=claim.symbol,
        category="reachability-test-collection-failed",
        detail=f"{len(candidates)} candidate test file(s) failed to collect",
    )


# --- check 3: caller graph --------------------------------------------------

def _is_production_caller(rel_path: Path) -> bool:
    parts = set(rel_path.parts)
    if "tests" in parts or "test" in parts:
        return False
    if ".agent" in parts or ".claude" in parts:
        return False
    if ".qor" in parts or "docs" in parts:
        return False
    if rel_path.suffix not in {".py"}:
        return False
    return True


def check_caller_graph(claim: Claim, repo_root: Path) -> ReachabilityFinding | None:
    """At least one production .py file imports the module or symbol."""
    needle_module = claim.module
    needle_symbol = claim.symbol
    self_path = (repo_root / claim.file_path).resolve()
    for py_file in repo_root.rglob("*.py"):
        rel = py_file.relative_to(repo_root)
        if not _is_production_caller(rel):
            continue
        if py_file.resolve() == self_path:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle_module in text or (needle_symbol and needle_symbol in text):
            return None
    return ReachabilityFinding(
        claim_module=claim.module,
        claim_symbol=claim.symbol,
        category="reachability-no-production-caller",
        detail=f"no production caller imports/invokes {claim.module}",
    )


# --- check 4: packaging -----------------------------------------------------

def check_packaging(claim: Claim, repo_root: Path,
                    manifest_path: Path | None = None) -> ReachabilityFinding | None:
    """The claimed file path is present in the production build manifest.

    If manifest_path is None, we attempt to find pyproject.toml's
    `tool.setuptools.packages.find` or `tool.poetry.packages` and verify
    the module's top-level package is included. If neither exists, we
    flag the manifest as missing.
    """
    if manifest_path is None:
        manifest_path = repo_root / "pyproject.toml"
    if not manifest_path.exists():
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-packaging-missing",
            detail=f"manifest not found at {manifest_path}",
        )
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-packaging-missing",
            detail=f"cannot read manifest: {exc}",
        )
    top_package = claim.module.split(".")[0]
    if top_package in text or claim.file_path.replace("\\", "/") in text:
        return None
    return ReachabilityFinding(
        claim_module=claim.module,
        claim_symbol=claim.symbol,
        category="reachability-packaging-missing",
        detail=f"top-level package {top_package!r} not referenced in manifest",
    )


# --- check 5: interface match ----------------------------------------------

def _extract_signature(module_file: Path, symbol: str) -> str | None:
    try:
        source = module_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            args = [a.arg for a in node.args.args]
            return ",".join(args)
        if isinstance(node, ast.ClassDef) and node.name == symbol:
            return f"class:{symbol}"
    return None


_CALL_RE = re.compile(r"\b(\w+)\s*\(([^)]*)\)")


def _extract_call_signature(call_site_path: Path, symbol: str) -> str | None:
    try:
        text = call_site_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    for match in _CALL_RE.finditer(text):
        name, args_str = match.group(1), match.group(2)
        if name != symbol:
            continue
        args = [a.strip().split("=")[0].strip() for a in args_str.split(",") if a.strip()]
        return ",".join(args)
    return None


def check_interface_match(claim: Claim, repo_root: Path) -> ReachabilityFinding | None:
    """Compare module-exported signature against call-site invocation."""
    if not claim.symbol or not claim.call_site:
        return None
    module_file = repo_root / claim.file_path
    exported = _extract_signature(module_file, claim.symbol)
    if exported is None:
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-interface-mismatch",
            detail=f"symbol {claim.symbol!r} not found in {claim.file_path}",
        )
    if exported.startswith("class:"):
        return None
    call_site_file, _, _line = claim.call_site.partition(":")
    invoked = _extract_call_signature(repo_root / call_site_file, claim.symbol)
    if invoked is None:
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-interface-mismatch",
            detail=f"call site {claim.call_site!r} does not invoke {claim.symbol!r}",
        )
    exp_arity = len(exported.split(",")) if exported else 0
    inv_arity = len(invoked.split(",")) if invoked else 0
    if exp_arity != inv_arity:
        return ReachabilityFinding(
            claim_module=claim.module,
            claim_symbol=claim.symbol,
            category="reachability-interface-mismatch",
            detail=f"signature drift: module exports ({exported}) but call site invokes ({invoked})",
        )
    return None


# --- top-level driver -------------------------------------------------------

def check_claim(claim: Claim, repo_root: Path,
                manifest_path: Path | None = None) -> list[ReachabilityFinding]:
    """Run all five checks; return findings for failing ones."""
    findings: list[ReachabilityFinding] = []
    for check in (
        lambda: check_importability(claim, repo_root),
        lambda: check_test_collection(claim, repo_root),
        lambda: check_caller_graph(claim, repo_root),
        lambda: check_packaging(claim, repo_root, manifest_path),
        lambda: check_interface_match(claim, repo_root),
    ):
        finding = check()
        if finding is not None:
            findings.append(finding)
    return findings


def _load_claims(path: Path) -> list[Claim]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    return [
        Claim(
            module=item["module"],
            symbol=item.get("symbol"),
            file_path=item["file_path"],
            call_site=item.get("call_site"),
        )
        for item in data
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reachability_probe")
    parser.add_argument("--claims", type=Path, required=True,
                        help="JSON file with one claim object or a list of them")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, default=None,
                        help="Path to pyproject.toml or equivalent manifest")
    parser.add_argument("--exit-on-any", action="store_true",
                        help="Exit 1 when any finding is present (default exit 0; V1 WARN-only)")
    args = parser.parse_args(argv)
    claims = _load_claims(args.claims)
    all_findings: list[ReachabilityFinding] = []
    for claim in claims:
        all_findings.extend(check_claim(claim, args.repo_root, args.manifest))
    if not all_findings:
        print("reachability_probe: 0 finding(s)")
        return 0
    print(f"reachability_probe: {len(all_findings)} finding(s)")
    for f in all_findings:
        print(f"  [{f.severity.upper()}] {f.category}: {f.claim_module}::{f.claim_symbol} -- {f.detail}")
    if args.exit_on_any:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
