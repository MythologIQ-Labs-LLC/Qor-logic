"""Phase 297: release-state record, reachable-tag reader, and coverage rule.

Exercises ``qor.scripts.release_state``: the closed-schema validator for
``docs/release-state.json``, the reachable-tag reader, and the pure coverage
computation (sealed/versioned != released/published; GH #520).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from qor.scripts import release_state
from qor.scripts.release_state import (
    ReleaseStateError,
    ShallowHistoryError,
    coverage_violations,
    load_release_state,
    merged_semver_tags,
)

_CHANGELOG_VERSIONS = {"0.1.0", "0.2.0", "0.3.0"}


def _entry(version: str = "0.1.0", state: str = "sealed_unpublished",
           reason: str = "sealed locally, never pushed") -> dict:
    return {"version": version, "state": state, "reason": reason}


def _record(*entries: dict) -> dict:
    return {"schema": release_state.SCHEMA_ID, "exceptions": list(entries)}


def _write(tmp_path: Path, payload) -> Path:
    path = tmp_path / "release-state.json"
    text = payload if isinstance(payload, str) else json.dumps(payload)
    path.write_text(text, encoding="utf-8")
    return path


# ----- validator -----

def test_accepted_states_load_with_their_state(tmp_path):
    path = _write(tmp_path, _record(
        _entry("0.1.0", "legacy_untagged"),
        _entry("0.2.0", "sealed_unpublished"),
        _entry("0.3.0", "unreachable_tag"),
    ))
    assert load_release_state(path, _CHANGELOG_VERSIONS) == {
        "0.1.0": "legacy_untagged",
        "0.2.0": "sealed_unpublished",
        "0.3.0": "unreachable_tag",
    }


_MALFORMED = {
    "wrong-root-shape": [],
    "extra-root-field": {**_record(), "extra": 1},
    "unsupported-schema": {"schema": "qor.release-state/v2", "exceptions": []},
    "non-list-exceptions": {"schema": "qor.release-state/v1", "exceptions": {}},
    "non-object-entry": _record("0.1.0"),
    "duplicate-version": _record(_entry("0.1.0"), _entry("0.1.0", "legacy_untagged")),
    "malformed-version": _record(_entry("0.1")),
    "unsupported-state": _record(_entry(state="published")),
    "orphaned-version": _record(_entry("9.9.9")),
    "empty-reason": _record(_entry(reason="  ")),
    "extra-entry-field": _record({**_entry(), "tag": "v0.1.0"}),
    "invalid-json": "{not json",
}


@pytest.mark.parametrize("payload", list(_MALFORMED.values()), ids=list(_MALFORMED))
def test_malformed_records_raise(tmp_path, payload):
    path = _write(tmp_path, payload)
    with pytest.raises(ReleaseStateError):
        load_release_state(path, _CHANGELOG_VERSIONS)


def test_unreadable_path_raises(tmp_path):
    with pytest.raises(ReleaseStateError):
        load_release_state(tmp_path / "absent.json", _CHANGELOG_VERSIONS)


# ----- pure coverage computation -----

def test_older_untagged_version_under_ceiling_is_orphan():
    result = coverage_violations({"0.1.0", "0.2.0", "0.3.0"}, {"0.2.0"}, "0.3.0", {})
    assert result.orphans == {"0.1.0"}
    assert result.missing_sections == set()


def test_project_version_is_not_an_orphan():
    result = coverage_violations({"0.1.0", "0.2.0"}, {"0.1.0"}, "0.2.0", {})
    assert result.orphans == set()


def test_project_version_without_dated_section_is_missing():
    result = coverage_violations({"0.1.0"}, {"0.1.0"}, "0.2.0", {})
    assert result.missing_sections == {"0.2.0"}


def test_reachable_tag_above_project_version_raises_ceiling():
    result = coverage_violations({"0.1.0", "0.2.0", "0.3.0"}, {"0.3.0"}, "0.1.0", {})
    assert result.orphans == {"0.2.0"}


def test_disposition_exempts_only_the_named_version():
    versions = {"0.1.0", "0.2.0", "0.3.0", "0.4.0"}
    result = coverage_violations(versions, {"0.1.0"}, "0.4.0", {"0.2.0": "legacy_untagged"})
    assert result.orphans == {"0.3.0"}


def test_sealed_unpublished_version_with_local_tag_is_clean():
    result = coverage_violations(
        {"0.1.0", "0.2.0"}, {"0.1.0", "0.2.0"}, "0.2.0", {"0.1.0": "sealed_unpublished"},
    )
    assert result.orphans == set()
    assert result.missing_sections == set()


def test_no_tags_reports_every_older_version():
    """No tag set means no exemption: every older untagged version is an orphan."""
    result = coverage_violations({"0.1.0", "0.2.0", "0.3.0"}, set(), "0.3.0", {})
    assert result.orphans == {"0.1.0", "0.2.0"}


# ----- reachable-tag reader against fixture repositories -----

@pytest.fixture
def git_env(tmp_path, monkeypatch):
    empty = tmp_path / "empty-gitconfig"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "Fixture")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "fixture@example.invalid")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _commit(repo: Path, name: str) -> None:
    (repo / name).write_text(name, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", name)


@pytest.fixture
def side_tag_repo(tmp_path, git_env) -> Path:
    """main: c1 (v0.1.0) -> c2 (v0.2.0); side branch off c1 tagged v0.3.0."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _commit(repo, "c1")
    _git(repo, "tag", "v0.1.0")
    _git(repo, "checkout", "-q", "-b", "side")
    _commit(repo, "side")
    _git(repo, "tag", "v0.3.0")
    _git(repo, "checkout", "-q", "main")
    _commit(repo, "c2")
    _git(repo, "tag", "v0.2.0")
    _git(repo, "tag", "v-migration")
    return repo


def test_side_branch_tag_is_not_reachable(side_tag_repo):
    tags = merged_semver_tags(side_tag_repo)
    assert tags == {"0.1.0", "0.2.0"}
    # 0.2.5 sits above the reachable ceiling (0.2.0); the side tag v0.3.0
    # would raise the ceiling over it if it were counted.
    result = coverage_violations({"0.1.0", "0.2.0", "0.2.5"}, tags, "0.2.0", {})
    assert result.missing_sections == set()
    assert result.orphans == set()


def test_reachable_tag_without_section_is_missing(side_tag_repo):
    tags = merged_semver_tags(side_tag_repo)
    result = coverage_violations({"0.1.0"}, tags, "0.1.0", {})
    assert result.missing_sections == {"0.2.0"}


def test_unreachable_tag_version_is_orphan_until_disposed(side_tag_repo):
    tags = merged_semver_tags(side_tag_repo)
    versions = {"0.1.0", "0.2.0", "0.3.0", "0.4.0"}
    assert coverage_violations(versions, tags, "0.4.0", {}).orphans == {"0.3.0"}
    disposed = coverage_violations(versions, tags, "0.4.0", {"0.3.0": "unreachable_tag"})
    assert disposed.orphans == set()


def test_shallow_clone_raises_shallow_history_error(tmp_path, git_env):
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init", "-q", "-b", "main")
    _commit(source, "c1")
    _git(source, "tag", "v0.1.0")
    _commit(source, "c2")
    _git(source, "tag", "v0.2.0")
    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", source.as_uri(), str(clone)],
        check=True, capture_output=True,
    )
    with pytest.raises(ShallowHistoryError):
        merged_semver_tags(clone)
