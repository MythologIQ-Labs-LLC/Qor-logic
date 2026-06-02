"""Pluggable version-bump backends (Phase 133; GH #163).

Detects the repo archetype (pyproject.toml / package.json / Cargo.toml) and bumps
the version in the detected manifest. The python path delegates to the unchanged
`governance_helpers.bump_version`; node/rust reuse the same semver compute + tag
guards with a format-specific read/write. Closes #38's deferred Option 2.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import governance_helpers as gh

_TOML_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', re.MULTILINE)
_JSON_RE = re.compile(r'"version"\s*:\s*"(\d+)\.(\d+)\.(\d+)"')


class NoBackendError(RuntimeError):
    """Raised when no supported version manifest is found under the repo root."""


@dataclass(frozen=True)
class VersionBackend:
    name: str
    filename: str
    pattern: re.Pattern
    template: str  # format string with {v}


BACKENDS: tuple[VersionBackend, ...] = (
    VersionBackend("python", "pyproject.toml", _TOML_RE, 'version = "{v}"'),
    VersionBackend("node", "package.json", _JSON_RE, '"version": "{v}"'),
    VersionBackend("rust", "Cargo.toml", _TOML_RE, 'version = "{v}"'),
)


def detect_backend(repo_root: Path) -> VersionBackend | None:
    for backend in BACKENDS:
        if (repo_root / backend.filename).is_file():
            return backend
    return None


def read_version(backend: VersionBackend, repo_root: Path) -> tuple[int, int, int]:
    text = (repo_root / backend.filename).read_text(encoding="utf-8")
    m = backend.pattern.search(text)
    if not m:
        raise ValueError(f"{backend.filename} has no parseable version")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _bump_generic(backend: VersionBackend, repo_root: Path, change_class: str) -> str:
    path = repo_root / backend.filename
    text = path.read_text(encoding="utf-8")
    cur = read_version(backend, repo_root)
    new = gh._compute_new(*cur, change_class)
    new_str = f"{new[0]}.{new[1]}.{new[2]}"
    tags = gh._list_tags()
    if f"v{new_str}" in tags:
        raise gh.InterdictionError(f"tag v{new_str} already exists")
    highest = gh._highest_tag(tags)
    if highest is not None and new <= highest:
        raise gh.InterdictionError(
            f"target v{new_str} <= current highest tag "
            f"v{highest[0]}.{highest[1]}.{highest[2]} (downgrade guard)"
        )
    new_text = backend.pattern.sub(backend.template.format(v=new_str), text, count=1)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    os.replace(tmp, path)
    return new_str


def bump(repo_root: Path, change_class: str) -> tuple[str, str]:
    """Bump the detected manifest's version. Returns (new_version, backend_name).
    Python delegates to governance_helpers.bump_version (unchanged behavior)."""
    backend = detect_backend(repo_root)
    if backend is None:
        raise NoBackendError(
            "no supported version manifest (pyproject.toml / package.json / Cargo.toml)"
        )
    if backend.name == "python":
        new = gh.bump_version(change_class, pyproject_path=repo_root / backend.filename)
        return new, "python"
    return _bump_generic(backend, repo_root, change_class), backend.name
