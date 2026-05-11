"""Phase 47 host_capability helper behavior tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts.host_capability import (
    CheckResult,
    PrereqSummary,
    FreshnessResult,
    check_module,
    check_file,
    check_step_prerequisites,
    check_qor_logic_freshness,
    emit_prerequisite_absent_event,
    emit_freshness_event,
)


def test_check_module_present_for_known_stdlib():
    r = check_module("json")
    assert r.present is True


def test_check_module_absent_for_nonexistent():
    r = check_module("qor.scripts.definitely_nonexistent_module_xyz")
    assert r.present is False
    assert r.detail


def test_check_file_present_returns_true_for_pyproject(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_text('version = "0.1.0"\n')
    r = check_file(p)
    assert r.present is True


def test_check_file_absent_returns_false(tmp_path):
    r = check_file(tmp_path / "no.toml")
    assert r.present is False


def test_check_step_prerequisites_aggregates_results():
    summary = check_step_prerequisites("4.6", [
        {"kind": "module", "target": "json"},
        {"kind": "module", "target": "qor.scripts.definitely_missing_xyz"},
    ])
    assert summary.step_name == "4.6"
    assert len(summary.checks) == 2


def test_check_step_prerequisites_can_proceed_true_when_all_present():
    summary = check_step_prerequisites("X", [
        {"kind": "module", "target": "json"},
        {"kind": "module", "target": "pathlib"},
    ])
    assert summary.can_proceed is True


def test_check_step_prerequisites_can_proceed_false_when_any_missing():
    summary = check_step_prerequisites("X", [
        {"kind": "module", "target": "json"},
        {"kind": "module", "target": "qor.scripts.definitely_missing_xyz"},
    ])
    assert summary.can_proceed is False


def test_check_qor_logic_freshness_drift_false_when_versions_match(tmp_path):
    (tmp_path / "pyproject.toml").write_text('version = "0.46.0"\n')
    r = check_qor_logic_freshness(repo_root=tmp_path, latest_known="0.46.0")
    assert r.drift is False
    assert r.installed_version == "0.46.0"


def test_check_qor_logic_freshness_drift_true_when_versions_differ(tmp_path):
    (tmp_path / "pyproject.toml").write_text('version = "0.31.1"\n')
    r = check_qor_logic_freshness(repo_root=tmp_path, latest_known="0.46.0")
    assert r.drift is True
    assert r.installed_version == "0.31.1"
    assert r.latest_known == "0.46.0"


def test_check_qor_logic_freshness_handles_missing_pyproject(tmp_path):
    r = check_qor_logic_freshness(repo_root=tmp_path, latest_known="0.46.0")
    assert r.installed_version is None
    assert r.drift is False


def test_check_qor_logic_freshness_reads_latest_known_from_marker(tmp_path):
    (tmp_path / "pyproject.toml").write_text('version = "0.46.0"\n')
    marker_dir = tmp_path / ".qor" / "freshness"
    marker_dir.mkdir(parents=True)
    (marker_dir / "latest_known").write_text("0.47.0\n")
    r = check_qor_logic_freshness(repo_root=tmp_path)
    assert r.latest_known == "0.47.0"
    assert r.drift is True


def test_emit_prerequisite_absent_event_writes_jsonl(tmp_path):
    log = tmp_path / "shadow.jsonl"
    emit_prerequisite_absent_event(
        step_name="4.6.5",
        missing=[CheckResult(name="qor.scripts.secret_scanner", present=False, detail="missing")],
        session_id="sess-test",
        log_path=log,
        ts="2026-05-09T05:00:00Z",
    )
    line = log.read_text(encoding="utf-8").strip()
    payload = json.loads(line)
    assert payload["event_type"] == "prerequisite_absent"
    assert payload["severity"] == 2
    assert payload["skill"] == "qor-substantiate"
    assert payload["details"]["step"] == "4.6.5"
    assert payload["details"]["missing"][0]["name"] == "qor.scripts.secret_scanner"


def test_emit_freshness_event_writes_jsonl(tmp_path):
    log = tmp_path / "shadow.jsonl"
    result = FreshnessResult(
        installed_version="0.31.1", latest_known="0.46.0", drift=True, detail="x",
    )
    emit_freshness_event(result, "sess-test", log, ts="2026-05-09T05:00:00Z")
    payload = json.loads(log.read_text(encoding="utf-8").strip())
    assert payload["event_type"] == "qor_logic_stale_install"
    assert payload["severity"] == 1
    assert payload["details"]["drift"] is True
    assert payload["details"]["installed_version"] == "0.31.1"
