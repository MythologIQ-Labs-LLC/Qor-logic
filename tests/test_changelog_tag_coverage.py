"""Phase 27 Phase 1: every git tag has a CHANGELOG section and vice versa.

Phase 297 (GH #520): sealed/versioned != released/published. Only the
``[project].version`` is an implicit untagged release candidate; every other
dated version at or below the ceiling (the greater of the project version and
the highest tag reachable from ``HEAD``) needs a reachable tag or an explicit
disposition in ``docs/release-state.json``. Tags not reachable from ``HEAD``
belong to another line of history and take no part in coverage. The rule lives
in ``qor.scripts.release_state``; CI (full history, tags fetched) is the
authoritative enforcement point.
"""
from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from qor.scripts import release_state


REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"
PYPROJECT = REPO / "pyproject.toml"
RELEASE_STATE = REPO / "docs" / "release-state.json"
_VERSION_HEADER = re.compile(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\] -", re.MULTILINE)
_GIT_UNAVAILABLE = "git not available; tag-coverage test skipped"
_SHALLOW = "shallow history cannot decide tag reachability; tag-coverage test skipped"


def _reachable_tags() -> set[str]:
    try:
        return release_state.merged_semver_tags(REPO)
    except release_state.ShallowHistoryError:
        pytest.skip(_SHALLOW)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip(_GIT_UNAVAILABLE)


def _changelog_versions() -> set[str]:
    text = CHANGELOG.read_text(encoding="utf-8")
    return set(_VERSION_HEADER.findall(text))


def _project_version() -> str:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]


def _live_violations() -> release_state.CoverageViolations:
    tags = _reachable_tags()
    versions = _changelog_versions()
    exceptions = release_state.load_release_state(RELEASE_STATE, versions)
    return release_state.coverage_violations(
        versions, tags, _project_version(), exceptions,
    )


def test_every_tag_has_changelog_section():
    missing = _live_violations().missing_sections
    assert not missing, (
        "Reachable git tags (or the project version) without dated CHANGELOG "
        "sections:\n  " + "\n  ".join(sorted(missing))
    )


def test_every_changelog_section_has_tag():
    orphans = _live_violations().orphans
    assert not orphans, (
        "CHANGELOG sections at or below the ceiling need a reachable tag or a "
        "docs/release-state.json disposition:\n  " + "\n  ".join(sorted(orphans))
    )


# ----- skip mechanism (runs on every checkout, shallow or not) -----

def _raiser(exc: BaseException):
    def reader(_repo_root):
        raise exc
    return reader


def test_shallow_history_skips_with_named_reason(monkeypatch):
    monkeypatch.setattr(
        release_state, "merged_semver_tags",
        _raiser(release_state.ShallowHistoryError("shallow")),
    )
    with pytest.raises(pytest.skip.Exception) as info:
        _reachable_tags()
    assert "shallow history" in str(info.value)


def test_git_unavailable_skips_with_existing_reason(monkeypatch):
    monkeypatch.setattr(
        release_state, "merged_semver_tags", _raiser(FileNotFoundError("git")),
    )
    with pytest.raises(pytest.skip.Exception) as info:
        _reachable_tags()
    assert str(info.value) == _GIT_UNAVAILABLE
