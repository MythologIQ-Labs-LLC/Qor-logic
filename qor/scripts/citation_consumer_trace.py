"""Citation consumer-trace (Phase 126; GH #157).

Executable form of the Phase 83 Infrastructure-Alignment consumer-trace sub-check
(`qor-audit/references/phase37-subpasses.md`): verify a cited code symbol is
reachable from the entry-point surface the plan claims to fix, via the file's
transitive in-repo import graph. A lexical grep-recursive trace (not an AST
call-graph), matching the issue's framing.

Operator supplies (entry, symbol) per Locked Decision under review. An unreached
citation is dead code / a wrong citation -> `infrastructure-mismatch`.
"""
from __future__ import annotations

import argparse
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path

_PY_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+(\.*[\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE
)
_JS_IMPORT_RE = re.compile(r"""(?:from|require\()\s*['"]([^'"]+)['"]""")
_CODE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx")
_JS_RESOLVE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.js")


@dataclass(frozen=True)
class TraceResult:
    reachable: bool
    skipped: bool
    visited: tuple[str, ...]


def _under_root(path: Path, repo_root: Path) -> Path | None:
    try:
        resolved = path.resolve()
        resolved.relative_to(repo_root.resolve())
    except (ValueError, OSError):
        return None
    return resolved


def _resolve_python(module: str, base_file: Path, repo_root: Path) -> Path | None:
    if module.startswith("."):
        # relative import: leading dots climb from base_file's dir
        dots = len(module) - len(module.lstrip("."))
        rest = module[dots:]
        anchor = base_file.parent
        for _ in range(dots - 1):
            anchor = anchor.parent
        parts = rest.split(".") if rest else []
    else:
        anchor = repo_root
        parts = module.split(".")
    if not parts:
        return None
    base = anchor.joinpath(*parts)
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        ok = _under_root(candidate, repo_root)
        if ok and ok.is_file():
            return ok
    return None


def _resolve_js(spec: str, base_file: Path, repo_root: Path) -> Path | None:
    if not spec.startswith("."):
        return None  # bare specifier -> node_modules / external
    base = (base_file.parent / spec)
    for suffix in ("",) + _JS_RESOLVE_SUFFIXES:
        candidate = Path(str(base) + suffix)
        ok = _under_root(candidate, repo_root)
        if ok and ok.is_file():
            return ok
    return None


def resolve_imports(text: str, base_file: Path, repo_root: Path) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for m in _PY_IMPORT_RE.finditer(text):
        module = m.group(1) or m.group(2)
        resolved = _resolve_python(module, base_file, repo_root) if module else None
        if resolved and resolved not in seen:
            seen.add(resolved)
            out.append(resolved)
    if base_file.suffix in (".ts", ".tsx", ".js", ".jsx"):
        for m in _JS_IMPORT_RE.finditer(text):
            resolved = _resolve_js(m.group(1), base_file, repo_root)
            if resolved and resolved not in seen:
                seen.add(resolved)
                out.append(resolved)
    return out


def trace_reachable(
    repo_root: Path, entry_path: Path, symbol: str, max_depth: int = 5
) -> TraceResult:
    if not entry_path.is_file():
        return TraceResult(reachable=False, skipped=True, visited=())
    sym_re = re.compile(rf"\b{re.escape(symbol)}\b")
    visited: set[Path] = set()
    order: list[str] = []
    queue: deque[tuple[Path, int]] = deque([(entry_path.resolve(), 0)])
    while queue:
        current, depth = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        try:
            text = current.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        order.append(current.relative_to(repo_root.resolve()).as_posix())
        if sym_re.search(text):
            return TraceResult(reachable=True, skipped=False, visited=tuple(order))
        if depth < max_depth:
            for imp in resolve_imports(text, current, repo_root):
                if imp not in visited:
                    queue.append((imp, depth + 1))
    return TraceResult(reachable=False, skipped=False, visited=tuple(order))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="citation_consumer_trace")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--entry", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--max-depth", type=int, default=5)
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    result = trace_reachable(repo_root, Path(args.entry), args.symbol, args.max_depth)
    if result.skipped:
        print(f"SKIP: entry file {args.entry} not found (consumer-trace not run)")
        return 0
    if result.reachable:
        print(f"OK: '{args.symbol}' reachable from {args.entry} "
              f"(walked {len(result.visited)} file(s))")
        return 0
    print(f"[infrastructure-mismatch] '{args.symbol}' is NOT reachable from "
          f"{args.entry} (walked {len(result.visited)} file(s)) -- dead code or "
          f"wrong symbol cited")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
