"""Hermetic, diagnosable git invocation for scratch-repo fixtures (Phase 209).

Two properties, both required by `doctrine-test-discipline.md`:

* **Hermetic.** A scratch repository created by `git init` still reads the
  machine's global and system configuration. On a CI runner `actions/checkout`
  installs `includeIf` entries pointing at credential files it removes during
  job cleanup, so ambient config is mutable underneath a running test.
  `scratch_env()` points `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` at a path
  that does not exist, which git treats as an empty config, and supplies its own
  identity so no ambient `user.name` is borrowed.

* **Diagnosable.** `subprocess.run(..., check=True)` captures git's stderr onto
  the exception, but `CalledProcessError.__str__` never prints it, so a failing
  fixture reports a bare exit code. Phase 194 closed this for the production
  path (`_git_log_merges_in_window`); `run_git` closes it for fixtures.

No retry lives here. A retry would convert a real failure into a slow pass and
destroy the signal these helpers exist to preserve.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

# A path that cannot exist. git reads a missing config file as an empty one.
_NO_CONFIG = str(Path(os.devnull).parent / "qor-nonexistent-gitconfig")

_IDENTITY = {
    "GIT_AUTHOR_NAME": "Qor Fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Qor Fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


def scratch_env(**overrides: str) -> dict[str, str]:
    """Return an environment for git in a scratch repo, free of ambient config.

    The result is a fresh mutable dict, so callers may extend it (for example
    with `GIT_AUTHOR_DATE`) without rebuilding from `os.environ`.
    """
    env = {**os.environ}
    env["GIT_CONFIG_GLOBAL"] = _NO_CONFIG
    env["GIT_CONFIG_SYSTEM"] = _NO_CONFIG
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env.update(_IDENTITY)
    env.update(overrides)
    return env


def run_git(
    argv: list[str], cwd: Path | str, env: dict[str, str] | None = None
) -> str:
    """Run a git command, returning stdout; raise with git's own reason.

    The raised `RuntimeError` names the argv, the cwd, the exit code, and both
    output streams, so a fixture failure is diagnosable from the report alone.
    """
    result = subprocess.run(
        argv, cwd=str(cwd), capture_output=True, text=True,
        env=scratch_env() if env is None else env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git command failed (exit {result.returncode}): {argv!r}\n"
            f"  cwd: {cwd}\n"
            f"  stderr: {result.stderr.strip() or '<empty>'}\n"
            f"  stdout: {result.stdout.strip() or '<empty>'}"
        )
    return result.stdout
