"""Phase 163: release publish gated on CI success for the tagged SHA.

`release.yml` had build -> publish with no test gate; a publish was coupled to
tests only by operator discipline. `release_ci_gate.evaluate` is the pure,
fail-closed decision (ok iff a CI run for the exact SHA concluded `success`); the
authenticated `gh api` call stays in the workflow and pipes its JSON to `main`.

Behavioral: each test invokes the unit and asserts on its return/exit value.
The two structural tests assert release.yml wires the gate into both jobs.
"""
from __future__ import annotations

import io
import json
import pathlib

import yaml

from qor.scripts import release_ci_gate as rcg

_SHA = "a" * 40
_RELEASE = pathlib.Path(".github/workflows/release.yml")


def _runs(*entries) -> dict:
    return {"workflow_runs": list(entries)}


# -------------------------------------------------------------- evaluate()

def test_evaluate_ok_when_success_run_for_sha():
    runs = _runs({"head_sha": _SHA, "status": "completed", "conclusion": "success"})
    assert rcg.evaluate(runs, _SHA).ok is True


def test_evaluate_fails_when_only_failure_run():
    runs = _runs({"head_sha": _SHA, "status": "completed", "conclusion": "failure"})
    assert rcg.evaluate(runs, _SHA).ok is False


def test_evaluate_fails_when_run_in_progress():
    runs = _runs({"head_sha": _SHA, "status": "in_progress", "conclusion": None})
    assert rcg.evaluate(runs, _SHA).ok is False


def test_evaluate_fails_when_run_is_for_a_different_sha():
    runs = _runs({"head_sha": "b" * 40, "status": "completed", "conclusion": "success"})
    res = rcg.evaluate(runs, _SHA)
    assert res.ok is False
    assert "no CI run" in res.message


def test_evaluate_fails_on_no_runs():
    assert rcg.evaluate(_runs(), _SHA).ok is False


def test_evaluate_ok_with_mixed_runs_one_success():
    runs = _runs(
        {"head_sha": _SHA, "status": "completed", "conclusion": "failure"},
        {"head_sha": _SHA, "status": "completed", "conclusion": "success"},
    )
    assert rcg.evaluate(runs, _SHA).ok is True


# -------------------------------------------------------------- main() / stdin

def test_main_exits_zero_on_success_via_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        _runs({"head_sha": _SHA, "status": "completed", "conclusion": "success"}))))
    assert rcg.main(["--sha", _SHA]) == 0
    assert "OK" in capsys.readouterr().out


def test_main_exits_one_on_no_success_via_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        _runs({"head_sha": _SHA, "status": "in_progress", "conclusion": None}))))
    assert rcg.main(["--sha", _SHA]) == 1
    assert "REFUSE" in capsys.readouterr().out


# -------------------------------------------------------------- release.yml wiring

def _gate_step_indices(job: str) -> list[int]:
    wf = yaml.safe_load(_RELEASE.read_text(encoding="utf-8"))
    steps = wf["jobs"][job]["steps"]
    return [i for i, s in enumerate(steps) if "release_ci_gate" in (s.get("run") or "")]


def test_release_yml_wires_gate_into_both_jobs():
    assert _gate_step_indices("build"), "build job must run release_ci_gate (early gate)"
    assert _gate_step_indices("publish"), "publish job must run release_ci_gate (enforcement gate)"


def test_release_yml_gate_precedes_publish():
    wf = yaml.safe_load(_RELEASE.read_text(encoding="utf-8"))
    steps = wf["jobs"]["publish"]["steps"]
    gate = _gate_step_indices("publish")[0]
    pub = next(i for i, s in enumerate(steps)
               if s.get("uses", "").startswith("pypa/gh-action-pypi-publish"))
    assert gate < pub, "CI-success gate must precede the PyPI publish step"
