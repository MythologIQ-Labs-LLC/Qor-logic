"""Phase 165: behavioral tests for the aggregate status runner (GH #240/#250).

The aggregator is tested against synthetic check registries; no test here
executes the real health checks against live repo state (that is the nightly
workflow's job, where repo state is sealed).
"""
from __future__ import annotations

import importlib.util
import json

from qor.scripts.status_json import (
    Check,
    default_registry,
    main,
    run_all,
    run_check,
)


def _passing_check() -> tuple[int, str]:
    return 0, "OK: everything fine\nsecond line"


def _failing_check() -> tuple[int, str]:
    return 1, "FAIL: something drifted"


def _raising_check() -> tuple[int, str]:
    raise RuntimeError("boom during check")


def test_run_check_captures_exit_and_summary():
    result = run_check(Check(id="demo", fn=_passing_check))
    assert result["id"] == "demo"
    assert result["ok"] is True
    assert result["exit"] == 0
    assert result["summary"] == "OK: everything fine"


def test_run_check_failure_and_exception_paths():
    failed = run_check(Check(id="drift", fn=_failing_check))
    assert failed["ok"] is False
    assert failed["exit"] == 1
    assert "drifted" in failed["summary"]
    raised = run_check(Check(id="crash", fn=_raising_check))
    assert raised["ok"] is False
    assert raised["exit"] == 3
    assert "boom" in raised["summary"]


def test_run_all_shape_and_overall():
    mixed = run_all([Check(id="a", fn=_passing_check), Check(id="b", fn=_failing_check)])
    assert mixed["schema_version"] == "1"
    assert "ts" in mixed
    assert [c["id"] for c in mixed["checks"]] == ["a", "b"]
    assert mixed["overall_ok"] is False
    clean = run_all([Check(id="a", fn=_passing_check)])
    assert clean["overall_ok"] is True


def test_main_emits_json_as_final_line_and_exit_codes(capsys):
    rc = main(["--repo-root", "."], registry=[Check(id="a", fn=_passing_check),
                                              Check(id="b", fn=_failing_check)])
    assert rc == 1
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    payload = json.loads(lines[-1])
    assert payload["overall_ok"] is False
    assert {c["id"] for c in payload["checks"]} == {"a", "b"}
    rc = main(["--repo-root", "."], registry=[Check(id="a", fn=_passing_check)])
    assert rc == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert json.loads(lines[-1])["overall_ok"] is True


def test_default_registry_ids_unique_and_argv_wellformed(tmp_path):
    registry = default_registry(tmp_path)
    ids = [c.id for c in registry]
    assert len(ids) == len(set(ids)), f"duplicate check ids: {ids}"
    assert len(ids) >= 6
    for check in registry:
        assert check.fn is not None, f"{check.id} must normalize to a callable"
        assert check.module, f"{check.id} must name its module"
        assert importlib.util.find_spec(check.module) is not None, (
            f"{check.id}: module {check.module} is not importable"
        )


def test_self_test_mode_passes(capsys):
    rc = main(["--self-test"])
    assert rc == 0
    assert "self-test PASSED" in capsys.readouterr().out
