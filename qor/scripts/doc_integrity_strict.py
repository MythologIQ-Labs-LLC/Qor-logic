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
            if _excluded_by_scope_fence(entry, rel, glossary_rel):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            if pattern.search(text):
                msg = f"Term '{entry.term}' used in {rel} not declared as referenced_by"
                if strict:
                    raise ValueError(msg)
                findings.append(msg)
    return findings


_DOCS_LIVING = frozenset({
    "docs/architecture.md",
    "docs/lifecycle.md",
    "docs/operations.md",
    "docs/policies.md",
})


def _excluded_by_scope_fence(entry, rel: str, glossary_rel: str) -> bool:
    """Phase 31 + 32 scope-fence tuning. True if `rel` should NOT be scanned for
    the given glossary entry's term."""
    if rel in entry.referenced_by or rel == entry.home or rel == glossary_rel:
        return True
    scope_exclude = getattr(entry, "scope_exclude", None) or []
    if rel in scope_exclude:
        return True
    if "qor/references/doctrine-" in entry.home and "qor/references/doctrine-" in rel:
        return True
    home_dir = entry.home.rsplit("/", 1)[0] if "/" in entry.home else ""
    rel_dir = rel.rsplit("/", 1)[0] if "/" in rel else ""
    if home_dir and home_dir == rel_dir:
        return True
    # Phase 32: docs/*.md is archive-by-default except the 4 system-tier docs.
    # Living docs (architecture/lifecycle/operations/policies) are legitimate
    # consumers and must be adopted into term's referenced_by when used.
    # All other docs/ content is historical (plans, ledger, archives, research
    # briefs, self-audits, snapshots) and doesn't need adoption.
    if rel.startswith("docs/") and rel not in _DOCS_LIVING:
        return True
    # README + CHANGELOG are narrative entry points that mention every major
    # term; they are not glossary consumers in the referenced_by sense.
    if rel in ("README.md", "CHANGELOG.md"):
        return True
    return False


_DEF_PATTERN_TMPL = r"\b{term}\s+(?:is|means|refers to)\s+([^.\n]{{10,200}})"


_CURRENCY_TRIGGER_PATTERNS = (
    "qor/skills/",  # SKILL.md edits
    "qor/references/doctrine-",
    "qor/gates/schema/",
    "qor/scripts/",
)
_SYSTEM_TIER_DOCS = (
    "docs/architecture.md",
    "docs/lifecycle.md",
    "docs/operations.md",
    "docs/policies.md",
)


def check_documentation_currency(implement_payload: dict, repo_root: str) -> list[str]:
    """Check whether doc-affecting phase changes updated system-tier docs.

    Heuristic: if files_touched contains any SKILL.md / doctrine / schema /
    script AND no system-tier doc is in files_touched, return a warning
    list. Else return empty list. Phase 31 wiring uses WARN semantics
    (operator decides) rather than BLOCK.
    """
    files_touched = implement_payload.get("files_touched", [])
    normalized = [f.replace("\\", "/") for f in files_touched]
    trigger_files = [
        f for f in normalized
        if any(p in f for p in _CURRENCY_TRIGGER_PATTERNS)
    ]
    if not trigger_files:
        return []
    system_doc_touched = any(d in normalized for d in _SYSTEM_TIER_DOCS)
    if system_doc_touched:
        return []
    return [
        f"Doc-affecting change to {f} without updating any system-tier doc "
        f"({', '.join(_SYSTEM_TIER_DOCS)})"
        for f in trigger_files
    ]


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
    glossary_rel = Path(glossary_path).relative_to(repo).as_posix() if Path(glossary_path).is_absolute() else "qor/references/glossary.md"
    for entry in entries:
        pattern = re.compile(
            _DEF_PATTERN_TMPL.format(term=re.escape(entry.term)),
            re.IGNORECASE,
        )
        for f in _iter_scan_files(repo_root):
            rel = f.relative_to(repo).as_posix()
            # Phase 32: E shares D's scope fence (archives + home/peer exclusions)
            if _excluded_by_scope_fence(entry, rel, glossary_rel):
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
