"""Tests for Phase 14 shadow attribution (dual Process Shadow Genome)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import shadow_process

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_doctrine_shadow_attribution_exists():
    path = REPO_ROOT / "qor" / "references" / "doctrine-shadow-attribution.md"
    assert path.exists(), f"Missing: {path}"


def test_doctrine_shadow_attribution_defines_both_classes():
    body = (REPO_ROOT / "qor" / "references" / "doctrine-shadow-attribution.md").read_text(encoding="utf-8")
    assert "UPSTREAM" in body
    assert "LOCAL" in body


def test_doctrine_shadow_attribution_has_worked_examples():
    body = (REPO_ROOT / "qor" / "references" / "doctrine-shadow-attribution.md").read_text(encoding="utf-8")
    assert body.count("Worked example") >= 2


def test_doctrine_declares_narrative_log_out_of_scope():
    body = (REPO_ROOT / "qor" / "references" / "doctrine-shadow-attribution.md").read_text(encoding="utf-8")
    lower = body.lower()
    assert "out of scope" in lower
    assert "SHADOW_GENOME.md" in body


def test_upstream_file_exists():
    path = REPO_ROOT / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
    assert path.exists(), f"Missing: {path}"


def test_log_path_for_upstream():
    assert shadow_process.log_path_for("UPSTREAM") == shadow_process.UPSTREAM_LOG_PATH


def test_log_path_for_local():
    assert shadow_process.log_path_for("LOCAL") == shadow_process.LOCAL_LOG_PATH


def test_append_event_requires_attribution_or_log_path():
    event = {
        "ts": "2026-04-15T12:00:00Z",
        "skill": "qor-audit",
        "session_id": "test-session",
        "event_type": "gate_override",
        "severity": 1,
        "details": {},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    with pytest.raises(ValueError, match="attribution"):
        shadow_process.append_event(event)


def test_collector_warns_on_legacy_only(tmp_path, capsys):
    import sys
    from qor.scripts import collect_shadow_genomes as collect

    repo = tmp_path / "repo1"
    (repo / "docs").mkdir(parents=True)
    legacy = repo / "docs" / "PROCESS_SHADOW_GENOME.md"
    event = {
        "ts": "2026-04-15T12:00:00Z",
        "skill": "qor-audit",
        "session_id": "s-1",
        "event_type": "gate_override",
        "severity": 1,
        "details": {},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    event["id"] = shadow_process.compute_id(event)
    legacy.write_text(json.dumps(event) + "\n", encoding="utf-8")

    events = collect.read_repo_shadow(repo)
    captured = capsys.readouterr()
    assert "legacy log present" in captured.err


def test_write_events_per_source_splits_correctly(tmp_path):
    local_log = tmp_path / "local.md"
    upstream_log = tmp_path / "upstream.md"

    e1 = {"id": "aaa", "ts": "2026-04-15T12:00:00Z", "severity": 1}
    e2 = {"id": "bbb", "ts": "2026-04-15T13:00:00Z", "severity": 2}
    e3 = {"id": "ccc", "ts": "2026-04-15T14:00:00Z", "severity": 3}

    local_log.write_text(
        json.dumps(e1) + "\n" + json.dumps(e2) + "\n", encoding="utf-8"
    )
    upstream_log.write_text(json.dumps(e3) + "\n", encoding="utf-8")

    src_map = {
        "aaa": local_log,
        "bbb": local_log,
        "ccc": upstream_log,
    }

    e1["severity"] = 10
    e2["severity"] = 20
    e3["severity"] = 30

    shadow_process.write_events_per_source([e1, e2, e3], src_map)

    local_events = shadow_process.read_events(local_log)
    upstream_events = shadow_process.read_events(upstream_log)

    assert len(local_events) == 2
    assert local_events[0]["severity"] == 10
    assert local_events[1]["severity"] == 20
    assert len(upstream_events) == 1
    assert upstream_events[0]["severity"] == 30
