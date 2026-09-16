"""Phase 290: seal-tag push gate composes ancestor + tagged-SHA CI checks (GH #482).

A post-seal commit on the phase branch moves the pushed branch head past the
seal commit; the ancestor check alone (`git merge-base --is-ancestor`) still
passes once merged, but no CI run for the seal commit's own SHA exists.
`evaluate` closes that gap by requiring both.
"""
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from qor.scripts.tag_ci_gate import evaluate, main

SHA = "abc123def456"


def _runs(entries):
    return {"workflow_runs": entries}


def test_evaluate_holds_when_not_ancestor():
    res = evaluate(False, _runs([{"head_sha": SHA, "conclusion": "success"}]), SHA)
    assert res.ok is False
    assert "not yet on origin/main" in res.message


def test_evaluate_holds_when_ancestor_but_no_ci_run():
    res = evaluate(True, _runs([]), SHA)
    assert res.ok is False
    assert SHA[:8] in res.message
    assert "no green CI run" in res.message


def test_evaluate_holds_when_ancestor_but_ci_failed():
    res = evaluate(True, _runs([{"head_sha": SHA, "conclusion": "failure"}]), SHA)
    assert res.ok is False
    assert "no green CI run" in res.message


def test_evaluate_ready_when_ancestor_and_ci_success():
    res = evaluate(True, _runs([{"head_sha": SHA, "conclusion": "success"}]), SHA)
    assert res.ok is True


def test_evaluate_ignores_ci_run_for_different_sha():
    res = evaluate(True, _runs([{"head_sha": "other", "conclusion": "success"}]), SHA)
    assert res.ok is False


def test_main_skips_stdin_when_not_seal_commit_on_main(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(["--sha", SHA])
    assert code == 1
    assert "not yet on origin/main" in out.getvalue()


def test_main_exits_zero_on_success_via_stdin(monkeypatch):
    payload = json.dumps(_runs([{"head_sha": SHA, "conclusion": "success"}]))
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    code = main(["--sha", SHA, "--on-main"])
    assert code == 0


def test_main_exits_one_on_no_success_via_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_runs([]))))
    code = main(["--sha", SHA, "--on-main"])
    assert code == 1
