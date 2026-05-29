"""Shared helpers for pre-audit plan lints (Phase 110, SG-AffectedFilesContract-A).

Centralizes the repo caller-discovery used by both
``plan_signature_widening_caller_lint`` (#133) and ``audit_risk_score``'s
signature-widening-cascade signal (#135), per the #135 de-duplication note.
"""
from __future__ import annotations

import re
from pathlib import Path

_SOURCE_SUFFIXES = {".rs", ".py", ".ts", ".tsx"}
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "target", "dist", "build"}
_SKIP_LINE_PREFIXES = ("assert!", "debug_assert!", "dbg!")


def _iter_sources(repo_root: Path):
    for path in repo_root.rglob("*"):
        if path.suffix not in _SOURCE_SUFFIXES or not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def find_callers(name: str, repo_root: Path) -> set[str]:
    """Repo-relative posix paths of source files with a free-function call to
    ``name`` (``name(`` not preceded by ``.`` or a word char, so method calls
    ``obj.name(`` and substrings ``xname(`` are excluded). Assertion-macro lines
    are skipped. The caller need not exclude the definition file; the lint does.
    """
    repo_root = Path(repo_root)
    pattern = re.compile(rf"(?<![.\w]){re.escape(name)}\s*\(")
    hits: set[str] = set()
    for path in _iter_sources(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if any(line.lstrip().startswith(pre) for pre in _SKIP_LINE_PREFIXES):
                continue
            if pattern.search(line):
                hits.add(path.relative_to(repo_root).as_posix())
                break
    return hits
