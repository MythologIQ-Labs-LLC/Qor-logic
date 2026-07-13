"""Shared canonical governance-path resolver (GH #282).

One resolver answers the two questions gates previously hardcoded:

- which file is the repository's architecture authority (system-tier topology)?
- is a given plan path a registered, in-root governance file (canary scanning)?

Registration parsing is reused from ``governance_index`` so there is exactly
one registration source of truth. Every resolution is fail-closed: missing,
ambiguous, unregistered, outside-root, or non-governance inputs raise
``GovernancePathError`` before any file is read.
"""
from __future__ import annotations

import re
from pathlib import Path

from qor.scripts import governance_index as gi

_INDEX_REL = "docs/GOVERNANCE_INDEX.md"
_LEGACY_ARCH = "docs/architecture.md"
_GOVERNANCE_SUFFIXES = frozenset({".md"})

# Families that are governance files by convention and need no explicit index
# row (mirrors the historical prompt-injection allowlist so its tests stay green
# without a governance index present).
_ALWAYS_ALLOWED_RE = re.compile(
    r"^(docs/plan-qor-phase\d+[a-z]*-[a-z0-9-]+\.md"
    r"|docs/(ARCHITECTURE_PLAN|META_LEDGER|CONCEPT)\.md"
    r"|docs/research-brief-[a-z0-9-]+\.md"
    r"|qor/references/doctrine-[a-z0-9-]+\.md)$"
)


class GovernancePathError(ValueError):
    """Fail-closed governance-path resolution failure."""


def _read_index(root: Path) -> str | None:
    path = root / _INDEX_REL
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None


def _within_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _is_architecture_name(rel: str) -> bool:
    stem = Path(rel).stem.lower()
    return stem == "architecture" or stem.startswith(("architecture_", "architecture-"))


def resolve_architecture_authority(repo_root: str | Path) -> Path:
    """Return the sole architecture authority for ``repo_root``.

    Index present: the legacy literal ``docs/architecture.md`` wins when it
    exists and is registered (zero behavior change for repos that keep it);
    otherwise the single registered architecture-stemmed doc is resolved.
    Index absent: the legacy literal is the fallback. Raises
    ``GovernancePathError`` on missing / multiple / outside-root inputs.
    """
    root = Path(repo_root)
    index_text = _read_index(root)
    legacy = root / _LEGACY_ARCH
    if index_text is None:
        if legacy.is_file():
            return legacy
        raise GovernancePathError(
            "no governance index and no docs/architecture.md present"
        )
    registered = gi._registered_paths(index_text)
    if legacy.is_file() and gi._is_registered(_LEGACY_ARCH, registered):
        return legacy
    existing = [
        root / rel
        for rel in sorted(registered)
        if _is_architecture_name(rel)
        and (root / rel).is_file()
        and _within_root(root, root / rel)
    ]
    if len(existing) == 1:
        return existing[0]
    if not existing:
        raise GovernancePathError(
            "no registered architecture authority resolves on disk "
            "(register docs/ARCHITECTURE_PLAN.md or docs/architecture.md)"
        )
    names = ", ".join(p.name for p in existing)
    raise GovernancePathError(f"multiple registered architecture authorities: {names}")


def check_architecture_slot(repo_root: str | Path, tier: str) -> None:
    """Raise ``ValueError`` when the system-tier architecture authority does not
    resolve (thin adapter so ``doc_integrity.check_topology`` stays one line)."""
    try:
        resolve_architecture_authority(repo_root)
    except GovernancePathError as exc:
        raise ValueError(
            f"Tier {tier!r} requires a registered architecture authority; {exc}"
        ) from exc


def resolve_governance_plan_path(raw: str, repo_root: str | Path) -> Path:
    """Resolve ``raw`` to a registered, in-root governance file.

    Rejects (before any read) empty/traversal paths, paths escaping the repo
    root, unsupported extensions, and paths that are neither an always-allowed
    governance family nor registered in the governance index.
    """
    if not raw or ".." in Path(str(raw)).parts:
        raise GovernancePathError(f"traversal or empty governance path rejected: {raw!r}")
    root = Path(repo_root).resolve()
    raw_path = Path(str(raw))
    candidate = raw_path if raw_path.is_absolute() else root / raw_path
    resolved = candidate.resolve()
    if not _within_root(root, resolved):
        raise GovernancePathError(f"governance path escapes repo root: {raw!r}")
    if resolved.suffix.lower() not in _GOVERNANCE_SUFFIXES:
        raise GovernancePathError(
            f"unsupported extension (governance requires .md): {raw!r}"
        )
    rel = resolved.relative_to(root).as_posix()
    if _ALWAYS_ALLOWED_RE.match(rel):
        return resolved
    index_text = _read_index(root)
    if index_text is not None and gi._is_registered(rel, gi._registered_paths(index_text)):
        return resolved
    raise GovernancePathError(f"governance path not registered in index: {rel!r}")
