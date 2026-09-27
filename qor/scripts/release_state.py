"""Release-state record and tag-coverage rule (Phase 297; GH #520).

sealed/versioned != released/published. ``docs/release-state.json`` records the
versions whose tag or publication history differs from the ordinary release
path; this module is its single owner:

- ``load_release_state`` validates the closed ``qor.release-state/v1`` shape and
  fails closed with ``ReleaseStateError``;
- ``merged_semver_tags`` reads only SemVer tags reachable from ``HEAD`` and
  raises ``ShallowHistoryError`` when truncated history cannot decide
  reachability;
- ``coverage_violations`` is the pure coverage computation.

Coverage rule: every reachable tag and the project version need a dated
CHANGELOG section. The project version is the single implicit untagged
candidate. Every other dated version at or below the ceiling (the greater of
the project version and the highest reachable tag) needs a reachable tag or a
disposition. With no reachable tag at all, nothing is exempt.

The enforcement consumer is the repository test gate
(``tests/test_changelog_tag_coverage.py``) run in CI.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import NamedTuple

SCHEMA_ID = "qor.release-state/v1"
STATES = frozenset({"sealed_unpublished", "legacy_untagged", "unreachable_tag"})
_ROOT_KEYS = frozenset({"schema", "exceptions"})
_ENTRY_KEYS = frozenset({"version", "state", "reason"})
_SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_TAG = re.compile(r"v([0-9]+\.[0-9]+\.[0-9]+)")


class ReleaseStateError(ValueError):
    """The release-state record is unreadable or violates the closed schema."""


class ShallowHistoryError(RuntimeError):
    """The repository is shallow, so tag reachability cannot be decided."""


class CoverageViolations(NamedTuple):
    missing_sections: set[str]
    orphans: set[str]


def load_release_state(path: Path, changelog_versions: set[str]) -> dict[str, str]:
    """Return ``{version: state}`` from the record at ``path``; fail closed."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseStateError(f"{path}: unreadable release-state record: {exc}") from exc
    if not isinstance(data, dict) or set(data) != _ROOT_KEYS:
        raise ReleaseStateError(f"{path}: root must be an object with exactly {sorted(_ROOT_KEYS)}")
    if data["schema"] != SCHEMA_ID:
        raise ReleaseStateError(f"{path}: unsupported schema {data['schema']!r}")
    if not isinstance(data["exceptions"], list):
        raise ReleaseStateError(f"{path}: 'exceptions' must be a list")
    result: dict[str, str] = {}
    for entry in data["exceptions"]:
        version, state = _validate_entry(path, entry, changelog_versions)
        if version in result:
            raise ReleaseStateError(f"{path}: duplicate version {version}")
        result[version] = state
    return result


def _validate_entry(path: Path, entry: object, changelog_versions: set[str]) -> tuple[str, str]:
    if not isinstance(entry, dict) or set(entry) != _ENTRY_KEYS:
        raise ReleaseStateError(f"{path}: entry must be an object with exactly {sorted(_ENTRY_KEYS)}")
    version, state, reason = entry["version"], entry["state"], entry["reason"]
    if not isinstance(version, str) or not _SEMVER.fullmatch(version):
        raise ReleaseStateError(f"{path}: version {version!r} is not MAJOR.MINOR.PATCH")
    if not isinstance(state, str) or state not in STATES:
        raise ReleaseStateError(f"{path}: unsupported state {state!r} for {version}")
    if not isinstance(reason, str) or not reason.strip():
        raise ReleaseStateError(f"{path}: empty reason for {version}")
    if version not in changelog_versions:
        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")
    return version, state


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo_root, check=True, capture_output=True, text=True,
    ).stdout


def merged_semver_tags(repo_root: Path) -> set[str]:
    """Return versions (no ``v``) of strict SemVer tags reachable from ``HEAD``.

    Raises ``ShallowHistoryError`` on a shallow repository; git failures
    (``FileNotFoundError``, ``subprocess.CalledProcessError``) propagate.
    """
    if _git(repo_root, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise ShallowHistoryError(f"{repo_root}: shallow repository")
    out = _git(repo_root, "tag", "--merged", "HEAD", "--list", "v*")
    matches = (_TAG.fullmatch(line.strip()) for line in out.splitlines())
    return {m.group(1) for m in matches if m}


def _semver(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def coverage_violations(versions: set[str], tags: set[str], project_version: str,
                        exceptions: dict[str, str]) -> CoverageViolations:
    """Missing dated sections and orphaned versions under the coverage rule."""
    missing = {v for v in tags | {project_version} if v not in versions}
    ceiling = max(_semver(v) for v in tags | {project_version})
    orphans = {
        v for v in versions - tags - set(exceptions) - {project_version}
        if _semver(v) <= ceiling
    }
    return CoverageViolations(missing, orphans)
