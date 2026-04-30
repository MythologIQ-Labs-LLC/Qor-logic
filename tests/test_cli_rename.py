"""Phase 48: qor-logic canonical CLI + qorlogic alias.

Functionality tests:
- pyproject declares both entry points pointing to qor.cli:main.
- qor.cli.main(['--version']) emits 'qor-logic <semver>'.
- qor.cli.main(['--help']) renders 'qor-logic' as the program name.
- qor.scripts.install_drift_check.main()'s fix-string output uses qor-logic.
"""
from __future__ import annotations

import io
import re
import sys
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_declares_both_qor_logic_and_qorlogic_entry_points():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    assert "qor-logic" in scripts, "pyproject must declare qor-logic entry point"
    assert "qorlogic" in scripts, "pyproject must retain qorlogic alias"
    assert scripts["qor-logic"] == "qor.cli:main", (
        f"qor-logic must map to qor.cli:main, got {scripts['qor-logic']!r}"
    )
    assert scripts["qorlogic"] == "qor.cli:main", (
        f"qorlogic alias must map to qor.cli:main, got {scripts['qorlogic']!r}"
    )


def test_cli_main_version_string_uses_qor_logic(capsys):
    from qor import cli as cli_mod
    with pytest.raises(SystemExit) as exc:
        cli_mod.main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out + capsys.readouterr().err
    captured = out.strip() or capsys.readouterr().out.strip()
    # argparse may write --version to either stream depending on Python version
    assert re.search(r"qor-logic\s+\d+\.\d+\.\d+", captured), (
        f"--version output must match 'qor-logic <semver>', got: {captured!r}"
    )
    assert not re.search(r"^qorlogic\s", captured), (
        f"--version output must not start with 'qorlogic' (no dash); got: {captured!r}"
    )


def test_cli_help_text_uses_qor_logic_program_name(capsys):
    from qor import cli as cli_mod
    with pytest.raises(SystemExit) as exc:
        cli_mod.main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    # Usage line emitted by argparse uses prog name.
    assert re.search(r"usage:\s+qor-logic\b", out), (
        f"help text usage line must use qor-logic, got: {out[:300]!r}"
    )
    assert not re.search(r"usage:\s+qorlogic\b", out), (
        f"help text usage line must not use bare qorlogic; got: {out[:300]!r}"
    )


# test_install_drift_check_emits_qor_logic_fix_string was REMOVED in Phase 52
# (presence-only test that read source bytes and asserted substring without
# invoking install_drift_check.main()). The replacement
# tests/test_install_drift_check_subprocess.py invokes main() via subprocess
# and asserts on captured output per Phase 46 doctrine.
