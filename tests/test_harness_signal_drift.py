"""Phase 131 (GH #165): confirm shadow_process.append_event does not consume the
QOR_SKILL_ACTIVE harness signal (moot), and the SG-HarnessSignalDrift-A doctrine
entry catalogues the pattern.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from qor.scripts import shadow_process


def _event(skill: str) -> dict:
    return {
        "ts": "2026-01-01T00:00:00Z",
        "skill": skill,
        "session_id": "sess-test",
        "event_type": "gate_override",
        "severity": 1,
        "details": {"gate": "test"},
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }


def test_append_event_ignores_qor_skill_active_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("QOR_SKILL_ACTIVE", "qor-implement")  # env sentinel
    log = tmp_path / "events.jsonl"
    shadow_process.append_event(_event("qor-plan"), log_path=log)  # different param skill
    line = log.read_text(encoding="utf-8").strip().splitlines()[-1]
    recorded = json.loads(line)
    assert recorded["skill"] == "qor-plan"  # caller-supplied field, not the env sentinel


def test_append_event_source_has_no_env_read() -> None:
    src = inspect.getsource(shadow_process.append_event)
    assert "os.environ" not in src
    assert "getenv" not in src
    assert "QOR_SKILL_ACTIVE" not in src


def test_doctrine_has_harness_signal_drift_entry() -> None:
    doc = Path("qor/references/doctrine-shadow-genome-countermeasures.md").read_text(
        encoding="utf-8"
    )
    assert "SG-HarnessSignalDrift-A" in doc
    assert "QOR_SKILL_ACTIVE" in doc
    assert "append_event" in doc
