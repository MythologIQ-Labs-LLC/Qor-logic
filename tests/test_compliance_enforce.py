"""Behavioral tests for the downstream enforcement SDK (Phase 142).

Each test invokes run_control/enforce (or the CLI dispatch) and asserts on the
returned Verdict/ControlResult / exit code -- not on artifacts.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

from qor.compliance import enforce as en
from qor.scripts.compliance_matrix import Control

REPO = Path(__file__).resolve().parents[1]


def _ctl(cid, *, posture="ABORT", engagement=("pre-commit",), module=None):
    return Control(
        id=cid, framework="F", control="c", enforcing_module=module or "m",
        posture=posture, detection="test", wired_into={}, variants=(),
        engagement=engagement,
        runner={"module": module, "entry": "main", "args": []} if module else None,
    )


def _install_module(name, exit_code):
    mod = types.ModuleType(name)
    mod.main = lambda argv=None: exit_code
    sys.modules[name] = mod
    return name


def test_run_control_reports_exit_code(tmp_path):
    name = _install_module("qor_test_runner_ok", 0)
    res = en.run_control(_ctl("a", module=name), tmp_path)
    assert res.passed is True and res.exit_code == 0
    name2 = _install_module("qor_test_runner_fail", 1)
    res2 = en.run_control(_ctl("b", module=name2), tmp_path)
    assert res2.passed is False and res2.exit_code == 1


def test_enforce_selects_by_engagement_and_runner(tmp_path):
    name = _install_module("qor_test_runner_sel", 0)
    controls = (
        _ctl("runs", engagement=("pre-commit",), module=name),
        _ctl("skipped-noeng", engagement=("seal",), module=name),
        _ctl("skipped-norunner", engagement=("pre-commit",), module=None),
    )
    verdict = en.enforce("pre-commit", tmp_path, controls=controls)
    assert {r.id for r in verdict.results} == {"runs"}
    assert verdict.passed is True


def test_enforce_verdict_fails_when_abort_runner_fails(tmp_path):
    bad = _install_module("qor_test_runner_bad", 1)
    controls = (_ctl("hard", posture="ABORT", module=bad),)
    assert en.enforce("pre-commit", tmp_path, controls=controls).passed is False
    # A WARN control failing does not fail the verdict.
    controls_warn = (_ctl("soft", posture="WARN", module=bad),)
    assert en.enforce("pre-commit", tmp_path, controls=controls_warn).passed is True


def test_sdk_reexports_enforce():
    from qor import sdk
    assert sdk.enforce is en.enforce


def test_cli_enforce_runs_pre_commit():
    import argparse
    from qor.cli_handlers import compliance as ch
    ns = argparse.Namespace(
        compliance_command="enforce", engagement="pre-commit", repo_root=REPO
    )
    rc = ch.dispatch(ns)
    assert rc in (0, 1)  # real wired path returns an int exit code on the repo
