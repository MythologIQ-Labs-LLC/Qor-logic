"""Strict-mode check surfaces for documentation integrity (Phase 30 Phase 4).

Sibling module to doc_integrity.py, keeping the core under the 250-line
Razor cap. Hosts the Phase 4 Check Surface D (term-drift grep) and
E (cross-doc conflict detection) plus their scope fences.

Both checks ship lenient-by-default (strict=False): lenient mode returns
a list of drift findings without raising. Strict mode raises on the first
finding. Phase 30 wires lenient; strict-mode wiring into
/qor-substantiate Step 4.7 is deferred to a future phase when the repo
is known-clean.
"""
from __future__ import annotations

import re
from pathlib import Path

from doc_integrity import parse_glossary


_STRICT_SCAN_ROOTS = (
    "qor/references",
    "qor/gates",
    "qor/skills",
    "docs",
)
_STRICT_SCAN_ROOT_FILES = ("CLAUDE.md", "CONTRIBUTING.md", "README.md", "CHANGELOG.md")
_STRICT_EXCLUDE_SUFFIXES = (".py", ".json", ".toml", ".cedar")
_STRICT_EXCLUDE_DIRS = ("vendor", "fixtures", "dist")


def _iter_scan_files(repo_root: str):
    root = Path(repo_root)
    for rel in _STRICT_SCAN_ROOTS:
        base = root / rel
        if not base.exists():
            continue
        for p in base.rglob("*.md"):
            if any(part in _STRICT_EXCLUDE_DIRS for part in p.parts):
                continue
            yield p
    for name in _STRICT_SCAN_ROOT_FILES:
        p = root / name
        if p.exists():
            yield p


def check_term_drift(
    glossary_path: str,
    repo_root: str,
    strict: bool = False,
) -> list[str]:
    """Detect canonical glossary terms used in scan-in-scope files whose
    file path is not in the term's referenced_by list.

    Returns a list of drift findings (empty if clean). Raises ValueError
    on the first finding when strict=True.
    """
    entries = parse_glossary(glossary_path)
    findings: list[str] = []
    repo = Path(repo_root)
    glossary_rel = Path(glossary_path).relative_to(repo).as_posix() if Path(glossary_path).is_absolute() else "qor/references/glossary.md"
    for entry in entries:
        pattern = re.compile(r"\b" + re.escape(entry.term) + r"\b")
        for f in _iter_scan_files(repo_root):
            rel = f.relative_to(repo).as_posix()
            if rel in entry.referenced_by or rel == entry.home or rel == glossary_rel:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            if pattern.search(text):
                msg = f"Term '{entry.term}' used in {rel} not declared as referenced_by"
                if strict:
                    raise ValueError(msg)
                findings.append(msg)
    return findings


_DEF_PATTERN_TMPL = r"\b{term}\s+(?:is|means|refers to)\s+([^.\n]{{10,200}})"


def check_cross_doc_conflicts(
    glossary_path: str,
    repo_root: str,
    strict: bool = False,
) -> list[str]:
    """Detect sentences defining a glossary term with a body that does not
    match the canonical definition (exact-text comparison).

    Lenient mode returns finding list; strict mode raises on the first.
    """
    entries = parse_glossary(glossary_path)
    findings: list[str] = []
    repo = Path(repo_root)
    for entry in entries:
        pattern = re.compile(
            _DEF_PATTERN_TMPL.format(term=re.escape(entry.term)),
            re.IGNORECASE,
        )
        for f in _iter_scan_files(repo_root):
            rel = f.relative_to(repo).as_posix()
            if rel == entry.home or rel == "qor/references/glossary.md":
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            for match in pattern.finditer(text):
                found_def = match.group(1).strip()
                canonical = entry.definition.strip()
                if found_def.lower() not in canonical.lower() and canonical.lower() not in found_def.lower():
                    msg = (
                        f"Term '{entry.term}' defined in {rel} with body "
                        f"diverging from canonical glossary definition"
                    )
                    if strict:
                        raise ValueError(msg)
                    findings.append(msg)
                    break
    return findings
