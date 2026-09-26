"""Phase 298 (GH #511): `dependency_admission_lint.main` honours `--lockfile`.

Regression coverage backfill: `main` already routes `--lockfile` to both the
current read and the base `git show` read. These tests pin that routing so a
regression in either read, or a dropped argument, fails a declared test.
No network, no wall clock, no ambient git config.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qor.scripts import dependency_admission_lint as lint
from tests.support.git_fixture import run_git, scratch_env


def _entry(name: str, version: str, hex_char: str) -> str:
    return f"{name}=={version} \\\n    --hash=sha256:{hex_char * 64}\n"


@pytest.fixture
def fixed_now(monkeypatch):
    fixed = datetime(2026, 5, 25, tzinfo=timezone.utc)
    monkeypatch.setattr(lint, "_now_utc", lambda: fixed)
    return fixed


@pytest.fixture
def fake_pypi(monkeypatch, fixed_now):
    calls: list[tuple[str, str]] = []

    def fetch(name, version, *args, **kwargs):
        calls.append((name, version))
        return fixed_now - timedelta(days=5)

    monkeypatch.setattr(lint, "_fetch_pypi_upload_time", fetch)
    monkeypatch.setattr(lint, "_query_pr_labels", lambda skip=False: None)
    return calls


@pytest.fixture
def hermetic_git(monkeypatch):
    env = scratch_env()
    for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM"):
        monkeypatch.setenv(key, env[key])


def _fixture_repo(tmp_path) -> str:
    run_git(["git", "init", "-b", "main"], cwd=tmp_path)
    (tmp_path / "requirements-release.txt").write_text(
        _entry("build", "1.6.0", "a"), encoding="utf-8"
    )
    sbom = tmp_path / "requirements-sbom.txt"
    sbom.write_text(
        _entry("cyclonedx-bom", "7.3.0", "b") + _entry("sbom-anchor", "1.0.0", "c"),
        encoding="utf-8",
    )
    run_git(["git", "add", "-A"], cwd=tmp_path)
    run_git(["git", "commit", "-q", "-m", "base"], cwd=tmp_path)
    base = run_git(["git", "rev-parse", "HEAD"], cwd=tmp_path).strip()
    sbom.write_text(
        _entry("cyclonedx-bom", "7.4.0", "d") + _entry("sbom-anchor", "1.0.0", "c"),
        encoding="utf-8",
    )
    run_git(["git", "commit", "-q", "-am", "head"], cwd=tmp_path)
    return base


def test_main_lockfile_arg_examines_named_lockfile(
    tmp_path, fake_pypi, hermetic_git, capsys
):
    base = _fixture_repo(tmp_path)
    rc = lint.main([
        "--base", base, "--lockfile", "requirements-sbom.txt",
        "--repo-root", str(tmp_path),
    ])
    out, err = capsys.readouterr()
    assert rc == 1
    assert fake_pypi == [("cyclonedx-bom", "7.4.0")]
    assert "| cyclonedx-bom | 7.4.0 | 5 | violation |" in out
    assert "WARN: cyclonedx-bom@7.4.0" in err


def test_main_default_lockfile_does_not_examine_sbom_bump(
    tmp_path, fake_pypi, hermetic_git, capsys
):
    base = _fixture_repo(tmp_path)
    rc = lint.main(["--base", base, "--repo-root", str(tmp_path)])
    out, _ = capsys.readouterr()
    assert rc == 0
    assert fake_pypi == []
    assert "_No lockfile bumps detected._" in out
