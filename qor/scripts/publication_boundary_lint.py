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
from dataclasses import dataclass
from pathlib import Path

_SELF_REPO = "MythologIQ-Labs-LLC/Qor-logic"

_ABS_PATH_RE = re.compile(r"(?<![\w./-])(?:[A-Za-z]:[/\\]|/Users/|/home/)[\w./\\-]+")
_GH_URL_RE = re.compile(r"github\.com/([\w.-]+/[\w.-]+)")
_CROSS_ISSUE_RE = re.compile(r"\b([A-Z][\w-]{2,})#\d+\b")
# Phase 208: record an exception the doctrine already grants, on the line that
# earns it. Mirrors prose_test_lint's `# prose-lint: ok=<reason>` allowlist; the
# comment prefix is dropped so one marker works in Markdown, Python, and YAML.
# The reason is required (`\S`), so an empty marker cannot silence the control.
# Scope is per line: no wildcard, no per-file or directory suppression.
_ALLOW_RE = re.compile(r"boundary-lint:\s*ok=(\S[^\s>]*)")

_TEXT_SUFFIXES = {".md", ".py", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".txt", ".cfg", ".ini"}
_SKIP_PARTS = {".git", "node_modules", "__pycache__"}
# Phase 208: the second exception doctrine-publication-boundary already grants.
# `qor/vendor/` is third-party material whose upstream attribution is legally
# required text, so its identities are not this repository's to anonymize. The
# grant predates this lint; expressing it here is what lets the control reach a
# satisfiable state and therefore be wired to a gate.
_CARVE_OUT_PREFIXES = ("qor/vendor/",)


def _git_list(repo_root: Path, *args: str) -> list[str] | None:
    result = subprocess.run(["git", "-C", str(repo_root), "ls-files", *args],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line.strip()]


def _tracked_files(repo_root: Path, no_git: bool) -> list[Path]:
    """Every file that could reach the published surface.

    The index (`ls-files`) plus untracked-not-ignored (`--others
    --exclude-standard`). GH #309: staged files were already covered -- the
    index is what `ls-files` lists -- but UNTRACKED ones were not, and untracked
    is the state every artifact is in when a phase produces it. Four leaks
    passed four green runs that way.

    `--exclude-standard` honors .gitignore, so build output and the operator's
    private terms overlay stay out. Ignored files are not published, and reading
    the overlay would surface the denylist the boundary exists to keep out.
    """
    if not no_git:
        listed = _git_list(repo_root)
        if listed is not None:
            others = _git_list(repo_root, "--others", "--exclude-standard") or []
            seen = dict.fromkeys(listed + others)
            return [repo_root / line for line in seen]
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
        if _ALLOW_RE.search(line):
            continue
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


@dataclass(frozen=True)
class BoundaryResult:
    """Findings plus the detector scope that produced them.

    CI cannot load the identity overlay (it is gitignored by design), so a bare
    "0 findings" from CI and from a local run mean different things. The scope
    travels with the result so a reader can tell which one they have.
    """

    findings: list[str]
    scope: str


def collect_findings(
    repo_root: Path,
    *,
    no_git: bool = False,
    terms_file: Path | None = None,
) -> BoundaryResult:
    """Scan the publishable surface and report what was examined."""
    if terms_file is None:
        terms_file = repo_root / ".qor" / "private" / "boundary-terms.txt"
    terms = _load_terms(terms_file)
    findings: list[str] = []
    self_name = Path(__file__).name
    for path in _tracked_files(repo_root, no_git):
        if path.suffix.lower() not in _TEXT_SUFFIXES or path.name == self_name:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(repo_root))
        if rel.replace("\\", "/").startswith(_CARVE_OUT_PREFIXES):
            continue
        findings.extend(scan_text(rel, text, terms))
    return BoundaryResult(findings, "structural+identity" if terms else "structural")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", type=Path, default=Path.cwd())
    ap.add_argument("--terms-file", type=Path, default=None,
                    help="operator-local identity terms (default .qor/private/boundary-terms.txt)")
    ap.add_argument("--no-git", action="store_true",
                    help="walk the filesystem instead of git ls-files (test fixtures)")
    args = ap.parse_args(argv)
    result = collect_findings(
        args.repo_root, no_git=args.no_git, terms_file=args.terms_file)
    for f in result.findings[:200]:
        print(f)
    print(f"publication_boundary_lint: {len(result.findings)} finding(s) "
          f"[scope: {result.scope}]")
    return 1 if result.findings else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
