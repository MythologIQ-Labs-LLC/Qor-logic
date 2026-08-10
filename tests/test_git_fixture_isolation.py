"""Phase 209: scratch-repo git fixtures are hermetic and diagnosable.

A fixture that inherits the machine's git configuration is environment coupling,
which `doctrine-test-discipline.md` forbids. On a CI runner `actions/checkout`
installs `includeIf` entries pointing at credential files it later tears down,
so ambient config is not merely untidy -- it is mutable underneath a running
test. These tests pin both properties of the shared helper: ambient config is
excluded, and a failing git command reports git's own reason.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.support.git_fixture import run_git, scratch_env


def _init_repo(path: Path, env: dict) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    run_git(["git", "init", "-b", "main"], cwd=path, env=env)
    return path


def test_scratch_repo_env_disables_ambient_config(tmp_path: Path):
    """A key defined in an ambient global config is invisible to the fixture."""
    ambient = tmp_path / "ambient.gitconfig"
    ambient.write_text("[qorfixture]\n\tprobe = ambient-value\n", encoding="utf-8")

    repo = _init_repo(tmp_path / "repo", scratch_env())

    # With the ambient config deliberately in scope, git finds the key...
    leaky = {**scratch_env(), "GIT_CONFIG_GLOBAL": str(ambient)}
    visible = subprocess.run(
        ["git", "config", "--get", "qorfixture.probe"],
        cwd=str(repo), env=leaky, capture_output=True, text=True,
    )
    assert visible.stdout.strip() == "ambient-value", (
        "control arm failed: the probe key must be readable when the ambient "
        f"config IS in scope; got {visible.stdout!r} / {visible.stderr!r}"
    )

    # ...and under the fixture environment it is not.
    isolated = subprocess.run(
        ["git", "config", "--get", "qorfixture.probe"],
        cwd=str(repo), env=scratch_env(), capture_output=True, text=True,
    )
    assert isolated.returncode != 0, "ambient config leaked into the fixture"
    assert isolated.stdout.strip() == ""


def test_scratch_repo_env_preserves_path_and_identity(tmp_path: Path):
    """git still resolves, and a commit succeeds with no ambient identity."""
    env = scratch_env()
    assert env.get("PATH"), "PATH must survive so `git` resolves"

    repo = _init_repo(tmp_path / "repo", env)
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    run_git(["git", "add", "f.txt"], cwd=repo, env=env)
    run_git(["git", "commit", "-m", "initial"], cwd=repo, env=env)

    subject = run_git(["git", "log", "-1", "--format=%s"], cwd=repo, env=env)
    assert subject.strip() == "initial"
    author = run_git(["git", "log", "-1", "--format=%an <%ae>"], cwd=repo, env=env)
    assert author.strip(), "fixture must supply an identity, not borrow one"


def test_run_git_raises_with_stderr_and_context(tmp_path: Path):
    """A failing git command reports git's reason, the argv, and the cwd."""
    env = scratch_env()
    repo = _init_repo(tmp_path / "repo", env)
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    run_git(["git", "add", "f.txt"], cwd=repo, env=env)
    run_git(["git", "commit", "-m", "initial"], cwd=repo, env=env)

    with pytest.raises(RuntimeError) as exc:
        run_git(["git", "merge", "--no-ff", "no-such-branch"], cwd=repo, env=env)

    message = str(exc.value)
    assert "no-such-branch" in message, "must quote the failing argv"
    assert str(repo) in message, "must name the cwd for diagnosis"
    lowered = message.lower()
    assert "not something we can merge" in lowered or "merge" in lowered, (
        f"must surface git's own stderr; got: {message!r}"
    )
