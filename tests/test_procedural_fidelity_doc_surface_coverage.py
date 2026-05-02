"""Phase 58: doc-surface coverage detector behavioral tests."""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import procedural_fidelity as pf


def _write_implement_gate(repo: Path, sid: str, files_touched: list[str]) -> None:
    gates = repo / ".qor" / "gates" / sid
    gates.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": "implement", "session_id": sid, "ts": "2026-05-01T20:00:00Z",
        "files_touched": files_touched,
    }
    (gates / "implement.json").write_text(json.dumps(payload), encoding="utf-8")


def test_detects_uncovered_when_skill_changed_without_system_state(tmp_path: Path):
    sid = "t1"
    _write_implement_gate(tmp_path, sid, ["qor/skills/sdlc/qor-foo/SKILL.md"])
    findings = pf.check_seal_commit(tmp_path, sid)
    assert len(findings) == 1
    assert findings[0].deviation_class == "doc-surface-uncovered"
    assert findings[0].severity == 2


def test_detects_uncovered_when_doctrine_changed_without_operations(tmp_path: Path):
    sid = "t2"
    _write_implement_gate(tmp_path, sid, ["qor/references/doctrine-bar.md"])
    findings = pf.check_seal_commit(tmp_path, sid)
    assert len(findings) == 1
    assert findings[0].deviation_class == "doc-surface-uncovered"


def test_passes_when_at_least_one_system_doc_updated(tmp_path: Path):
    sid = "t3"
    _write_implement_gate(tmp_path, sid, [
        "qor/skills/sdlc/qor-foo/SKILL.md",
        "docs/SYSTEM_STATE.md",
    ])
    findings = pf.check_seal_commit(tmp_path, sid)
    assert findings == []


def test_passes_when_only_test_files_touched(tmp_path: Path):
    sid = "t4"
    _write_implement_gate(tmp_path, sid, ["tests/test_x.py"])
    findings = pf.check_seal_commit(tmp_path, sid)
    assert findings == []


def test_respects_threshold_at_least_one(tmp_path: Path):
    sid = "t5"
    _write_implement_gate(tmp_path, sid, [
        "qor/skills/sdlc/qor-foo/SKILL.md",
        "docs/operations.md",  # one of the four; sufficient
    ])
    findings = pf.check_seal_commit(tmp_path, sid)
    assert findings == []
