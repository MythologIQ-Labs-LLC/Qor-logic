"""Release-tag coverage for CHANGELOG versions.

The current project version is the one implicit untagged release candidate.
Older untagged versions require an explicit disposition in
``docs/release-state.json``.
"""
from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from qor.scripts.release_state import load_exceptions


REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"
PYPROJECT = REPO / "pyproject.toml"
RELEASE_STATE = REPO / "docs" / "release-state.json"
_VERSION_HEADER = re.compile(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\] -", re.MULTILINE)
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _git_tags() -> list[str]:
    """Return sorted SemVer-prefixed tags visible in this checkout."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "v*"],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("git not available; tag-coverage test skipped")
    tags = [tag.strip() for tag in result.stdout.splitlines() if tag.strip()]
    return sorted(tag for tag in tags if re.match(r"^v[0-9]+\.[0-9]+\.[0-9]+$", tag))


def _changelog_versions() -> set[str]:
    return set(_VERSION_HEADER.findall(CHANGELOG.read_text(encoding="utf-8")))


def _project_version() -> str:
    payload = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = payload.get("project", {}).get("version")
    assert isinstance(version, str) and _SEMVER.fullmatch(version), (
        "pyproject project.version must be strict MAJOR.MINOR.PATCH"
    )
    return version


def _parse_semver(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".", 2)
    return int(major), int(minor), int(patch)


def _coverage_ceiling(tags: set[str], candidate_version: str) -> tuple[int, int, int]:
    ceiling = _parse_semver(candidate_version)
    if tags:
        ceiling = max(ceiling, max(_parse_semver(tag) for tag in tags))
    return ceiling


def _released_orphans(
    versions: set[str],
    tags: set[str],
    explicit_exceptions: set[str] | frozenset[str] = frozenset(),
    *,
    candidate_version: str,
) -> set[str]:
    """Return versions lacking an ordinary or explicit release disposition."""
    ceiling = _coverage_ceiling(tags, candidate_version)
    candidates = versions - tags - explicit_exceptions - {candidate_version}
    return {version for version in candidates if _parse_semver(version) <= ceiling}


def test_every_tag_has_changelog_section():
    tags = _git_tags()
    versions = _changelog_versions()
    missing = [tag for tag in tags if tag.lstrip("v") not in versions]
    assert not missing, "Git tags without CHANGELOG entries:\n  " + "\n  ".join(missing)


def test_project_version_has_changelog_section():
    candidate = _project_version()
    assert candidate in _changelog_versions(), (
        f"project version {candidate} has no dated CHANGELOG section"
    )


def test_release_state_record_is_valid():
    load_exceptions(RELEASE_STATE, _changelog_versions())


def test_every_changelog_section_has_release_disposition():
    tags = {tag.lstrip("v") for tag in _git_tags()}
    versions = _changelog_versions()
    candidate = _project_version()
    exceptions = load_exceptions(RELEASE_STATE, versions)
    orphans = _released_orphans(
        versions,
        tags,
        exceptions,
        candidate_version=candidate,
    )
    assert not orphans, (
        "CHANGELOG sections at or below the current release-candidate ceiling "
        "must have a matching git tag or an explicit release-state entry:\n  "
        + "\n  ".join(sorted(orphans))
    )


def test_current_candidate_is_the_only_implicit_untagged_exemption():
    tags = {"0.28.1"}
    versions = {"0.28.0", "0.28.1", "0.29.0"}
    assert _released_orphans(
        versions, tags, candidate_version="0.29.0"
    ) == {"0.28.0"}


def test_older_unpublished_version_needs_explicit_disposition():
    tags = {"0.172.2"}
    versions = {"0.172.2", "0.173.0", "0.174.0", "0.175.0"}
    assert _released_orphans(
        versions,
        tags,
        {"0.173.0", "0.174.0"},
        candidate_version="0.175.0",
    ) == set()
    assert _released_orphans(
        versions,
        tags,
        {"0.173.0"},
        candidate_version="0.175.0",
    ) == {"0.174.0"}


def test_observed_tag_above_candidate_extends_coverage_ceiling():
    tags = {"0.28.0", "0.30.0"}
    versions = {"0.28.0", "0.29.0", "0.30.0"}
    assert _released_orphans(
        versions, tags, candidate_version="0.28.0"
    ) == {"0.29.0"}


def test_explicit_exception_is_exempt_but_unrecorded_peer_is_not():
    tags = {"0.175.2"}
    versions = {"0.175.0", "0.175.1", "0.175.2"}
    assert _released_orphans(
        versions,
        tags,
        {"0.175.0"},
        candidate_version="0.175.2",
    ) == {"0.175.1"}


def test_coverage_ceiling_uses_candidate_without_tags():
    assert _released_orphans(
        {"0.1.0", "0.2.0"},
        set(),
        candidate_version="0.2.0",
    ) == {"0.1.0"}
