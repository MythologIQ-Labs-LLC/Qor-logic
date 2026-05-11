"""Phase 47 integration scenarios for host_capability."""
from __future__ import annotations

import json

import pytest

from qor.scripts.host_capability import (
    CheckResult,
    check_step_prerequisites,
    check_qor_logic_freshness,
    emit_prerequisite_absent_event,
    emit_freshness_event,
)


def test_scenario_1_all_prereqs_present():
    summary = check_step_prerequisites("X", [
        {"kind": "module", "target": "json"},
        {"kind": "module", "target": "pathlib"},
    ])
    assert summary.can_proceed is True
    assert all(c.present for c in summary.checks)


def test_scenario_2_missing_module_emits_event(tmp_path):
    log = tmp_path / "shadow.jsonl"
    summary = check_step_prerequisites("4.6.5", [
        {"kind": "module", "target": "qor.scripts.nonexistent_xyz"},
    ])
    assert summary.can_proceed is False
    emit_prerequisite_absent_event(
        "4.6.5",
        [c for c in summary.checks if not c.present],
        "sess",
        log,
        ts="2026-05-09T05:00:00Z",
    )
    event = json.loads(log.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "prerequisite_absent"
    assert event["details"]["step"] == "4.6.5"


def test_scenario_3_missing_file_returns_absent(tmp_path):
    summary = check_step_prerequisites("7.5", [
        {"kind": "file", "target": str(tmp_path / "no_pyproject.toml")},
    ])
    assert summary.can_proceed is False


def test_scenario_4_freshness_match_no_event(tmp_path):
    (tmp_path / "pyproject.toml").write_text('version = "0.46.0"\n')
    r = check_qor_logic_freshness(repo_root=tmp_path, latest_known="0.46.0")
    assert r.drift is False


def test_scenario_5_freshness_mismatch_emits_event(tmp_path):
    (tmp_path / "pyproject.toml").write_text('version = "0.31.1"\n')
    log = tmp_path / "shadow.jsonl"
    r = check_qor_logic_freshness(repo_root=tmp_path, latest_known="0.46.0")
    emit_freshness_event(r, "sess", log, ts="2026-05-09T05:00:00Z")
    event = json.loads(log.read_text(encoding="utf-8").strip())
    assert event["event_type"] == "qor_logic_stale_install"
    assert event["details"]["drift"] is True


def test_scenario_6_missing_pyproject_drift_false(tmp_path):
    r = check_qor_logic_freshness(repo_root=tmp_path, latest_known="0.46.0")
    assert r.installed_version is None
    assert r.drift is False
