"""Phase 214 (GH #308): git auto-maintenance cannot race the test fixtures.

git >= 2.5x runs `git maintenance run --auto --detach` after commit/merge.
Because it daemonizes, `git repack -d` keeps rewriting a scratch repository's
object store after the foreground call has returned, deleting loose objects and
their shard directories while the next call is using them. Upstream saw eight
occurrences and established the mechanism with an A/B counterfactual.

These tests assert the guard is IN EFFECT rather than asserting an outcome.
The obvious test -- "zero pack files after N merges" -- passes vacuously on any
host whose git predates the behavior, including this project's Windows dev host
at git 2.52 versus CI's 2.54. A test that passes for the wrong reason at the
place it is most often run is worse than no test.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.support.git_fixture import run_git, scratch_env


def _scratch_repo(tmp_path: Path, env: dict) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    run_git(["git", "init", "-q", "-b", "main"], cwd=repo, env=env)
    return repo


def _resolved(repo: Path, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "config", "--get", "maintenance.auto"],
        cwd=str(repo), env=env, capture_output=True, text=True,
    )


def test_maintenance_auto_is_disabled_for_test_git_calls(tmp_path: Path):
    """The autouse fixture puts the guard in the ambient test environment."""
    env = dict(os.environ)
    repo = _scratch_repo(tmp_path, env)

    result = _resolved(repo, env)
    assert result.returncode == 0, (
        "maintenance.auto must resolve for git calls made by tests; the autouse "
        f"guard in conftest.py is missing. stderr: {result.stderr!r}"
    )
    assert result.stdout.strip() == "false", result.stdout


def test_guard_survives_the_hermetic_scratch_environment(tmp_path: Path):
    """The Phase 209 pinning must not shadow the Phase 214 guard.

    `scratch_env()` pins GIT_CONFIG_GLOBAL / GIT_CONFIG_SYSTEM /
    GIT_CONFIG_NOSYSTEM. A guard written as a global or system config file
    would be read out of scope by that pinning -- the earlier fix would have
    silently defeated this one. The env-config layer is read independently.
    """
    env = scratch_env()
    repo = _scratch_repo(tmp_path, env)

    result = _resolved(repo, env)
    assert result.returncode == 0, (
        "the guard must survive GIT_CONFIG_GLOBAL/SYSTEM pinning; it is being "
        f"shadowed. stderr: {result.stderr!r}"
    )
    assert result.stdout.strip() == "false"


def test_guard_does_not_clobber_an_existing_env_config_layer(tmp_path: Path):
    """The fixture appends; it does not assume index 0 is free."""
    env = scratch_env()
    repo = _scratch_repo(tmp_path, env)

    count = int(env.get("GIT_CONFIG_COUNT", "0"))
    assert count >= 1, "the guard should have contributed an env-config entry"

    keys = {env[f"GIT_CONFIG_KEY_{i}"] for i in range(count)}
    assert "maintenance.auto" in keys, keys

    # A pre-existing entry supplied by a caller must still resolve alongside it.
    extended = {
        **env,
        "GIT_CONFIG_COUNT": str(count + 1),
        f"GIT_CONFIG_KEY_{count}": "qorfixture.probe",
        f"GIT_CONFIG_VALUE_{count}": "kept",
    }
    probe = subprocess.run(
        ["git", "config", "--get", "qorfixture.probe"],
        cwd=str(repo), env=extended, capture_output=True, text=True,
    )
    assert probe.stdout.strip() == "kept", probe.stderr
    assert _resolved(repo, extended).stdout.strip() == "false"
