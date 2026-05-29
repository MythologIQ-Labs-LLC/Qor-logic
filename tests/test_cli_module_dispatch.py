"""Phase 118 (GH #150): `qor-logic reliability/scripts <module>` dispatch.

The dispatch runs the named module via the CLI's own ``sys.executable`` so it
resolves regardless of which ``python`` is active on PATH. These tests invoke
``qor.cli`` (the code under test) in a subprocess, NEVER the PATH ``qor-logic``
console script (which may be a stale global install). Per
``qor/references/doctrine-test-functionality.md`` each test invokes the unit
and asserts on its output / exit code, not on artifact presence.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _venv_inactive_env() -> dict[str, str]:
    """Copy of os.environ simulating a shell where the install venv is NOT
    active: VIRTUAL_ENV unset and the interpreter's own directory stripped
    from PATH. The dispatch must still resolve because it keys off
    sys.executable, not PATH."""
    env = dict(os.environ)
    env.pop("VIRTUAL_ENV", None)
    exe_dir = str(Path(sys.executable).parent)
    parts = [p for p in env.get("PATH", "").split(os.pathsep) if p and p != exe_dir]
    env["PATH"] = os.pathsep.join(parts)
    # Force the child to import the repo's qor.cli, not an installed copy.
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "qor.cli", *args],
        cwd=str(REPO_ROOT),
        env=env if env is not None else dict(os.environ),
        capture_output=True,
        text=True,
    )


def test_reliability_dispatch_resolves_with_venv_inactive():
    """`qor-logic reliability skill_admission qor-plan` resolves the module and
    runs it to completion even with the venv stripped from the env."""
    result = _run("reliability", "skill_admission", "qor-plan", env=_venv_inactive_env())
    assert result.returncode == 0, result.stderr
    assert "ADMITTED: qor-plan" in result.stdout, (result.stdout, result.stderr)


def test_arg_passthrough_forwards_trailing_args_verbatim():
    """The module-specific trailing arg reaches the module: dispatching with
    'qor-audit' yields output keyed to 'qor-audit', proving REMAINDER forwarded
    the arg rather than the dispatch parser swallowing it."""
    result = _run("reliability", "skill_admission", "qor-audit")
    assert result.returncode == 0, result.stderr
    assert "qor-audit" in result.stdout, (result.stdout, result.stderr)


def test_scripts_family_resolves_and_forwards_option_flag():
    """The 'scripts' family dispatches, and a leading-`--` option (--help) is
    forwarded to the module via REMAINDER instead of being parsed by the
    dispatch subparser."""
    result = _run("scripts", "active_phase", "--help")
    assert result.returncode == 0, result.stderr
    assert "active_phase" in result.stdout or "usage" in result.stdout.lower(), (
        result.stdout,
        result.stderr,
    )


def test_dispatch_propagates_nonzero_exit():
    """A module that exits non-zero (skill_admission on an unregistered skill,
    rc=1) propagates that code through the dispatch; the dispatch does not
    swallow it to 0."""
    result = _run("reliability", "skill_admission", "__nope__")
    assert result.returncode == 1, (result.returncode, result.stdout, result.stderr)


def test_unknown_module_returns_nonzero():
    """An unknown module surfaces Python's 'No module named' failure as a
    non-zero exit rather than crashing the CLI process itself."""
    result = _run("reliability", "no_such_module_xyz")
    assert result.returncode != 0
    assert "No module named" in result.stderr


def test_family_prefix_isolation():
    """The family prefix is not bypassable: 'reliability active_phase' targets
    qor.reliability.active_phase (which does not exist) and fails; it cannot
    reach qor.scripts.active_phase."""
    result = _run("reliability", "active_phase")
    assert result.returncode != 0
    assert "qor.reliability.active_phase" in result.stderr
