"""Structural publication-boundary lint (Phase 172).

Enforces qor/references/doctrine-publication-boundary.md WITHOUT itself
naming any outside identity: a tracked denylist of private identifiers in a
public repository would violate the boundary it enforces. Tracked, structural
patterns only -- absolute local path shapes, GitHub URLs whose owner/repo is
not this repository, and cross-repository issue shapes -- plus an OPTIONAL
operator-local terms file (default ``.qor/private/boundary-terms.txt``,
gitignored) supplying identity terms for local verification. Exit 1 on
findings (the audit Step 0.6 ladder wraps ``|| true``).
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

_SELF_REPO = "MythologIQ-Labs-LLC/Qor-logic"

_ABS_PATH_RE = re.compile(r"(?<![\w./-])(?:[A-Za-z]:[/\\]|/Users/|/home/)[\w./\\-]+")
_GH_URL_RE = re.compile(r"github\.com/([\w.-]+/[\w.-]+)")
_CROSS_ISSUE_RE = re.compile(r"\b([A-Z][\w-]{2,})#\d+\b")

_TEXT_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".txt", ".cfg", ".ini"}
_SKIP_PARTS = {".git", "node_modules", "__pycache__"}


def _tracked_files(repo_root: Path, no_git: bool) -> list[Path]:
    if not no_git:
        result = subprocess.run(["git", "-C", str(repo_root), "ls-files"],
                                capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return [repo_root / line for line in result.stdout.splitlines() if line.strip()]
    return [p for p in repo_root.rglob("*")
            if p.is_file() and not (_SKIP_PARTS & set(p.parts))]


def _load_terms(terms_file: Path | None) -> list[str]:
    if terms_file is None or not terms_file.is_file():
        return []
    terms = []
    for line in terms_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            terms.append(line)
    return terms


def scan_text(rel: str, text: str, terms: list[str]) -> list[str]:
    findings: list[str] = []
    for i, line in enumerate(text.splitlines(), start=1):
        for m in _ABS_PATH_RE.finditer(line):
            findings.append(f"[boundary] {rel}:{i}: absolute local path: {m.group(0)[:60]}")
        for m in _GH_URL_RE.finditer(line):
            if m.group(1).lower() != _SELF_REPO.lower():
                findings.append(f"[boundary] {rel}:{i}: foreign repository URL: {m.group(1)}")
        for m in _CROSS_ISSUE_RE.finditer(line):
            findings.append(f"[boundary] {rel}:{i}: cross-repo issue shape: {m.group(0)}")
        for term in terms:
            if term.lower() in line.lower():
                findings.append(f"[boundary] {rel}:{i}: identity term: {term}")
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--terms-file", type=Path, default=None,
                    help="operator-local identity terms (default .qor/private/boundary-terms.txt)")
    ap.add_argument("--no-git", action="store_true",
                    help="walk the filesystem instead of git ls-files (test fixtures)")
    args = ap.parse_args(argv)
    root = args.repo_root
    terms_file = args.terms_file or (root / ".qor" / "private" / "boundary-terms.txt")
    terms = _load_terms(terms_file)
    findings: list[str] = []
    self_name = Path(__file__).name
    for path in _tracked_files(root, args.no_git):
        if path.suffix.lower() not in _TEXT_SUFFIXES or path.name == self_name:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(root))
        findings.extend(scan_text(rel, text, terms))
    for f in findings[:200]:
        print(f)
    print(f"publication_boundary_lint: {len(findings)} finding(s)"
          + (f" (terms overlay: {len(terms)} terms)" if terms else " (structural only)"))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
