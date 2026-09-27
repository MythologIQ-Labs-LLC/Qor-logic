"""Phase 298 (GH #511): dependency_admission_lint.main routes --lockfile.

The CI admission step runs once per governed root lockfile by passing
`--lockfile <name>`. These tests prove `main` uses that argument for both
the current-file read and the base `git show` read. No network (PyPI lookup
and PR-label query are monkeypatched) and no wall clock (`_now_utc` pinned).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qor.scripts import dependency_admission_lint as lint
from tests.support.git_fixture import run_git, scratch_env


def _lock(*pins: tuple[str, str, str]) -> str:
    """Render pip-compile hash-lockfile text from (name, version, hexchar)."""
    return "".join(
        f"{name}=={version} \\\n    --hash=sha256:{ch * 64}\n"
        for name, version, ch in pins
    )


_RELEASE = _lock(("build", "1.6.0", "a"))
_SBOM_BASE = _lock(("cyclonedx-bom", "7.3.0", "b"), ("sbom-anchor", "1.0.0", "c"))
_SBOM_HEAD = _lock(("cyclonedx-bom", "7.4.0", "d"), ("sbom-anchor", "1.0.0", "c"))


@pytest.fixture
def fixed_now(monkeypatch):
    fixed = datetime(2026, 5, 25, tzinfo=timezone.utc)
    monkeypatch.setattr(lint, "_now_utc", lambda: fixed)
    return fixed


@pytest.fixture
def fake_pypi(monkeypatch, fixed_now):
    calls: list[tuple[str, str]] = []

    def _fetch(name, version, *args, **kwargs):
        calls.append((name, version))
        return fixed_now - timedelta(days=5)

    monkeypatch.setattr(lint, "_fetch_pypi_upload_time", _fetch)
    monkeypatch.setattr(lint, "_query_pr_labels", lambda skip=False: None)
    return calls


@pytest.fixture
def hermetic_git(monkeypatch):
    env = scratch_env()
    for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM"):
        monkeypatch.setenv(key, env[key])


def _fixture_repo(tmp_path: Path) -> str:
    """Base commit holds both lockfiles; head bumps only the sbom lockfile."""
    run_git(["git", "init", "-q", "-b", "main"], tmp_path)
    (tmp_path / "requirements-release.txt").write_text(_RELEASE, encoding="utf-8")
    (tmp_path / "requirements-sbom.txt").write_text(_SBOM_BASE, encoding="utf-8")
    run_git(["git", "add", "-A"], tmp_path)
    run_git(["git", "commit", "-q", "-m", "base"], tmp_path)
    base = run_git(["git", "rev-parse", "HEAD"], tmp_path).strip()
    (tmp_path / "requirements-sbom.txt").write_text(_SBOM_HEAD, encoding="utf-8")
    run_git(["git", "commit", "-q", "-am", "bump cyclonedx-bom"], tmp_path)
    return base


def test_main_lockfile_arg_examines_named_lockfile(
    tmp_path, fake_pypi, hermetic_git, capsys
):
    base = _fixture_repo(tmp_path)
    rc = lint.main([
        "--base", base, "--lockfile", "requirements-sbom.txt",
        "--repo-root", str(tmp_path),
    ])
    out = capsys.readouterr()
    assert rc == 1
    assert fake_pypi == [("cyclonedx-bom", "7.4.0")]
    assert "| cyclonedx-bom | 7.4.0 | 5 | violation |" in out.out
    assert "WARN: cyclonedx-bom@7.4.0" in out.err


def test_main_default_lockfile_does_not_examine_sbom_bump(
    tmp_path, fake_pypi, hermetic_git, capsys
):
    base = _fixture_repo(tmp_path)
    rc = lint.main(["--base", base, "--repo-root", str(tmp_path)])
    out = capsys.readouterr()
    assert rc == 0
    assert fake_pypi == []
    assert "_No lockfile bumps detected._" in out.out
