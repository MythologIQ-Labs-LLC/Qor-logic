"""Canonical governance artifact path discovery.

This module centralizes path resolution for governance gates. Callers must not
reintroduce filename-family allowlists or literal architecture paths after a
repository has registered a different canonical authority.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

_INDEX_PATH = Path("docs/GOVERNANCE_INDEX.md")
_MARKDOWN_PATH_RE = re.compile(r"`([^`]+\.md)`")
_TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|", re.MULTILINE)
_ALLOWED_GOVERNANCE_PREFIXES = ("docs/", "qor/references/")


@dataclass(frozen=True)
class GovernanceRegistration:
    artifact: str
    path_pattern: str


def _repo_root(root: str | Path) -> Path:
    return Path(root).resolve()


def _confined_relative_path(raw: str | Path, root: str | Path) -> tuple[Path, str]:
    repo_root = _repo_root(root)
    candidate = Path(raw)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (repo_root / candidate).resolve()
    try:
        relative = resolved.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise ValueError(f"governance path escapes repository root: {raw!r}") from exc
    if relative == "." or not relative.endswith(".md"):
        raise ValueError(f"unsupported governance path: {raw!r}")
    if not relative.startswith(_ALLOWED_GOVERNANCE_PREFIXES):
        raise ValueError(f"path is outside governance document roots: {raw!r}")
    return resolved, relative


def load_governance_registrations(root: str | Path) -> tuple[GovernanceRegistration, ...]:
    repo_root = _repo_root(root)
    index_path = repo_root / _INDEX_PATH
    if not index_path.is_file():
        raise ValueError(f"governance index not found at {_INDEX_PATH.as_posix()!r}")

    text = index_path.read_text(encoding="utf-8")
    registrations = tuple(
        GovernanceRegistration(artifact=artifact.strip(), path_pattern=path.strip())
        for artifact, path in _TABLE_ROW_RE.findall(text)
    )
    if not registrations:
        raise ValueError("governance index contains no registered artifact rows")
    return registrations


def is_registered_governance_path(raw: str | Path, root: str | Path) -> bool:
    _, relative = _confined_relative_path(raw, root)
    for registration in load_governance_registrations(root):
        patterns = [part.strip() for part in registration.path_pattern.split(",")]
        if any(fnmatch.fnmatchcase(relative, pattern) for pattern in patterns):
            return True
    return False


def resolve_registered_governance_path(
    raw: str | Path,
    root: str | Path,
    *,
    require_exists: bool = True,
) -> Path:
    resolved, relative = _confined_relative_path(raw, root)
    if not is_registered_governance_path(relative, root):
        raise ValueError(f"unregistered governance path: {relative!r}")
    if require_exists and not resolved.is_file():
        raise ValueError(f"registered governance path does not exist: {relative!r}")
    return resolved


def resolve_architecture_authority(root: str | Path) -> Path:
    repo_root = _repo_root(root)
    matches: list[Path] = []
    for registration in load_governance_registrations(repo_root):
        artifact = registration.artifact.casefold()
        if "architecture" not in artifact:
            continue
        for pattern in [part.strip() for part in registration.path_pattern.split(",")]:
            if any(token in pattern for token in "*?["):
                for candidate in repo_root.glob(pattern):
                    if candidate.is_file():
                        matches.append(candidate.resolve())
            else:
                candidate = (repo_root / pattern).resolve()
                try:
                    candidate.relative_to(repo_root)
                except ValueError as exc:
                    raise ValueError(
                        f"registered architecture authority escapes repository root: {pattern!r}"
                    ) from exc
                if candidate.is_file():
                    matches.append(candidate)

    unique = sorted(set(matches))
    if not unique:
        legacy = repo_root / "docs" / "architecture.md"
        if legacy.is_file():
            return legacy.resolve()
        raise ValueError("no existing registered architecture authority found")
    if len(unique) != 1:
        rendered = ", ".join(path.relative_to(repo_root).as_posix() for path in unique)
        raise ValueError(f"multiple architecture authorities found: {rendered}")
    return unique[0]
